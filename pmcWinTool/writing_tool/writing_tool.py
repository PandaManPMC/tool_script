import tkinter as tk
from tkinter import ttk, font, filedialog, simpledialog, messagebox
import os
import json
import shutil
import unicodedata


class WritingTool:
    """
    中文网文写作工具
    - 单小说项目（一个根目录）
    - 左侧文件树：文件夹和 .txt 文件
    - 顶部多标签编辑
    - 每个文件独立编辑、撤销和自动保存
    - 保留全文字数、段落字数、行号、滚动同步和底部保存状态
    """

    def __init__(self, root):
        self.root = root
        self.root.title("中文写作工具 pmc v1.0 pandamancoin.com")

        # 左侧文件树增加的宽度不挤压原有正文区域：
        # 原来约 550px 的编辑区域 + 210px 文件树。
        self.root.geometry("760x900+150+50")
        self.root.minsize(700, 600)
        self.root.configure(bg="#f5f5f5")

        self.save_delay = 2000
        self.refresh_timer = None
        self.active_path = None
        self.documents = {}       # path -> {widget, dirty, save_timer}
        self.widget_to_path = {}  # Text widget -> path

        self.project_root = None
        self.config_path = self.get_config_path()

        self.editor_font = font.Font(
            family="Microsoft YaHei",
            size=14
        )

        self.build_ui()
        self.load_project_setting()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.project_root:
            self.root.after(150, self.choose_project_folder)

    # =========================================================
    # 配置
    # =========================================================

    def get_config_path(self):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "ChineseNovelWriter")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "config.json")

    def load_project_setting(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                path = data.get("project_root")
                if path and os.path.isdir(path):
                    self.project_root = os.path.abspath(path)
        except Exception:
            self.project_root = None

        self.update_project_title()
        if self.project_root:
            self.refresh_file_tree()

    def save_project_setting(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"project_root": self.project_root},
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            messagebox.showerror("保存设置失败", str(e), parent=self.root)

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg="#ffffff", height=55)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text="中文写作工具",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ffffff",
            fg="#333333"
        ).pack(side=tk.LEFT, padx=(15, 12))

        self.project_label = tk.Label(
            toolbar,
            text="未选择小说目录",
            font=("Microsoft YaHei", 9),
            bg="#ffffff",
            fg="#888888",
            anchor="w"
        )
        self.project_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            toolbar,
            text="选择项目目录",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            bg="#f1f3f5",
            activebackground="#e5e9ed",
            command=self.choose_project_folder
        ).pack(side=tk.LEFT, padx=8, pady=10)

        self.word_label = tk.Label(
            toolbar,
            text="当前字数：0",
            font=("Microsoft YaHei", 10),
            bg="#ffffff",
            fg="#666666"
        )
        self.word_label.pack(side=tk.RIGHT, padx=15)

        # 顶部文件 Tab 区域
        self.tabbar = tk.Frame(self.root, bg="#eeeeee", height=36)
        self.tabbar.pack(fill=tk.X)
        self.tabbar.pack_propagate(False)

        # 主体区域：左侧项目树 + 原有编辑器区域
        body = tk.Frame(self.root, bg="#f5f5f5")
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 左侧文件管理
        sidebar = tk.Frame(body, bg="#f8f8f8", width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        sidebar.pack_propagate(False)

        sidebar_header = tk.Frame(sidebar, bg="#f8f8f8", height=38)
        sidebar_header.pack(fill=tk.X)
        sidebar_header.pack_propagate(False)

        tk.Label(
            sidebar_header,
            text="项目文件",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#f8f8f8",
            fg="#555555"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            sidebar_header,
            text="↻",
            font=("Microsoft YaHei", 11),
            relief=tk.FLAT,
            bg="#f8f8f8",
            activebackground="#e8e8e8",
            command=self.refresh_file_tree
        ).pack(side=tk.RIGHT, padx=5)

        tree_frame = tk.Frame(sidebar, bg="#f8f8f8")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.file_tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse"
        )
        tree_scroll = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.file_tree.bind("<Button-3>", self.show_tree_context_menu)

        # 文件树底部快捷按钮
        sidebar_actions = tk.Frame(sidebar, bg="#f8f8f8", height=38)
        sidebar_actions.pack(side=tk.BOTTOM, fill=tk.X)
        sidebar_actions.pack_propagate(False)

        tk.Button(
            sidebar_actions,
            text="+ 文件夹",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            bg="#eeeeee",
            command=self.new_folder
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 2), pady=5)

        tk.Button(
            sidebar_actions,
            text="+ 文件",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            bg="#eeeeee",
            command=self.new_file
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 5), pady=5)

        # 原有编辑器容器，保留行号、正文、统计栏和滚动条
        container = tk.Frame(body, bg="#ffffff")
        container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gutter = tk.Canvas(
            container,
            width=48,
            bg="#f7f7f7",
            highlightthickness=0
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        self.scrollbar = tk.Scrollbar(
            container,
            command=self.on_scroll
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧段落统计区域
        stats_frame = tk.Frame(container, width=135, bg="#fafafa")
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y)
        stats_frame.pack_propagate(False)

        stats_header = tk.Frame(stats_frame, bg="#fafafa", height=36)
        stats_header.pack(fill=tk.X)
        stats_header.pack_propagate(False)

        tk.Label(
            stats_header,
            text="段落",
            font=("Microsoft YaHei", 9),
            bg="#fafafa",
            fg="#999999"
        ).place(x=15, rely=0.5, anchor="w")

        tk.Label(
            stats_header,
            text="字数",
            font=("Microsoft YaHei", 9),
            bg="#fafafa",
            fg="#999999"
        ).place(x=105, rely=0.5, anchor="e")

        self.stats_canvas = tk.Canvas(
            stats_frame,
            bg="#fafafa",
            highlightthickness=0
        )
        self.stats_canvas.pack(fill=tk.BOTH, expand=True)

        # 每个文件有独立 Text 控件，切换文件时保留各自撤销历史
        self.text_frame = tk.Frame(container, bg="#ffffff")
        self.text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.empty_label = tk.Label(
            self.text_frame,
            text="请在左侧选择或新建一个文本文件",
            font=("Microsoft YaHei", 11),
            bg="#ffffff",
            fg="#aaaaaa"
        )
        self.empty_label.pack(fill=tk.BOTH, expand=True)

        self.editor = None

        # 底部状态栏（保留原有功能）
        statusbar = tk.Frame(self.root, bg="#ffffff", height=38)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        statusbar.pack_propagate(False)

        self.save_status = tk.Label(
            statusbar,
            text="请选择小说项目目录",
            font=("Microsoft YaHei", 9),
            bg="#ffffff",
            fg="#888888"
        )
        self.save_status.pack(side=tk.LEFT, padx=15)

    # =========================================================
    # 项目目录
    # =========================================================

    def choose_project_folder(self):
        folder = filedialog.askdirectory(
            title="选择小说项目根目录",
            parent=self.root,
            mustexist=True
        )
        if not folder:
            return

        folder = os.path.abspath(folder)
        if self.project_root and os.path.normcase(folder) == os.path.normcase(self.project_root):
            return

        if not self.close_all_documents_with_prompt():
            return

        self.project_root = folder
        self.save_project_setting()
        self.update_project_title()
        self.refresh_file_tree()
        self.save_status.config(text="已打开小说项目", fg="#888888")

    def update_project_title(self):
        if self.project_root:
            name = os.path.basename(os.path.normpath(self.project_root))
            self.project_label.config(text=f"项目：{name}")
        else:
            self.project_label.config(text="未选择小说目录")

    def refresh_file_tree(self):
        if not hasattr(self, "file_tree"):
            return

        self.file_tree.delete(*self.file_tree.get_children())

        if not self.project_root or not os.path.isdir(self.project_root):
            return

        root_path = os.path.abspath(self.project_root)
        root_name = os.path.basename(os.path.normpath(root_path)) or root_path

        self.file_tree.insert(
            "",
            tk.END,
            iid=root_path,
            text=root_name,
            values=("folder",),
            open=True
        )
        self._insert_directory_contents(root_path)

    def _insert_directory_contents(self, folder):
        try:
            entries = list(os.scandir(folder))
        except (PermissionError, OSError):
            return

        dirs = []
        files = []
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                elif entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".txt"):
                    files.append(entry)
            except OSError:
                continue

        dirs.sort(key=lambda x: x.name.casefold())
        files.sort(key=lambda x: x.name.casefold())

        for entry in dirs:
            path = os.path.abspath(entry.path)
            self.file_tree.insert(
                folder,
                tk.END,
                iid=path,
                text=entry.name,
                values=("folder",),
                open=False
            )
            self._insert_directory_contents(path)

        for entry in files:
            path = os.path.abspath(entry.path)
            self.file_tree.insert(
                folder,
                tk.END,
                iid=path,
                text=entry.name,
                values=("file",),
                open=False
            )

    def is_inside_project(self, path):
        if not self.project_root:
            return False
        try:
            root = os.path.normcase(os.path.abspath(self.project_root))
            target = os.path.normcase(os.path.abspath(path))
            return os.path.commonpath([root, target]) == root
        except (ValueError, OSError):
            return False

    def get_selected_tree_path(self):
        selection = self.file_tree.selection()
        if selection:
            return selection[0]
        return self.project_root

    def get_target_directory(self):
        path = self.get_selected_tree_path()
        if path and os.path.isdir(path):
            return path
        if path and os.path.isfile(path):
            return os.path.dirname(path)
        return self.project_root

    # =========================================================
    # 文件树操作
    # =========================================================

    def new_folder(self):
        if not self.project_root:
            messagebox.showinfo("提示", "请先选择小说项目目录。", parent=self.root)
            return

        parent = self.get_target_directory()
        name = simpledialog.askstring(
            "新建文件夹",
            "请输入文件夹名称：",
            parent=self.root
        )
        if name is None:
            return
        name = name.strip()
        if not self.validate_name(name):
            return

        path = os.path.join(parent, name)
        try:
            os.mkdir(path)
            self.refresh_file_tree()
            self.file_tree.item(parent, open=True)
            self.file_tree.selection_set(path)
            self.file_tree.see(path)
        except FileExistsError:
            messagebox.showerror("创建失败", "同名文件或文件夹已经存在。", parent=self.root)
        except Exception as e:
            messagebox.showerror("创建失败", str(e), parent=self.root)

    def new_file(self):
        if not self.project_root:
            messagebox.showinfo("提示", "请先选择小说项目目录。", parent=self.root)
            return

        parent = self.get_target_directory()
        name = simpledialog.askstring(
            "新建文本文件",
            "请输入文件名称（无需输入 .txt）：",
            parent=self.root
        )
        if name is None:
            return
        name = name.strip()
        if not self.validate_name(name):
            return

        if not name.lower().endswith(".txt"):
            name += ".txt"
        elif name.lower().endswith(".txt.txt"):
            name = name[:-4]

        path = os.path.abspath(os.path.join(parent, name))
        try:
            with open(path, "x", encoding="utf-8"):
                pass
            self.refresh_file_tree()
            self.file_tree.item(parent, open=True)
            self.file_tree.selection_set(path)
            self.file_tree.see(path)
            self.open_file(path)
        except FileExistsError:
            messagebox.showerror("创建失败", "同名文件已经存在。", parent=self.root)
        except Exception as e:
            messagebox.showerror("创建失败", str(e), parent=self.root)

    @staticmethod
    def validate_name(name):
        if not name or name in (".", ".."):
            messagebox.showwarning("名称无效", "名称不能为空，也不能是 . 或 ..。")
            return False
        if any(ch in name for ch in ('\\', '/', ':', '*', '?', '"', '<', '>', '|')):
            messagebox.showwarning("名称无效", "名称不能包含 Windows 文件名不允许的字符。")
            return False
        return True

    def show_tree_context_menu(self, event):
        row = self.file_tree.identify_row(event.y)
        if row:
            self.file_tree.selection_set(row)

        path = row or self.project_root
        if not path:
            return

        is_root = os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.project_root))
        is_dir = os.path.isdir(path)

        menu = tk.Menu(self.root, tearoff=0)
        if is_dir:
            menu.add_command(label="新建文件夹", command=self.new_folder)
            menu.add_command(label="新建文本文件", command=self.new_file)
            if not is_root:
                menu.add_separator()
                menu.add_command(label="重命名", command=lambda p=path: self.rename_path(p))
                menu.add_command(label="删除文件夹", command=lambda p=path: self.delete_path(p))
            menu.add_separator()
            menu.add_command(label="刷新", command=self.refresh_file_tree)
        else:
            menu.add_command(label="打开", command=lambda p=path: self.open_file(p))
            menu.add_command(label="重命名", command=lambda p=path: self.rename_path(p))
            menu.add_command(label="删除文件", command=lambda p=path: self.delete_path(p))

        menu.tk_popup(event.x_root, event.y_root)

    def on_tree_select(self, event=None):
        selection = self.file_tree.selection()
        if not selection:
            return
        path = selection[0]
        if os.path.isfile(path) and path.lower().endswith(".txt"):
            self.open_file(path)

    def rename_path(self, old_path):
        if not self.is_inside_project(old_path):
            return

        is_file = os.path.isfile(old_path)
        old_name = os.path.basename(old_path)
        if is_file and old_name.lower().endswith(".txt"):
            initial = old_name[:-4]
        else:
            initial = old_name

        new_name = simpledialog.askstring(
            "重命名",
            "请输入新名称：",
            initialvalue=initial,
            parent=self.root
        )
        if new_name is None:
            return
        new_name = new_name.strip()
        if not self.validate_name(new_name):
            return

        if is_file:
            if not new_name.lower().endswith(".txt"):
                new_name += ".txt"
        new_path = os.path.abspath(os.path.join(os.path.dirname(old_path), new_name))

        if os.path.normcase(new_path) == os.path.normcase(old_path):
            return
        if os.path.exists(new_path):
            messagebox.showerror("重命名失败", "目标名称已经存在。", parent=self.root)
            return

        try:
            os.rename(old_path, new_path)
            self.remap_open_documents(old_path, new_path)
            self.refresh_file_tree()
            if os.path.exists(new_path):
                self.file_tree.selection_set(new_path)
                self.file_tree.see(new_path)
        except Exception as e:
            messagebox.showerror("重命名失败", str(e), parent=self.root)

    def remap_open_documents(self, old_path, new_path):
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)
        mapping = {}

        for path in list(self.documents.keys()):
            try:
                if os.path.commonpath([old_abs, os.path.abspath(path)]) == old_abs:
                    relative = os.path.relpath(path, old_abs)
                    updated = new_abs if relative == "." else os.path.join(new_abs, relative)
                    mapping[path] = os.path.abspath(updated)
            except ValueError:
                continue

        if not mapping:
            return

        new_documents = {}
        for old_key, doc in list(self.documents.items()):
            new_key = mapping.get(old_key, old_key)
            new_documents[new_key] = doc
            self.widget_to_path[doc["widget"]] = new_key

        self.documents = new_documents
        if self.active_path in mapping:
            self.active_path = mapping[self.active_path]

        # 路径改变后重新安排未保存文件的自动保存任务
        for path, doc in self.documents.items():
            timer = doc.get("save_timer")
            if timer:
                try:
                    self.root.after_cancel(timer)
                except tk.TclError:
                    pass
                doc["save_timer"] = None
            if doc["dirty"]:
                self.schedule_document_save(path)

        self.refresh_tabs()

    def delete_path(self, path):
        if not self.is_inside_project(path):
            return

        is_dir = os.path.isdir(path)
        label = "文件夹及其全部内容" if is_dir else "文件"
        if not messagebox.askyesno(
            "确认删除",
            f"确定要删除这个{label}吗？\n\n{path}\n\n此操作会直接删除磁盘上的内容。",
            parent=self.root
        ):
            return

        affected = []
        target = os.path.abspath(path)
        for doc_path in list(self.documents.keys()):
            try:
                if os.path.commonpath([target, os.path.abspath(doc_path)]) == target:
                    affected.append(doc_path)
            except ValueError:
                pass

        # 删除前处理相关打开文件的未保存内容
        for doc_path in affected:
            doc = self.documents[doc_path]
            if doc["dirty"]:
                answer = messagebox.askyesnocancel(
                    "文件尚未保存",
                    f"文件有未保存的修改：\n{doc_path}\n\n是否先保存？\n是：保存后删除\n否：放弃修改并删除\n取消：取消删除",
                    parent=self.root
                )
                if answer is None:
                    return
                if answer:
                    if not self.save_document(doc_path):
                        return

        try:
            if is_dir:
                shutil.rmtree(path)
            else:
                os.remove(path)

            for doc_path in affected:
                self.remove_document_without_prompt(doc_path)

            self.refresh_tabs()
            self.refresh_file_tree()
            if self.active_path is None:
                self.activate_first_document()
            self.save_status.config(text="已删除", fg="#888888")
        except Exception as e:
            messagebox.showerror("删除失败", str(e), parent=self.root)

    # =========================================================
    # 文档和 Tab
    # =========================================================

    def create_editor(self, path, content):
        editor = tk.Text(
            self.text_frame,
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

        editor.insert("1.0", content)
        editor.edit_modified(False)

        editor.bind("<<Modified>>", self.on_text_changed)
        editor.bind("<KeyRelease>", self.on_editor_action)
        editor.bind("<ButtonRelease-1>", self.on_editor_action)
        editor.bind("<Configure>", self.schedule_refresh)
        editor.bind("<MouseWheel>", self.schedule_refresh)
        editor.bind("<Button-4>", self.schedule_refresh)
        editor.bind("<Button-5>", self.schedule_refresh)

        editor.configure(
            yscrollcommand=lambda first, last, w=editor:
                self.on_editor_scroll(w, first, last)
        )
        return editor

    def open_file(self, path):
        if not self.is_inside_project(path):
            messagebox.showwarning("无法打开", "只能打开小说项目根目录中的文件。", parent=self.root)
            return
        if not os.path.isfile(path) or not path.lower().endswith(".txt"):
            return

        path = os.path.abspath(path)
        if path in self.documents:
            self.activate_document(path)
            return

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("打开失败", str(e), parent=self.root)
            return

        editor = self.create_editor(path, content)
        self.documents[path] = {
            "widget": editor,
            "dirty": False,
            "save_timer": None
        }
        self.widget_to_path[editor] = path

        self.activate_document(path)
        self.refresh_tabs()
        self.save_status.config(text="已打开：" + os.path.basename(path), fg="#888888")

    def activate_document(self, path):
        if path not in self.documents:
            return

        # 切换前先把当前文档的待保存内容写入磁盘，避免切换时丢失
        if self.active_path and self.active_path != path:
            current_doc = self.documents.get(self.active_path)
            if current_doc and current_doc["dirty"]:
                self.save_document(self.active_path)

        if self.editor is not None:
            self.editor.pack_forget()

        self.empty_label.pack_forget()

        self.active_path = path
        self.editor = self.documents[path]["widget"]
        self.editor.pack(fill=tk.BOTH, expand=True)

        self.scrollbar.configure(command=self.on_scroll)
        self.update_word_count()
        self.schedule_refresh()
        self.refresh_tabs()

        if self.documents[path]["dirty"]:
            self.save_status.config(text="有未保存的修改", fg="#e67e22")
        else:
            self.save_status.config(text="已打开：" + os.path.basename(path), fg="#888888")

    def activate_first_document(self):
        if self.documents:
            self.activate_document(next(iter(self.documents)))
        else:
            self.active_path = None
            self.editor = None
            self.empty_label.pack(fill=tk.BOTH, expand=True)
            self.gutter.delete("all")
            self.stats_canvas.delete("all")
            self.word_label.config(text="当前字数：0")
            self.save_status.config(text="没有打开的文件", fg="#888888")

    def refresh_tabs(self):
        for child in self.tabbar.winfo_children():
            child.destroy()

        for path in self.documents:
            doc = self.documents[path]
            active = path == self.active_path
            bg = "#ffffff" if active else "#e9e9e9"
            fg = "#333333" if active else "#777777"
            name = os.path.basename(path)
            if doc["dirty"]:
                name += " *"

            tab = tk.Frame(
                self.tabbar,
                bg=bg,
                highlightthickness=1 if active else 0,
                highlightbackground="#d5d5d5"
            )
            tab.pack(side=tk.LEFT, padx=(0, 2), pady=(3, 0))

            label = tk.Label(
                tab,
                text=name,
                font=("Microsoft YaHei", 9),
                bg=bg,
                fg=fg,
                padx=10,
                pady=5,
                cursor="hand2"
            )
            label.pack(side=tk.LEFT)

            close = tk.Label(
                tab,
                text="×",
                font=("Microsoft YaHei", 11),
                bg=bg,
                fg="#888888",
                padx=7,
                cursor="hand2"
            )
            close.pack(side=tk.LEFT)

            for widget in (tab, label):
                widget.bind("<Button-1>", lambda e, p=path: self.activate_document(p))
            close.bind("<Button-1>", lambda e, p=path: self.close_document(p))

    def close_document(self, path):
        if path not in self.documents:
            return

        doc = self.documents[path]
        if doc["dirty"]:
            answer = messagebox.askyesnocancel(
                "文件尚未保存",
                f"是否保存对以下文件的修改？\n\n{path}",
                parent=self.root
            )
            if answer is None:
                return
            if answer and not self.save_document(path):
                return

        was_active = path == self.active_path
        self.remove_document_without_prompt(path)

        if was_active:
            self.activate_first_document()
        self.refresh_tabs()

    def remove_document_without_prompt(self, path):
        doc = self.documents.pop(path, None)
        if not doc:
            return

        timer = doc.get("save_timer")
        if timer:
            try:
                self.root.after_cancel(timer)
            except tk.TclError:
                pass

        widget = doc["widget"]
        self.widget_to_path.pop(widget, None)
        if widget == self.editor:
            widget.pack_forget()
            self.editor = None
        widget.destroy()

        if self.active_path == path:
            self.active_path = None

    def close_all_documents_with_prompt(self):
        for path in list(self.documents.keys()):
            doc = self.documents[path]
            if not doc["dirty"]:
                continue

            answer = messagebox.askyesnocancel(
                "文件尚未保存",
                f"是否保存对以下文件的修改？\n\n{path}",
                parent=self.root
            )
            if answer is None:
                return False
            if answer and not self.save_document(path):
                return False

        for path in list(self.documents.keys()):
            self.remove_document_without_prompt(path)

        self.active_path = None
        self.editor = None
        self.activate_first_document()
        self.refresh_tabs()
        return True

    # =========================================================
    # 字数统计
    # =========================================================

    def count_words(self, content):
        count = 0
        for char in content:
            if char.isspace():
                continue
            category = unicodedata.category(char)
            if category.startswith("P"):
                continue
            if category.startswith("C"):
                continue
            count += 1
        return count

    def update_word_count(self):
        if self.editor is None:
            self.word_label.config(text="当前字数：0")
            return

        content = self.editor.get("1.0", "end-1c")
        count = self.count_words(content)
        self.word_label.config(text=f"当前字数：{count}")

    def update_paragraph_stats(self):
        self.stats_canvas.delete("all")
        if self.editor is None:
            return

        total_lines = int(self.editor.index("end-1c").split(".")[0])
        paragraph_number = 0

        for line in range(1, total_lines + 1):
            start = f"{line}.0"
            end = f"{line}.0 lineend"
            content = self.editor.get(start, end)

            if not content.strip():
                continue

            paragraph_number += 1
            count = self.count_words(content)

            if count > 50:
                count_color = "#e74c3c"
            elif count > 40:
                count_color = "#e6a23c"
            else:
                count_color = "#666666"

            info = self.editor.dlineinfo(start)
            if info is None:
                continue

            x, y, width, height, baseline = info
            text_y = y + baseline

            self.stats_canvas.create_text(
                15,
                text_y,
                text=str(paragraph_number),
                anchor="w",
                font=("Microsoft YaHei", 9),
                fill="#999999"
            )
            self.stats_canvas.create_text(
                105,
                text_y,
                text=str(count),
                anchor="e",
                font=("Microsoft YaHei", 10, "bold"),
                fill=count_color
            )

    # =========================================================
    # 文本变化和自动保存
    # =========================================================

    def on_text_changed(self, event=None):
        widget = event.widget if event else self.editor
        if widget is None:
            return

        if widget.edit_modified():
            widget.edit_modified(False)
            path = self.widget_to_path.get(widget)
            if not path or path not in self.documents:
                return

            self.documents[path]["dirty"] = True
            self.refresh_tabs()

            if path == self.active_path:
                self.update_word_count()
                self.schedule_refresh()
                self.save_status.config(text="正在编辑...", fg="#e67e22")

            self.schedule_document_save(path)

    def on_editor_action(self, event=None):
        widget = event.widget if event else self.editor
        if widget is self.editor:
            self.schedule_refresh()
            self.update_word_count()

    def schedule_document_save(self, path):
        if path not in self.documents:
            return

        old_timer = self.documents[path].get("save_timer")
        if old_timer:
            try:
                self.root.after_cancel(old_timer)
            except tk.TclError:
                pass

        self.documents[path]["save_timer"] = self.root.after(
            self.save_delay,
            lambda p=path: self.auto_save_document(p)
        )

    def auto_save_document(self, path):
        if path not in self.documents:
            return
        self.documents[path]["save_timer"] = None
        self.save_document(path)

    def save_document(self, path):
        if path not in self.documents:
            return True

        doc = self.documents[path]
        widget = doc["widget"]
        content = widget.get("1.0", "end-1c")
        temp_path = path + ".tmp"

        try:
            with open(temp_path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, path)
            doc["dirty"] = False

            timer = doc.get("save_timer")
            if timer:
                try:
                    self.root.after_cancel(timer)
                except tk.TclError:
                    pass
                doc["save_timer"] = None

            self.refresh_tabs()
            if path == self.active_path:
                self.save_status.config(text="已自动保存", fg="#27ae60")
            return True

        except Exception as e:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

            if path == self.active_path:
                self.save_status.config(text=f"保存失败：{e}", fg="#e74c3c")
            else:
                messagebox.showerror(
                    "保存失败",
                    f"文件：{path}\n\n{e}",
                    parent=self.root
                )
            return False

    # =========================================================
    # 滚动、行号和刷新
    # =========================================================

    def on_scroll(self, *args):
        if self.editor is not None:
            self.editor.yview(*args)
            self.schedule_refresh()

    def on_editor_scroll(self, widget, first, last):
        if widget is self.editor:
            self.scrollbar.set(first, last)
            self.schedule_refresh()

    def schedule_refresh(self, event=None):
        if self.refresh_timer is None:
            self.refresh_timer = self.root.after_idle(self.update_layout)

    def update_layout(self):
        self.refresh_timer = None
        if self.editor is None or not self.editor.winfo_exists():
            return
        self.update_line_numbers()
        self.update_paragraph_stats()

    def update_line_numbers(self):
        self.gutter.delete("all")
        if self.editor is None:
            return

        total_lines = int(self.editor.index("end-1c").split(".")[0])
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

    # =========================================================
    # 关闭程序
    # =========================================================

    def on_close(self):
        # 先处理所有未保存文件；用户选择取消则不退出
        for path in list(self.documents.keys()):
            doc = self.documents[path]
            if not doc["dirty"]:
                continue

            answer = messagebox.askyesnocancel(
                "文件尚未保存",
                f"是否保存对以下文件的修改？\n\n{path}",
                parent=self.root
            )
            if answer is None:
                return
            if answer and not self.save_document(path):
                return

        for doc in self.documents.values():
            timer = doc.get("save_timer")
            if timer:
                try:
                    self.root.after_cancel(timer)
                except tk.TclError:
                    pass

        if self.refresh_timer:
            try:
                self.root.after_cancel(self.refresh_timer)
            except tk.TclError:
                pass
            self.refresh_timer = None

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WritingTool(root)
    root.mainloop()
