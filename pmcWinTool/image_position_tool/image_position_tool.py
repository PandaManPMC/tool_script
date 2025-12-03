import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageClickApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PMC 图片查看器（增强版）")
        self.root.geometry("900x600")

        # 菜单
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="打开图片...", command=self.open_image)
        filemenu.add_separator()
        filemenu.add_command(label="退出", command=root.quit)
        menubar.add_cascade(label="文件", menu=filemenu)
        root.config(menu=menubar)

        # 主画布
        self.canvas = tk.Canvas(root, bg="#333333")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status = tk.Label(root, text="打开一张图片开始...", anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        # 事件绑定
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Configure>", self.on_resize)

        # 图片状态
        self.image_path = None
        self.orig_image = None
        self.tk_image = None
        self.display_size = (0, 0)
        self.display_offset = (0, 0)

        # 十字线
        self.cross_lines = []

        # 点击后的像素值，用于放大镜显示十字线
        self.click_px = None
        self.click_py = None

        # 放大镜
        self.zoom_size = 140
        self.zoom_scale = 6
        self.zoom_canvas = tk.Canvas(self.canvas, width=self.zoom_size, height=self.zoom_size,
                                     highlightthickness=1, highlightbackground="white")
        self.zoom_img = None

    def open_image(self):
        path = filedialog.askopenfilename(title="选择图片", filetypes=[
            ("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),
            ("所有文件", "*")
        ])
        if not path:
            return

        try:
            img = Image.open(path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")
            return

        self.image_path = path
        self.orig_image = img.convert("RGBA")
        self.redraw_image()
        self.status.config(text=f"已打开: {os.path.basename(path)}  ({self.orig_image.width}×{self.orig_image.height})")

    def redraw_image(self, event=None):
        if self.orig_image is None:
            return

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        img_w, img_h = self.orig_image.size

        ratio = min(canvas_w / img_w, canvas_h / img_h, 1.0)
        disp_w = int(img_w * ratio)
        disp_h = int(img_h * ratio)

        offset_x = (canvas_w - disp_w) // 2
        offset_y = (canvas_h - disp_h) // 2

        resized = self.orig_image.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)

        # 不要删除十字线
        current_lines = self.cross_lines.copy()

        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=self.tk_image)

        self.display_size = (disp_w, disp_h)
        self.display_offset = (offset_x, offset_y)

        # 恢复十字线
        for line in current_lines:
            self.canvas.itemconfig(line, state="normal")

        self.cross_lines = current_lines

    def on_resize(self, event):
        self.redraw_image()

    def draw_cross(self, x, y):
        # 删除旧十字线
        for l in self.cross_lines:
            self.canvas.delete(l)
        self.cross_lines.clear()

        off_x, off_y = self.display_offset
        disp_w, disp_h = self.display_size

        # 横线
        h_line = self.canvas.create_line(off_x, y, off_x + disp_w, y, fill="yellow", width=1)
        # 竖线
        v_line = self.canvas.create_line(x, off_y, x, off_y + disp_h, fill="yellow", width=1)

        self.cross_lines = [h_line, v_line]

    def on_click(self, event):
        if self.orig_image is None:
            return

        x_canvas = event.x
        y_canvas = event.y
        off_x, off_y = self.display_offset
        disp_w, disp_h = self.display_size
        img_w, img_h = self.orig_image.size

        if not (off_x <= x_canvas < off_x + disp_w and off_y <= y_canvas < off_y + disp_h):
            return

        rel_x = x_canvas - off_x
        rel_y = y_canvas - off_y

        px = int(rel_x * img_w / disp_w)
        py = int(rel_y * img_h / disp_h)

        px = max(0, min(img_w - 1, px))
        py = max(0, min(img_h - 1, py))

        self.click_px = px
        self.click_py = py

        pct_x = rel_x / disp_w * 100
        pct_y = rel_y / disp_h * 100

        txt = f"像素: ({px}, {py})  百分比: ({pct_x:.2f}%, {pct_y:.2f}%)"
        self.status.config(text=txt)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(f"{px},{py} ({pct_x:.2f}%,{pct_y:.2f}%)")
        except:
            pass

        disp_x = off_x + (px + 0.5) * disp_w / img_w
        disp_y = off_y + (py + 0.5) * disp_h / img_h

        self.draw_cross(disp_x, disp_y)

    # ================= 放大镜 ===================
    def on_mouse_move(self, event):
        if self.orig_image is None or self.click_px is None:
            self.zoom_canvas.place_forget()
            return

        x_canvas, y_canvas = event.x, event.y

        # 把点击的 px, py 映射到原图
        px = self.click_px
        py = self.click_py
        img_w, img_h = self.orig_image.size

        r = 10
        left = max(0, px - r)
        top = max(0, py - r)
        right = min(img_w, px + r)
        bottom = min(img_h, py + r)

        crop = self.orig_image.crop((left, top, right, bottom))
        crop = crop.resize((self.zoom_size, self.zoom_size), Image.NEAREST)

        # 在放大镜里画十字线
        draw_center = self.zoom_size // 2
        for i in range(self.zoom_size):
            crop.putpixel((draw_center, i), (255, 255, 0, 255))
            crop.putpixel((i, draw_center), (255, 255, 0, 255))

        self.zoom_img = ImageTk.PhotoImage(crop)
        self.zoom_canvas.delete("all")
        self.zoom_canvas.create_image(0, 0, anchor=tk.NW, image=self.zoom_img)

        # 显示在鼠标右下角
        self.zoom_canvas.place(x=x_canvas + 20, y=y_canvas + 20)


if __name__ == '__main__':
    root = tk.Tk()
    app = ImageClickApp(root)
    root.mainloop()
