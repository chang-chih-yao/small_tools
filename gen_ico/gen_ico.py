from PIL import Image

class IcoGenerator:
    # 最大的 size 必須放在最後面
    DEFAULT_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

    def __init__(self, src: str, dst: str = "app.ico", sizes: list = None):
        self.src = src
        self.dst = dst
        self.sizes = sizes or self.DEFAULT_SIZES

    @staticmethod
    def make_square_transparent(img: Image.Image) -> Image.Image:
        img = img.convert("RGBA")
        w, h = img.size
        size = max(w, h)

        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        x = (size - w) // 2
        y = (size - h) // 2
        canvas.paste(img, (x, y), img)
        return canvas

    def generate(self):
        img = Image.open(self.src)
        w, h = img.size

        if w != h:
            answer = input(f"圖片非正方形 ({w}x{h})，是否自動補透明像素變成正方形？[y/N] ").strip().lower()
            if answer == "y":
                base = self.make_square_transparent(img)
            else:
                print("已取消，請提供正方形圖片後再執行。")
                return
        else:
            base = img.convert("RGBA")

        icons = [base.resize(size, Image.Resampling.LANCZOS) for size in self.sizes]
        icons[-1].save(
            self.dst,
            format="ICO",
            append_images=icons[:-1],
        )
        print(f"已儲存：{self.dst}")


if __name__ == "__main__":
    import glob
    import os

    patterns = ["*.png", "*.PNG", "*.jpg", "*.JPG", "*.jpeg", "*.JPEG"]
    found = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))
    found = sorted(set(found))

    if not found:
        print("警告：目前資料夾內沒有任何 .png / .jpg / .jpeg 影像檔。")
    else:
        for i, f in enumerate(found, 1):
            print(f"  {i}. {f}")
        choice = input("請選擇要使用的圖片編號：").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(found):
            src = found[int(choice) - 1]
            dst = os.path.splitext(src)[0] + ".ico"
            IcoGenerator(src=src, dst=dst).generate()
        else:
            print("無效的選擇，程式結束。")
