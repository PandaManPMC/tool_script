
import tkinter as tk
from tkinter import font
import os
import unicodedata


class WritingTool:

    def __init__(self, root):
        self.root = root
        self.root.title("文本写作工具  pmc v1.0 pandamancoin.com")
        self.root.geometry("550x900+150+50")
        self.root.minsize(500, 600)
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

        # 滚动条
        self.scrollbar = tk.Scrollbar(
            container,
            command=self.on_scroll
        )
        self.scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        # 右侧段落统计区域
        stats_frame = tk.Frame(
            container,
            width=135,
            bg="#fafafa"
        )
        stats_frame.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )
        stats_frame.pack_propagate(False)

        # 统计标题
        stats_header = tk.Frame(
            stats_frame,
            bg="#fafafa",
            height=36
        )
        stats_header.pack(fill=tk.X)
        stats_header.pack_propagate(False)

        tk.Label(
            stats_header,
            text="段落",
            font=("Microsoft YaHei", 9),
            bg="#fafafa",
            fg="#999999"
        ).place(
            x=15,
            rely=0.5,
            anchor="w"
        )

        tk.Label(
            stats_header,
            text="字数",
            font=("Microsoft YaHei", 9),
            bg="#fafafa",
            fg="#999999"
        ).place(
            x=105,
            rely=0.5,
            anchor="e"
        )

        self.stats_canvas = tk.Canvas(
            stats_frame,
            bg="#fafafa",
            highlightthickness=0
        )
        self.stats_canvas.pack(
            fill=tk.BOTH,
            expand=True
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
            spacing1=5,
            spacing3=7
        )
        self.editor.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
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

        # 滚动同步
        self.editor.configure(
            yscrollcommand=self.on_editor_scroll
        )

        # ==============================
        # 底部状态栏（保留原有功能）
        # ==============================

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
        self.schedule_refresh()

    # ==============================
    # 字数统计
    # ==============================

    def count_words(self, content):

        count = 0

        for char in content:

            # 空白不计数
            if char.isspace():
                continue

            category = unicodedata.category(char)

            # 标点符号不计数
            if category.startswith("P"):
                continue

            # 控制字符不计数
            if category.startswith("C"):
                continue

            count += 1

        return count

    # ==============================
    # 全文统计
    # ==============================

    def update_word_count(self):

        content = self.editor.get(
            "1.0",
            "end-1c"
        )

        count = self.count_words(content)

        self.word_label.config(
            text=f"当前字数：{count}"
        )

    # ==============================
    # 右侧段落统计
    # ==============================

    def update_paragraph_stats(self):

        self.stats_canvas.delete("all")

        total_lines = int(
            self.editor.index("end-1c").split(".")[0]
        )

        paragraph_number = 0

        for line in range(1, total_lines + 1):

            start = f"{line}.0"
            end = f"{line}.0 lineend"

            content = self.editor.get(
                start,
                end
            )

            # 空行不展示
            if not content.strip():
                continue

            paragraph_number += 1

            count = self.count_words(content)

            # 根据段落字数设置颜色
            if count > 50:
                count_color = "#e74c3c"
            elif count > 40:
                count_color = "#e6a23c"
            else:
                count_color = "#666666"

            # 获取段落实际显示位置
            info = self.editor.dlineinfo(start)

            if info is None:
                continue

            x, y, width, height, baseline = info

            text_y = y + baseline

            # 段落编号
            self.stats_canvas.create_text(
                15,
                text_y,
                text=str(paragraph_number),
                anchor="w",
                font=("Microsoft YaHei", 9),
                fill="#999999"
            )

            # 字数
            self.stats_canvas.create_text(
                105,
                text_y,
                text=str(count),
                anchor="e",
                font=("Microsoft YaHei", 10, "bold"),
                fill=count_color
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

        self.scrollbar.set(first, last)
        self.schedule_refresh()

    # ==============================
    # 刷新
    # ==============================

    def schedule_refresh(self, event=None):

        if self.refresh_timer is None:

            self.refresh_timer = self.root.after_idle(
                self.update_layout
            )

    def update_layout(self):

        self.refresh_timer = None

        if not self.editor.winfo_exists():
            return

        self.update_line_numbers()
        self.update_paragraph_stats()

    # ==============================
    # 行号刷新
    # ==============================

    def update_line_numbers(self):

        self.gutter.delete("all")

        total_lines = int(
            self.editor.index("end-1c").split(".")[0]
        )

        for line in range(1, total_lines + 1):

            index = f"{line}.0"

            info = self.editor.dlineinfo(index)

            if info is None:
                continue

            x, y, width, height, baseline = info

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

    root.mainloop()
