

```
pyinstaller --onefile --windowed --name mp3Compress main.py
```

pip install pydub


1. Windows 下安装 ffmpeg

去 ffmpeg 官网下载 或者用 gyan.dev 提供的静态编译版：
👉 https://www.gyan.dev/ffmpeg/builds/

下载 Release full 压缩包（比如 ffmpeg-2025-win64-gpl.zip）。

解压后，把里面的 bin 目录路径（例如 C:\ffmpeg\bin）加入系统 环境变量 PATH。

打开「此电脑 → 属性 → 高级系统设置 → 环境变量」

编辑 Path，添加 C:\ffmpeg\bin

打开命令行，输入：


ffmpeg -version
ffprobe -version



