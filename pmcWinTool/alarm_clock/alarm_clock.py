import os
import sys
import tkinter as tk
from datetime import datetime
import threading
import time
import pygame


def resource_path(relative_path):
    """获取资源文件的绝对路径，打包后也能正确访问"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class AlarmClock:
    def __init__(self, root, audio_file=resource_path("res/alarm.mp3")):
        self.root = root
        self.audio_file = audio_file

        self.root.title("PMC 整点闹铃")

        window_width = 200
        window_height = 100

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = screen_width - window_width - 60  # 右边对齐
        y = screen_height // 2 - window_height # 顶部对齐

        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.title_label = tk.Label(
            root,
            text="PMC 整点闹铃 该起来了",
            font=("Consolas", 10),
            fg="cyan",
            bg="black"
        )
        self.title_label.pack(expand=True, fill="x")

        # 时间显示
        self.time_label = tk.Label(
            root,
            text="",
            font=("Consolas", 28),
            fg="cyan",
            bg="black"
        )
        self.time_label.pack(expand=True, fill="both")

        # 测试按钮
        self.test_button = tk.Button(
            root,
            text="测试闹铃",
            command=self.play_alarm,
            bg="gray",
            fg="white"
        )
        self.test_button.pack(fill="x")

        # 避免重复闹铃
        self.last_alarm_hour = None
        self.last_alarm_date = None

        # 初始化 pygame
        pygame.mixer.init()

        self.update_clock()

    # 播放 10 秒闹铃
    def play_alarm(self):
        def play():
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play(-1)  # 循环播放
            time.sleep(10)
            pygame.mixer.music.stop()
        threading.Thread(target=play, daemon=True).start()

    # 判断是否整点响铃
    def check_alarm(self, now):
        hour = now.hour
        minute = now.minute
        second = now.second

        if 9 <= hour <= 21 and minute == 0 and second == 0:
            if self.last_alarm_hour != hour or self.last_alarm_date != now.date():
                self.last_alarm_hour = hour
                self.last_alarm_date = now.date()
                self.play_alarm()

    # 更新时间
    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.check_alarm(now)
        self.root.after(1000, self.update_clock)


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="black")
    app = AlarmClock(root, audio_file=resource_path("res/alarm.mp3"))
    root.mainloop()
