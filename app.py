from typing import Literal
import io
import os
import subprocess
import platform

from glob import glob
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import Label, Frame, Event, Button, Canvas, Scrollbar
from PIL import Image, ImageTk

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".JPG", ".JPEG"]

# GUIアプリケーションクラスの定義
class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.setup_app()
        self.setup_drop_area()
        self.setup_thumbnail_area()
        self.setup_open_directory_button()
        self.thumbnail_frame.bind('<Configure>', self.on_frame_configure)


    def setup_app(self):
        self.root.title("Image Compressor")
        if not os.path.exists("./compressed/"):
            os.mkdir("./compressed/")
            print("Created ./compressed/ directory.")

    def setup_drop_area(self):
        self.drop_area = Label(self.root, text="ここに画像をドラッグ＆ドロップ", width=40, height=10, bg="gray")
        self.drop_area.pack(pady=20)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)

    def setup_thumbnail_area(self):
        self.thumbnail_frame = Frame(self.root)
        self.thumbnail_frame.pack(pady=10)
        self.thumbnail_frame = Canvas(self.root, borderwidth=0)
        self.thumbnail_frame.pack(side="bottom", fill="x", expand=True)
        scrollbar = Scrollbar(self.root, orient="horizontal", command=self.thumbnail_frame.xview)
        scrollbar.pack(side="bottom", fill="x")
        self.thumbnail_frame.configure(xscrollcommand=scrollbar.set)
        self.thumbnail_frame.bind('<Configure>', self.on_frame_configure)
        self.thumbnail_container = Frame(self.thumbnail_frame)
        self.thumbnail_frame.create_window((0,0), window=self.thumbnail_container, anchor="nw")
        self.update_thumbnail()

    def setup_open_directory_button(self):
        os_name = self.get_os_name()
        if os_name == "Darwin":  # macOS
            btn_text = "Finderで開く"
            self.open_command = ["open", "./compressed/"]
        elif os_name == "Windows":
            btn_text = "Explorerで開く"
            self.open_command = ["explorer", "./compressed/"]
        else:
            btn_text = None
            self.open_command = None
        self.open_directory_button = Button(self.root, text=btn_text, command=self.open_directory)
        self.open_directory_button.pack(pady=10)

    def handle_drop(self, event: Event):
        file_paths = event.data.strip().split(" ")
        for file_path in file_paths:
            self.process_file(file_path)

    def process_file(self, file_path:str):
        if self.check_file_path(file_path):
            self.compress_and_update_image(file_path)

    def compress_and_update_image(self, file_path:str):
        compressed_path, size = self.compress_image(file_path)
        size_mb = size / 1024 / 1024
        print(f"{os.path.basename(file_path)} has been compressed to {size_mb:.2f} MB.")
        self.update_thumbnail()

        # サムネイルの更新
        self.update_thumbnail()

        # OSに応じたFinder/Explorerで開くボタン
        os_name = self.get_os_name()
        if os_name == "Darwin":  # macOS
            btn_text = "Finderで開く"
            self.open_command = ["open", "./compressed/"]
        elif os_name == "Windows":
            btn_text = "Explorerで開く"
            self.open_command = ["explorer", "./compressed/"]
        else:
            btn_text = None
            self.open_command = None
        
        self.open_directory_button = Button(root, text=btn_text, command=self.open_directory)
        self.open_directory_button.pack(pady=10)

    def get_os_name(self) -> Literal["Darwin", "Windows", "Linux"]:
        return platform.system()

    def open_directory(self):
        if self.open_command:
            subprocess.run(self.open_command)
        else:
            print("このOSではサポートされていません。")


    def on_frame_configure(self, event=None):
        self.thumbnail_frame.configure(scrollregion=self.thumbnail_frame.bbox("all"))

    def update_thumbnail(self):
        # サムネイルコンテナ内の既存のウィジェットを削除
        for widget in self.thumbnail_container.winfo_children():
            widget.destroy()

        # 圧縮された画像のサムネイルを表示
        compressed_images = []
        for ext in SUPPORTED_EXTENSIONS:
            compressed_images.extend(glob(f"./compressed/*{ext}"))
        
        for img_path in compressed_images:
            thumbnail = Image.open(img_path)
            thumbnail.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(thumbnail)

            thumb_frame = Frame(self.thumbnail_container)
            label = Label(thumb_frame, image=photo)
            label.image = photo  # 参照を保持
            label.pack()

            # 画像名のラベル
            name_label = Label(thumb_frame, text=os.path.basename(img_path))
            name_label.pack()

            thumb_frame.pack(side="left", padx=10)
        # Canvasのスクロール領域を更新
        self.on_frame_configure()

    def handle_drop(self, event: Event):
        # ドロップされたファイルのパスを取得
        # event.dataはファイルのパスがスペース区切りで格納されている
        file_paths = event.data.strip().split(" ")

        for file_path in file_paths:
            self.check_file_path(file_path) # ファイルのパスを確認
            self.compress_image(file_path) # 画像を圧縮
    
    def check_file_path(self, file_path:str):
        # ファイルのパスを確認
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist.")
            return
        
        # ファイルの拡張子を確認
        _, ext = os.path.splitext(file_path)
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"{file_path} is not supported file type.")
            return

    def compress_image(self, file_path:str):
        # 画像を開く
        with Image.open(file_path) as img:
            # 画像の圧縮と保存
            target_size = 5 * 1024 * 1024 # 5MB
            quality = 95

            while True:
                # メモリ上で圧縮された画像を保存
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=quality)
                size = img_bytes.tell()

                if size <= target_size or quality <= 10:
                    break

                # 品質を下げて再試行
                quality -= 5

            # 圧縮された画像を./compressed/に保存
            compressed_path = os.path.join("./compressed/", os.path.basename(file_path))
            with open(compressed_path, "wb") as f:
                f.write(img_bytes.getvalue())
            
            # MB単位に変換
            size_mb = size / 1024 / 1024

            print(f"{os.path.basename(file_path)} has been compressed to {size_mb:.2f} MB.")

            # サムネイルの更新
            self.update_thumbnail()

if __name__ == "__main__":
    # アプリケーションの起動
    root = TkinterDnD.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()
