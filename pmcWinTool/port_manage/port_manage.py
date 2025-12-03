import tkinter as tk
from tkinter import messagebox, scrolledtext
import psutil
import subprocess

WINDOW_WIDTH = 480
WINDOW_HEIGHT = 320

def query_port():
    port = entry_port.get().strip()
    if not port.isdigit():
        messagebox.showerror("错误", "请输入正确的端口号")
        return

    output_box.delete(1.0, tk.END)
    results = []

    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == int(port):
            pid = conn.pid
            if pid:
                try:
                    p = psutil.Process(pid)
                    info = (
                        f"端口: {port}\nPID: {pid}\n进程名: {p.name()}\n路径: {p.exe()}\n"
                        f"命令行: {p.cmdline()}\n用户: {p.username()}\n状态: {p.status()}\n------\n"
                    )
                except psutil.AccessDenied:
                    info = f"端口: {port}\nPID: {pid}\n进程名: 无法访问（权限不足）\n------\n"
            else:
                info = f"端口: {port}\nPID: 无\n------\n"
            results.append((pid, info))
            output_box.insert(tk.END, info)

    global found_pid
    found_pid = results[0][0] if results else None

    if not results:
        messagebox.showinfo("提示", f"端口 {port} 未被占用或无法获取信息")


def kill_process():
    if not found_pid:
        messagebox.showwarning("提示", "没有可结束的进程")
        return

    try:
        subprocess.run(["taskkill", "/F", "/PID", str(found_pid)], capture_output=True, text=True)
        messagebox.showinfo("完成", f"已结束 PID {found_pid}")
        output_box.insert(tk.END, f"\n✔ 成功释放进程 PID {found_pid}\n")
    except Exception as e:
        messagebox.showerror("错误", f"无法结束进程:\n{e}")


# ---------------- GUI ----------------
root = tk.Tk()
root.title("PMC 端口占用查询工具")
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

# === 输入框 + 查询按钮在同一行 ===
frame_top = tk.Frame(root)
frame_top.pack(pady=8)

tk.Label(frame_top, text="端口号:", font=("Microsoft YaHei", 11)).pack(side=tk.LEFT, padx=3)

entry_port = tk.Entry(frame_top, width=10, font=("Microsoft YaHei", 11))
entry_port.pack(side=tk.LEFT, padx=3)

btn_query = tk.Button(frame_top, text="查询", command=query_port, width=8, font=("Microsoft YaHei", 10))
btn_query.pack(side=tk.LEFT, padx=5)

btn_kill = tk.Button(root, text="结束进程释放端口", command=kill_process, width=22, font=("Microsoft YaHei", 10))
btn_kill.pack(pady=4)

output_box = scrolledtext.ScrolledText(root, width=58, height=12, font=("Consolas", 9))
output_box.pack(pady=5)

found_pid = None
root.mainloop()
