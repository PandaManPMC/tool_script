import tkinter as tk
from tkinter import ttk, messagebox
import pygetwindow as gw
import win32gui
import win32con

def is_window_topmost(hwnd: int) -> bool:
    """判断窗口是否为置顶窗口"""
    exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    return bool(exstyle & win32con.WS_EX_TOPMOST)

def list_windows():
    """获取所有有标题的窗口"""
    windows = []
    for w in gw.getAllWindows():
        visible = getattr(w, "isVisible", None)
        if visible is None:
            visible = getattr(w, "visible", False)
        if w.title and visible:
            windows.append((w.title, w._hWnd))
    return windows

def refresh_list():
    """刷新窗口列表"""
    window_list.delete(*window_list.get_children())
    for i, (title, hwnd) in enumerate(list_windows()):
        topmost = is_window_topmost(hwnd)
        window_list.insert("", "end", iid=i, values=(title, hwnd),
                           tags=("topmost" if topmost else "normal",))
    window_list.tag_configure("topmost", foreground="red")
    window_list.tag_configure("normal", foreground="black")

def set_topmost():
    """置顶选中窗口"""
    selected = window_list.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择一个窗口")
        return
    hwnd = int(window_list.item(selected[0], "values")[1])
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    refresh_list()
    # messagebox.showinfo("成功", "窗口已置顶")

def unset_topmost():
    """取消置顶选中窗口"""
    selected = window_list.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择一个窗口")
        return
    hwnd = int(window_list.item(selected[0], "values")[1])
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    refresh_list()
    # messagebox.showinfo("成功", "已取消置顶")


def keep_self_topmost():
    """周期性让自己回到最顶层"""
    hwnd = win32gui.FindWindow(None, "PMC 窗口置顶工具 for Windows 11")
    if hwnd:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    root.after(2000, keep_self_topmost)  # 每 2 秒执行一次


# --- GUI 界面 ---
root = tk.Tk()
root.title("PMC 窗口置顶工具 for Windows 11")
root.geometry("320x240")
root.resizable(False, False)
root.attributes("-topmost", True)
# keep_self_topmost()  # 定期强制保持最高层

columns = ("title", "hwnd")
window_list = ttk.Treeview(root, columns=columns, show="headings", height=7)  # ✅ 减少行数
window_list.heading("title", text="窗口标题")
window_list.heading("hwnd", text="窗口句柄")
window_list.column("title", width=235)
window_list.column("hwnd", width=80)
window_list.pack(padx=8, pady=5, fill="both", expand=True)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=3)  # ✅ 缩小按钮区间距

tk.Button(btn_frame, text="刷新列表", command=refresh_list, width=15).pack(side="left", padx=4)
tk.Button(btn_frame, text="置顶", command=set_topmost, width=10, bg="#4CAF50", fg="white").pack(side="left", padx=4)
tk.Button(btn_frame, text="取消置顶", command=unset_topmost, width=10, bg="#F44336", fg="white").pack(side="left", padx=4)

refresh_list()
root.mainloop()
