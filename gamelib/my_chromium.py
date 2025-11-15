import time

from playwright.sync_api import sync_playwright


def open_chrome(url: str, username: str, wight=1280, height=720, position_x=0,position_y=0, devtools: bool = False, is_proxy=True):
    if "" == url:
        url = 'https://blog.pandamancoin.com/'
    user_dir = f"user_data/{username}"
    p = sync_playwright().start()

    proxy = None
    if is_proxy:
        proxy = {"server": "http://127.0.0.1:1080"}

    context = p.chromium.launch_persistent_context(
        user_data_dir=user_dir,
        headless=False,     # True headless 渲染
        devtools=devtools,  # 自动弹出调试窗口
        proxy=proxy,
        # args=[
        #     # "--host-resolver-rules=MAP * 8.8.8.8",
        #     # "--disable-web-security",
        #     # "--disable-features=IsolateOrigins,site-per-process",
        #     "--mute-audio",
        #     "--autoplay-policy=no-user-gesture-required",
        #     "--use-fake-ui-for-media-stream",
        #     "--allow-running-insecure-content",
        #     "--disable-blink-features=AutomationControlled",
        #     "--disable-gpu-memory-buffer-video-frames",
        #     "--use-angle=gl",
        #     "--disable-background-timer-throttling",
        #     "--disable-backgrounding-occluded-windows",
        #     "--disable-renderer-backgrounding",
        #     "--disable-renderer-throttling",
        #     #"--window-position=-2000,-2000",  # 放到屏幕外，实现后台运行
        #     f"--window-position={position_x},{position_y}",
        #     f"--window-size={wight},{height}"
        # ]
        args=[
            "--mute-audio",
            "--autoplay-policy=no-user-gesture-required",
            "--use-fake-ui-for-media-stream",
            "--allow-running-insecure-content",
            "--disable-blink-features=AutomationControlled",

            "--enable-gpu-rasterization",
            "--enable-accelerated-video-decode",
            "--ignore-gpu-blocklist",

            "--no-sandbox",
            "--disable-setuid-sandbox",

            f"--window-position={position_x},{position_y}",
            f"--window-size={wight},{height}",

            "--disable-features=UseDnsHttpsSvcb",  # 避免走本地 DNS
            "--no-proxy-server",                   # 不要走系统代理（CFW）
        ]
    )
    page = context.new_page()
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })

    print("Opening:", url)
    page.goto(url)
    # 等待加载
    time.sleep(1)
    return context, page
