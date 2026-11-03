
import tkinter as tk
from tkinter import font
import os


class WritingTool:

    def __init__(self, root):
        self.root = root
        self.root.title("文本写作工具")
        self.root.geometry("720x960+200+20")
        self.root.minsize(400, 500)
        self.root.configure(bg="#f5f5f5")

        # 固定保存文件
        self.save_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "writing.txt"
        )

        self.save_timer = None
        self.refresh_timer = None

        # 编辑器字体
        self.editor_font = font.Font(
            family="Microsoft YaHei",
            size=14
        )

        self.build_ui()
        self.load_content()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # ==============================
    # UI
    # ==============================

    def build_ui(self):

        # 顶部工具栏
        toolbar = tk.Frame(
            self.root,
            bg="#ffffff",
            height=55
        )
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text="文本写作工具",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ffffff",
            fg="#333333"
        ).pack(side=tk.LEFT, padx=20)

        # 顶部字数统计
        self.word_label = tk.Label(
            toolbar,
            text="当前字数：0",
            font=("Microsoft YaHei", 11),
            bg="#ffffff",
            fg="#666666"
        )
        self.word_label.pack(side=tk.RIGHT, padx=20)

        # 编辑器容器
        container = tk.Frame(
            self.root,
            bg="#ffffff"
        )
        container.pack(
            fill=tk.BOTH,
            expand=True,
            padx=15,
            pady=15
        )

        # 左侧行号区域
        self.gutter = tk.Canvas(
            container,
            width=48,
            bg="#f7f7f7",
            highlightthickness=0
        )
        self.gutter.pack(
            side=tk.LEFT,
            fill=tk.Y
        )

        # 文本编辑器
        self.editor = tk.Text(
            container,
            font=self.editor_font,
            bg="#ffffff",
            fg="#333333",
            insertbackground="#333333",
            selectbackground="#cce5ff",
            selectforeground="#222222",
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=12,
            wrap=tk.WORD,
            undo=True,
            maxundo=-1,
            spacing1=3,
            spacing3=3
        )
        self.editor.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        # 滚动条
        scrollbar = tk.Scrollbar(
            container,
            command=self.on_scroll
        )
        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.editor.configure(
            yscrollcommand=self.on_editor_scroll
        )

        # 文本变化事件
        self.editor.bind(
            "<<Modified>>",
            self.on_text_changed
        )

        # 光标、输入、鼠标操作
        self.editor.bind(
            "<KeyRelease>",
            self.on_editor_action
        )

        self.editor.bind(
            "<ButtonRelease-1>",
            self.on_editor_action
        )

        self.editor.bind(
            "<Configure>",
            self.schedule_refresh
        )

        self.editor.bind(
            "<MouseWheel>",
            self.schedule_refresh
        )

        self.editor.bind(
            "<Button-4>",
            self.schedule_refresh
        )

        self.editor.bind(
            "<Button-5>",
            self.schedule_refresh
        )

        # 底部状态栏
        statusbar = tk.Frame(
            self.root,
            bg="#ffffff",
            height=38
        )
        statusbar.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )
        statusbar.pack_propagate(False)

        self.save_status = tk.Label(
            statusbar,
            text="已加载",
            font=("Microsoft YaHei", 9),
            bg="#ffffff",
            fg="#888888"
        )
        self.save_status.pack(
            side=tk.LEFT,
            padx=15
        )

    # ==============================
    # 加载文本
    # ==============================

    def load_content(self):

        if os.path.exists(self.save_path):
            try:
                with open(
                    self.save_path,
                    "r",
                    encoding="utf-8"
                ) as f:
                    content = f.read()

                self.editor.insert("1.0", content)

            except Exception as e:
                self.save_status.config(
                    text=f"读取失败：{e}",
                    fg="#e74c3c"
                )

        self.editor.edit_modified(False)

        self.update_word_count()
        self.update_line_numbers()

    # ==============================
    # 字数统计
    # ==============================

    def update_word_count(self):

        content = self.editor.get(
            "1.0",
            "end-1c"
        )

        # 不计算空格、换行、制表符
        count = sum(
            1 for char in content
            if not char.isspace()
        )

        self.word_label.config(
            text=f"当前字数：{count}"
        )

    # ==============================
    # 文本变化
    # ==============================

    def on_text_changed(self, event=None):

        if self.editor.edit_modified():

            self.editor.edit_modified(False)

            self.update_word_count()
            self.schedule_refresh()

            self.save_status.config(
                text="正在编辑...",
                fg="#e67e22"
            )

            # 延迟保存，避免频繁写入
            if self.save_timer:
                self.root.after_cancel(
                    self.save_timer
                )

            self.save_timer = self.root.after(
                2000,
                self.auto_save
            )

    def on_editor_action(self, event=None):

        self.schedule_refresh()
        self.update_word_count()

    # ==============================
    # 自动保存
    # ==============================

    def auto_save(self):

        self.save_timer = None

        content = self.editor.get(
            "1.0",
            "end-1c"
        )

        temp_path = self.save_path + ".tmp"

        try:
            # 先写入临时文件，再替换正式文件
            with open(
                temp_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            os.replace(
                temp_path,
                self.save_path
            )

            self.save_status.config(
                text="已自动保存",
                fg="#27ae60"
            )

        except Exception as e:

            self.save_status.config(
                text=f"保存失败：{e}",
                fg="#e74c3c"
            )

            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

    # ==============================
    # 滚动同步
    # ==============================

    def on_scroll(self, *args):

        self.editor.yview(*args)
        self.schedule_refresh()

    def on_editor_scroll(self, first, last):

        self.scrollbar_update(first, last)
        self.schedule_refresh()

    def scrollbar_update(self, first, last):

        # 获取滚动条
        scrollbar = self.editor.master.winfo_children()

        for widget in scrollbar:
            if isinstance(widget, tk.Scrollbar):
                widget.set(first, last)
                break

    # ==============================
    # 行号刷新
    # ==============================

    def schedule_refresh(self, event=None):

        if self.refresh_timer is None:
            self.refresh_timer = self.root.after_idle(
                self.update_line_numbers
            )

    def update_line_numbers(self):

        self.refresh_timer = None

        if not self.editor.winfo_exists():
            return

        self.gutter.delete("all")

        # 获取总逻辑行数
        total_lines = int(
            self.editor.index("end-1c").split(".")[0]
        )

        # 根据每一行实际显示位置绘制行号
        for line in range(1, total_lines + 1):

            index = f"{line}.0"

            # 获取该行在屏幕上的实际位置
            info = self.editor.dlineinfo(index)

            if info is None:
                continue

            x, y, width, height, baseline = info

            # 只绘制当前可见的行号
            self.gutter.create_text(
                40,
                y + baseline,
                text=str(line),
                anchor="e",
                font=self.editor_font,
                fill="#999999"
            )

    # ==============================
    # 关闭窗口
    # ==============================

    def on_close(self):

        if self.save_timer:
            self.root.after_cancel(
                self.save_timer
            )
            self.save_timer = None

        if self.refresh_timer:
            self.root.after_cancel(
                self.refresh_timer
            )
            self.refresh_timer = None

        # 关闭前强制保存
        self.auto_save()

        self.root.destroy()


if __name__ == "__main__":

    root = tk.Tk()

    app = WritingTool(root)

    # 保存滚动条引用
    app.scrollbar = next(
        widget for widget in app.editor.master.winfo_children()
        if isinstance(widget, tk.Scrollbar)
    )

    root.mainloop()
