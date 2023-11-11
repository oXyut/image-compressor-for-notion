import io
import os
import subprocess
import platform

from glob import glob
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import Label, Frame, Event, Button
from PIL import Image, ImageTk

# GUIアプリケーションクラスの定義
class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Compressor")

        if not os.path.exists("./compressed/"):
            os.mkdir("./compressed/")
            print("Created ./compressed/ directory.")

        # ドラッグアンドドロップエリアの作成
        self.drop_area = Label(root, text="ここに画像をドラッグ＆ドロップ", width=40, height=10, bg="gray")
        self.drop_area.pack(pady=20)

        # ドラッグアンドドロップイベントのバインド
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)

        # サムネイル表示用のフレーム
        self.thumbnail_frame = Frame(root)
        self.thumbnail_frame.pack(pady=10)


        # サムネイルの更新
        self.update_thumbnail()

        # OSに応じたFinder/Explorerで開くボタン
        os_name = platform.system()
        if os_name == "Darwin":  # macOS
            btn_text = "Finderで開く"
            self.open_command = ["open", "./compressed/"]
        elif os_name == "Windows":
            btn_text = "Explorerで開く"
            self.open_command = ["explorer", "./compressed/"]
        else:
            btn_text = "ディレクトリを開く"
            self.open_command = None
        
        self.open_directory_button = Button(root, text=btn_text, command=self.open_directory)
        self.open_directory_button.pack(pady=10)

    def open_directory(self):
        if self.open_command:
            subprocess.run(self.open_command)
        else:
            print("このOSではサポートされていません。")


    def update_thumbnail(self):
        # サムネイルフレーム内の既存のウィジェットを削除
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()

        # 最新の5枚の画像を取得
        compressed_images = glob('./compressed/*.jpg') + glob('./compressed/*.JPG')
        compressed_images.sort(key=os.path.getmtime, reverse=True)
        for img_path in compressed_images[:5]:
            img = Image.open(img_path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            label = Label(self.thumbnail_frame, image=photo)
            label.image = photo  # 参照を保持
            label.pack(side="left")

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
        if ext.lower() not in [".jpg", ".jpeg"]:
            print(f"{file_path} is not a JPEG file.")
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
