import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "json_formatter_data.json"
)


class JSONFormatter(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("PMC Tool JSON Formatter blog.pandamancoin.com")
        self.geometry("1200x750")
        self.minsize(900, 600)

        self.nodes = []
        self.line_nodes = {}
        self.collapsed = set()

        self.create_ui()
        self.load_saved_json()

    # ============================================================
    # UI
    # ============================================================

    def create_ui(self):
        # ============================================================
        # 顶部按钮区域
        # ============================================================

        top_frame = ttk.Frame(self)
        top_frame.pack(
            fill=tk.X,
            padx=10,
            pady=8
        )

        format_btn = ttk.Button(
            top_frame,
            text="格式化",
            command=self.format_json
        )
        format_btn.pack(
            side=tk.LEFT,
            padx=(0, 8)
        )

        clear_btn = ttk.Button(
            top_frame,
            text="清空",
            command=self.clear_all
        )
        clear_btn.pack(
            side=tk.LEFT,
            padx=(0, 8)
        )

        expand_btn = ttk.Button(
            top_frame,
            text="全部展开",
            command=self.expand_all
        )
        expand_btn.pack(
            side=tk.LEFT,
            padx=(0, 8)
        )

        collapse_btn = ttk.Button(
            top_frame,
            text="全部收起",
            command=self.collapse_all
        )
        collapse_btn.pack(
            side=tk.LEFT
        )

        # ============================================================
        # 主区域
        #
        # 使用 tk.PanedWindow，而不是 ttk.PanedWindow
        # 这样可以直接控制 sash 的位置
        # ============================================================

        main_frame = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            sashrelief=tk.RAISED,
            showhandle=False
        )

        main_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        # ============================================================
        # 左侧 JSON 输入
        # ============================================================

        left_frame = ttk.LabelFrame(
            main_frame,
            text="JSON 输入"
        )

        # ============================================================
        # 右侧格式化结果
        # ============================================================

        right_frame = ttk.LabelFrame(
            main_frame,
            text="格式化结果"
        )

        # ============================================================
        # 加入左右区域
        #
        # 不使用 weight 控制比例
        # 后面通过 sashpos 精确设置 30%
        # ============================================================

        main_frame.add(
            left_frame,
            stretch="always",
            minsize=200
        )

        main_frame.add(
            right_frame,
            stretch="always",
            minsize=300
        )

        # ============================================================
        # 左侧 Text
        # ============================================================

        self.input_text = tk.Text(
            left_frame,
            wrap=tk.NONE,
            undo=True,
            font=("Consolas", 11)
        )

        self.input_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        # 左侧垂直滚动条
        input_scroll_y = ttk.Scrollbar(
            left_frame,
            orient=tk.VERTICAL,
            command=self.input_text.yview
        )

        input_scroll_y.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        # 左侧水平滚动条
        input_scroll_x = ttk.Scrollbar(
            left_frame,
            orient=tk.HORIZONTAL,
            command=self.input_text.xview
        )

        input_scroll_x.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )

        self.input_text.configure(
            yscrollcommand=input_scroll_y.set,
            xscrollcommand=input_scroll_x.set
        )

        # ============================================================
        # 右侧 Text
        # ============================================================

        self.output_text = tk.Text(
            right_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            state=tk.DISABLED,
            cursor="arrow"
        )

        self.output_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        # 右侧垂直滚动条
        output_scroll_y = ttk.Scrollbar(
            right_frame,
            orient=tk.VERTICAL,
            command=self.output_text.yview
        )

        output_scroll_y.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        # 右侧水平滚动条
        output_scroll_x = ttk.Scrollbar(
            right_frame,
            orient=tk.HORIZONTAL,
            command=self.output_text.xview
        )

        output_scroll_x.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )

        self.output_text.configure(
            yscrollcommand=output_scroll_y.set,
            xscrollcommand=output_scroll_x.set
        )

        # ============================================================
        # 右侧鼠标点击
        # ============================================================

        self.output_text.bind(
            "<Button-1>",
            self.output_click
        )

        # ============================================================
        # 状态栏
        # ============================================================

        self.status_var = tk.StringVar(
            value="就绪"
        )

        status = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor=tk.W
        )

        status.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 5)
        )

        # ============================================================
        # 设置初始比例
        #
        # 必须等窗口完成布局之后再设置 sash
        #
        # 左边 30%
        # 右边 70%
        # ============================================================

        def set_initial_sash():
            width = main_frame.winfo_width()

            if width > 0:
                # 30% 的位置
                sash_position = int(width * 0.30)

                main_frame.sash_place(
                    0,
                    sash_position,
                    0
                )

        # 延迟执行，确保 PanedWindow 已经完成布局
        self.after(
            100,
            set_initial_sash
        )

    # ============================================================
    # JSON 格式化
    # ============================================================

    def format_json(self):
        raw = self.input_text.get("1.0", tk.END).strip()

        if not raw:
            messagebox.showwarning(
                "提示",
                "请输入 JSON"
            )
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "JSON 格式错误",
                f"{e.msg}\n\n"
                f"行：{e.lineno}\n"
                f"列：{e.colno}"
            )
            self.status_var.set("JSON 格式错误")
            return

        # 保存原始 JSON
        self.save_json(raw)

        # 清空旧状态
        self.nodes.clear()
        self.line_nodes.clear()
        self.collapsed.clear()

        # 生成格式化内容
        lines = []
        self.build_json_lines(
            data,
            lines,
            level=0,
            path=()
        )

        self.render_output(lines)

        self.status_var.set(
            f"格式化完成，共 {len(lines)} 行"
        )

    # ============================================================
    # 生成 JSON 文本
    # ============================================================

    def build_json_lines(
        self,
        value,
        lines,
        level,
        path
    ):
        indent = "    " * level

        # dict
        if isinstance(value, dict):

            if not value:
                lines.append({
                    "text": indent + "{}",
                    "node": None
                })
                return

            node_id = len(self.nodes)

            node = {
                "id": node_id,
                "path": path,
                "type": "dict",
                "level": level,
                "collapsed": False
            }

            self.nodes.append(node)

            # 开始行
            lines.append({
                "text": indent + "{",
                "node": node_id,
                "action": "toggle"
            })

            items = list(value.items())

            for index, (key, val) in enumerate(items):

                comma = "," if index < len(items) - 1 else ""

                key_text = json.dumps(
                    key,
                    ensure_ascii=False
                )

                child_path = path + (key,)

                if isinstance(val, (dict, list)):

                    # 子节点
                    child_node_id = len(self.nodes)

                    child_node = {
                        "id": child_node_id,
                        "path": child_path,
                        "type": "dict"
                        if isinstance(val, dict)
                        else "list",
                        "level": level + 1,
                        "collapsed": False
                    }

                    self.nodes.append(child_node)

                    if isinstance(val, dict):
                        opening = "{"
                    else:
                        opening = "["

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + key_text
                            + ": "
                            + opening,
                        "node": child_node_id,
                        "action": "toggle",
                        "parent": node_id,
                        "suffix": comma
                    })

                    self.build_children(
                        val,
                        lines,
                        level + 2,
                        child_node_id,
                        child_path,
                        comma
                    )

                else:
                    value_text = json.dumps(
                        val,
                        ensure_ascii=False
                    )

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + key_text
                            + ": "
                            + value_text
                            + comma,
                        "node": None,
                        "parent": node_id
                    })

            lines.append({
                "text": indent + "}",
                "node": None,
                "close_for": node_id
            })

        # list
        elif isinstance(value, list):

            if not value:
                lines.append({
                    "text": indent + "[]",
                    "node": None
                })
                return

            node_id = len(self.nodes)

            node = {
                "id": node_id,
                "path": path,
                "type": "list",
                "level": level,
                "collapsed": False
            }

            self.nodes.append(node)

            lines.append({
                "text": indent + "[",
                "node": node_id,
                "action": "toggle"
            })

            for index, val in enumerate(value):

                comma = "," if index < len(value) - 1 else ""

                child_path = path + (index,)

                if isinstance(val, (dict, list)):

                    child_node_id = len(self.nodes)

                    child_node = {
                        "id": child_node_id,
                        "path": child_path,
                        "type":
                            "dict"
                            if isinstance(val, dict)
                            else "list",
                        "level": level + 1,
                        "collapsed": False
                    }

                    self.nodes.append(child_node)

                    opening = (
                        "{"
                        if isinstance(val, dict)
                        else "["
                    )

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + opening,
                        "node": child_node_id,
                        "action": "toggle",
                        "parent": node_id,
                        "suffix": comma
                    })

                    self.build_children(
                        val,
                        lines,
                        level + 2,
                        child_node_id,
                        child_path,
                        comma
                    )

                else:

                    value_text = json.dumps(
                        val,
                        ensure_ascii=False
                    )

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + value_text
                            + comma,
                        "node": None,
                        "parent": node_id
                    })

            lines.append({
                "text": indent + "]",
                "node": None,
                "close_for": node_id
            })

        else:

            lines.append({
                "text": indent + json.dumps(
                    value,
                    ensure_ascii=False
                ),
                "node": None
            })

    # ============================================================
    # 子节点
    # ============================================================

    def build_children(
        self,
        value,
        lines,
        level,
        node_id,
        path,
        parent_comma
    ):
        indent = "    " * level

        if isinstance(value, dict):

            items = list(value.items())

            for index, (key, val) in enumerate(items):

                comma = "," if index < len(items) - 1 else ""

                key_text = json.dumps(
                    key,
                    ensure_ascii=False
                )

                child_path = path + (key,)

                if isinstance(val, (dict, list)):

                    child_node_id = len(self.nodes)

                    child_node = {
                        "id": child_node_id,
                        "path": child_path,
                        "type":
                            "dict"
                            if isinstance(val, dict)
                            else "list",
                        "level": level,
                        "collapsed": False
                    }

                    self.nodes.append(child_node)

                    opening = (
                        "{"
                        if isinstance(val, dict)
                        else "["
                    )

                    lines.append({
                        "text":
                            indent
                            + key_text
                            + ": "
                            + opening,
                        "node": child_node_id,
                        "action": "toggle",
                        "parent": node_id,
                        "suffix": comma
                    })

                    self.build_children(
                        val,
                        lines,
                        level + 1,
                        child_node_id,
                        child_path,
                        comma
                    )

                else:

                    lines.append({
                        "text":
                            indent
                            + key_text
                            + ": "
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + comma,
                        "node": None,
                        "parent": node_id
                    })

        elif isinstance(value, list):

            for index, val in enumerate(value):

                comma = "," if index < len(value) - 1 else ""

                child_path = path + (index,)

                if isinstance(val, (dict, list)):

                    child_node_id = len(self.nodes)

                    child_node = {
                        "id": child_node_id,
                        "path": child_path,
                        "type":
                            "dict"
                            if isinstance(val, dict)
                            else "list",
                        "level": level,
                        "collapsed": False
                    }

                    self.nodes.append(child_node)

                    opening = (
                        "{"
                        if isinstance(val, dict)
                        else "["
                    )

                    lines.append({
                        "text":
                            indent + opening,
                        "node": child_node_id,
                        "action": "toggle",
                        "parent": node_id,
                        "suffix": comma
                    })

                    self.build_children(
                        val,
                        lines,
                        level + 1,
                        child_node_id,
                        child_path,
                        comma
                    )

                else:

                    lines.append({
                        "text":
                            indent
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + comma,
                        "node": None,
                        "parent": node_id
                    })

        closing = "}" if isinstance(value, dict) else "]"

        lines.append({
            "text":
                "    " * (level - 1)
                + closing,
            "node": None,
            "close_for": node_id,
            "suffix": parent_comma
        })

    # ============================================================
    # 渲染
    # ============================================================

    def render_output(self, lines):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)

        self.line_nodes.clear()

        for line_index, item in enumerate(lines):

            node_id = item.get("node")

            if node_id is not None:

                node = self.nodes[node_id]

                symbol = (
                    "▶ "
                    if node_id in self.collapsed
                    else "▼ "
                )

                self.output_text.insert(
                    tk.END,
                    symbol
                )

                self.output_text.insert(
                    tk.END,
                    item["text"]
                )

                self.line_nodes[
                    line_index + 1
                ] = node_id

            else:

                self.output_text.insert(
                    tk.END,
                    "  " + item["text"]
                )

            self.output_text.insert(
                tk.END,
                "\n"
            )

        self.output_text.config(state=tk.DISABLED)

    # ============================================================
    # 点击展开 / 收起
    # ============================================================

    def output_click(self, event):

        index = self.output_text.index(
            f"@{event.x},{event.y}"
        )

        line = int(index.split(".")[0])

        node_id = self.line_nodes.get(line)

        if node_id is None:
            return

        # 只有点击行最前面的 ▶ / ▼ 才触发
        column = int(index.split(".")[1])

        if column <= 2:

            if node_id in self.collapsed:
                self.collapsed.remove(node_id)
            else:
                self.collapsed.add(node_id)

            self.refresh_collapsed()

    # ============================================================
    # 根据 collapsed 状态重新生成显示
    # ============================================================

    def refresh_collapsed(self):

        try:
            raw = self.input_text.get(
                "1.0",
                tk.END
            ).strip()

            data = json.loads(raw)

        except Exception:
            return

        lines = []

        self.build_visible_lines(
            data,
            lines,
            0,
            ()
        )

        self.render_output(lines)

    # ============================================================
    # 生成折叠后的文本
    # ============================================================

    def build_visible_lines(
        self,
        value,
        lines,
        level,
        path
    ):

        indent = "    " * level

        # 找当前节点
        current_id = self.find_node(path)

        collapsed = (
            current_id is not None
            and current_id in self.collapsed
        )

        if isinstance(value, dict):

            if not value:
                lines.append({
                    "text": indent + "{}",
                    "node": None
                })
                return

            node_id = current_id

            lines.append({
                "text": indent + "{",
                "node": node_id,
                "action": "toggle"
            })

            if collapsed:
                lines.append({
                    "text":
                        "    " * (level + 1)
                        + "...",
                    "node": None
                })

                lines.append({
                    "text": indent + "}",
                    "node": None
                })

                return

            items = list(value.items())

            for i, (key, val) in enumerate(items):

                comma = "," if i < len(items) - 1 else ""

                key_text = json.dumps(
                    key,
                    ensure_ascii=False
                )

                child_path = path + (key,)

                if isinstance(val, (dict, list)):

                    self.build_visible_child(
                        key_text,
                        val,
                        lines,
                        level + 1,
                        child_path,
                        comma
                    )

                else:

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + key_text
                            + ": "
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + comma,
                        "node": None
                    })

            lines.append({
                "text": indent + "}",
                "node": None
            })

        elif isinstance(value, list):

            if not value:
                lines.append({
                    "text": indent + "[]",
                    "node": None
                })
                return

            node_id = current_id

            lines.append({
                "text": indent + "[",
                "node": node_id,
                "action": "toggle"
            })

            if collapsed:
                lines.append({
                    "text":
                        "    " * (level + 1)
                        + "...",
                    "node": None
                })

                lines.append({
                    "text": indent + "]",
                    "node": None
                })

                return

            for i, val in enumerate(value):

                comma = "," if i < len(value) - 1 else ""

                child_path = path + (i,)

                if isinstance(val, (dict, list)):

                    self.build_visible_child(
                        None,
                        val,
                        lines,
                        level + 1,
                        child_path,
                        comma
                    )

                else:

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + comma,
                        "node": None
                    })

            lines.append({
                "text": indent + "]",
                "node": None
            })

    def build_visible_child(
        self,
        key_text,
        value,
        lines,
        level,
        path,
        comma
    ):

        node_id = self.find_node(path)

        indent = "    " * level

        opening = (
            "{"
            if isinstance(value, dict)
            else "["
        )

        prefix = ""

        if key_text is not None:
            prefix = key_text + ": "

        lines.append({
            "text":
                indent
                + prefix
                + opening,
            "node": node_id,
            "action": "toggle"
        })

        if node_id in self.collapsed:

            lines.append({
                "text":
                    "    " * (level + 1)
                    + "..."
            })

            closing = (
                "}"
                if isinstance(value, dict)
                else "]"
            )

            lines.append({
                "text":
                    indent
                    + closing
                    + comma
            })

            return

        if isinstance(value, dict):

            items = list(value.items())

            for i, (key, val) in enumerate(items):

                item_comma = (
                    ","
                    if i < len(items) - 1
                    else ""
                )

                key_text2 = json.dumps(
                    key,
                    ensure_ascii=False
                )

                child_path = path + (key,)

                if isinstance(val, (dict, list)):

                    self.build_visible_child(
                        key_text2,
                        val,
                        lines,
                        level + 1,
                        child_path,
                        item_comma
                    )

                else:

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + key_text2
                            + ": "
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + item_comma
                    })

        else:

            for i, val in enumerate(value):

                item_comma = (
                    ","
                    if i < len(value) - 1
                    else ""
                )

                child_path = path + (i,)

                if isinstance(val, (dict, list)):

                    self.build_visible_child(
                        None,
                        val,
                        lines,
                        level + 1,
                        child_path,
                        item_comma
                    )

                else:

                    lines.append({
                        "text":
                            "    " * (level + 1)
                            + json.dumps(
                                val,
                                ensure_ascii=False
                            )
                            + item_comma
                    })

        closing = (
            "}"
            if isinstance(value, dict)
            else "]"
        )

        lines.append({
            "text":
                indent
                + closing
                + comma
        })

    # ============================================================
    # 查找节点
    # ============================================================

    def find_node(self, path):

        for node in self.nodes:
            if tuple(node["path"]) == tuple(path):
                return node["id"]

        return None

    # ============================================================
    # 全部展开
    # ============================================================

    def expand_all(self):

        self.collapsed.clear()
        self.refresh_collapsed()

    # ============================================================
    # 全部收起
    # ============================================================

    def collapse_all(self):

        self.collapsed = {
            node["id"]
            for node in self.nodes
        }

        self.refresh_collapsed()

    # ============================================================
    # 清空
    # ============================================================

    def clear_all(self):

        self.input_text.delete(
            "1.0",
            tk.END
        )

        self.output_text.config(
            state=tk.NORMAL
        )

        self.output_text.delete(
            "1.0",
            tk.END
        )

        self.output_text.config(
            state=tk.DISABLED
        )

        self.nodes.clear()
        self.collapsed.clear()
        self.line_nodes.clear()

        self.status_var.set("已清空")

    # ============================================================
    # 保存
    # ============================================================

    def save_json(self, text):

        try:
            with open(
                SAVE_FILE,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    {
                        "json": text
                    },
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            print(
                "保存 JSON 失败:",
                e
            )

    # ============================================================
    # 读取
    # ============================================================

    def load_saved_json(self):

        if not os.path.exists(SAVE_FILE):
            return

        try:
            with open(
                SAVE_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            text = data.get(
                "json",
                ""
            )

            if text:

                self.input_text.insert(
                    "1.0",
                    text
                )

                # 自动格式化
                self.format_json()

        except Exception as e:
            print(
                "读取保存数据失败:",
                e
            )


if __name__ == "__main__":

    app = JSONFormatter()

    app.mainloop()
