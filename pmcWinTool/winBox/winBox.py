import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import keyboard
from tkinter import messagebox
import gamelib

from pmcWinTool.winBox import auto
from pmcWinTool.winBox import app_const

# 窗口置顶
topmost = False

# 全局UI控制锁
LOCK_GLOBAL_UI = threading.Lock()


def root_click(event):
    # 在点击其他地方时，将焦点移出输入框
    # input_entry.focus_out()
    # num_entry.focus_out()
    # input_hwnd_send_key.focus_out()
    # mu_ye_entry.focus_out()
    # if event.widget != input_entry \
    #         and event.widget != input_entry \
    #         and event.widget != input_hwnd_send_key \
    #         and event.widget != mu_ye_entry \
    #         and event.widget != input_say_time \
    #         and event.widget != input_say_content:  # 只有点击其他地方才失去焦点

    root.focus_set()


def validate_float(value_if_allowed):
    if value_if_allowed == "":
        return True
    try:
        float(value_if_allowed)
        return True
    except ValueError:
        return False


def on_closing():
    gamelib.log3.console("关闭所有线程，确保程序完全退出")
    stop_all_script()
    root.destroy()


# stop_all_script 停止所有脚本
def stop_all_script(event=None):
    gamelib.log3.console("stop_all_script")
    if gamelib.i_mouse.is_run_mouse_left_click:
        mouse_left_click()
    if gamelib.i_mouse.is_run_mouse_right_click:
        mouse_right_click()
    # messagebox.showwarning("提示", "所有脚本已停止")


def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def toggle_topmost():
    global topmost
    topmost = not topmost
    if topmost:
        root.attributes('-topmost', True)
        btn_topmost.config(text="取消置顶")
        gamelib.log3.console("窗口已置顶")
    else:
        root.attributes('-topmost', False)
        btn_topmost.config(text="窗口置顶")
        gamelib.log3.console("取消窗口置顶")


def toggle_collect(event=None):
    with LOCK_GLOBAL_UI:
        print(1)
    #     gamelib.ms_quick.runningCollect = not ms_quick.runningCollect
    #     if gamelib.ms_quick.runningCollect:
    #         btn_collect.config(bg="red")
    #         t = threading.Thread(target=ms_quick.collect, args=(window_name,), daemon=True)
    #         t.start()
    #     else:
    #         btn_collect.config(bg="white")


def mouse_right_click(event=None):
    with LOCK_GLOBAL_UI:
        gamelib.i_mouse.is_run_mouse_right_click = not gamelib.i_mouse.is_run_mouse_right_click
        gamelib.log3.console(f"鼠标右键点击{gamelib.i_mouse.is_run_mouse_right_click}")

    interval = 0.05
    with gamelib.i_mouse.lock_run_mouse_right_click:
        if gamelib.i_mouse.is_run_mouse_right_click:
            btn_mouse_right_click.config(bg="red")
            t = threading.Thread(target=gamelib.i_mouse.while_mouse_right_click, args=(interval,), daemon=True)
            t.start()
        else:
            btn_mouse_right_click.config(bg="white")


def mouse_left_click(event=None):
    with LOCK_GLOBAL_UI:
        gamelib.i_mouse.is_run_mouse_left_click = not gamelib.i_mouse.is_run_mouse_left_click
        gamelib.log3.console(f"鼠标左键点击{gamelib.i_mouse.is_run_mouse_left_click}")
    interval = 0.05
    with gamelib.i_mouse.lock_run_mouse_left_click:
        if gamelib.i_mouse.is_run_mouse_left_click:
            btn_mouse_left_click.config(bg="red")
            t = threading.Thread(target=gamelib.i_mouse.while_mouse_left_click, args=(interval,), daemon=True)
            t.start()
        else:
            btn_mouse_left_click.config(bg="white")


if __name__ == "__main__":

    # 创建 Tkinter GUI
    root = tk.Tk()
    root.title(app_const.APP_NAME)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    root.geometry(f'{app_const.WINDOW_GEOMETRY}+{int(screen_w * 0.75)}+{int(screen_h * 0.2)}')

    root.attributes('-alpha', 0.96)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 创建一个画布和滚动条
    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # 布局滚动条和画布
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # 绑定鼠标滚轮事件
    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    # frame 第一排按钮
    label = tk.Label(scrollable_frame, text=f"严正声明：窗口大小 {app_const.screen_w} * {app_const.screen_h}\n",
                     fg="red", anchor='w', justify='left')
    label.pack(fill='x', pady=1)

    frame = tk.Frame(scrollable_frame)
    frame.pack(pady=10, anchor='w', fill='x')

    btn_topmost = tk.Button(frame, text="窗口置顶", width=10, height=1, command=toggle_topmost)
    btn_topmost.pack(side=tk.LEFT, padx=5)

    btn_mouse_left_click = tk.Button(frame, text="鼠标左键连击(F6)", width=14, height=1, command=mouse_left_click)
    btn_mouse_left_click.pack(side=tk.LEFT, padx=5)

    btn_mouse_right_click = tk.Button(frame, text="鼠标右键连击(F7)", width=14, height=1, command=mouse_right_click)
    btn_mouse_right_click.pack(side=tk.LEFT, padx=5)

    frame2 = tk.Frame(scrollable_frame)
    frame2.pack(pady=20, side=tk.TOP, fill="x", anchor="w")

    # 功能
    fun_frame_q_h = tk.Frame(scrollable_frame)
    fun_frame_q_h.pack(pady=20, side=tk.TOP, fill="x", anchor="w")

    #  label 说明

    label_frame = tk.Frame(scrollable_frame)
    label_frame.pack(pady=10, side=tk.TOP, fill='x', anchor='w')

    label = tk.Label(label_frame, text="停止脚本：快捷键 F12 停止所有脚本，请确保该快捷键未发生冲突。", fg="blue",
                     anchor='w', justify='left')
    label.pack(fill='x', pady=1)

    # 使用 keyboard 绑定全局快捷键
    keyboard.add_hotkey('F12', stop_all_script)
    keyboard.add_hotkey('F7', mouse_right_click)
    keyboard.add_hotkey('F6', mouse_left_click)

    root.bind("<Button-1>", root_click)
    # app.start_release_job()
    root.mainloop()
