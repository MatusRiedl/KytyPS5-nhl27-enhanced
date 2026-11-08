"""Open the Faceoff window."""
import os
import sys

from . import __version__, home
from .api import Api

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
WIDTH, HEIGHT, MIN_SIZE = 1200, 820, (1000, 700)
TITLE_BAR = 0x140C07          # #070c14 as Windows writes it (blue, green, red)
WEBVIEW2_DOWNLOAD = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"


def message(title, text):
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    else:
        print(f"{title}\n{text}")


def webview2_installed():
    if os.name != "nt":
        return True
    import winreg
    client = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for root, key in ((winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\" + client),
                      (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\" + client), (winreg.HKEY_CURRENT_USER, "SOFTWARE\\" + client)):
        try:
            with winreg.OpenKey(root, key) as k:
                found, _ = winreg.QueryValueEx(k, "pv")
                if found and found != "0.0.0.0":
                    return True
        except OSError:
            continue
    return False


def dark_title_bar(window):
    """Windows: a dark title bar in the app's colour (Windows 10 takes the dark mode only)."""
    if os.name != "nt":
        return
    try:
        import ctypes
        hwnd = window.native.Handle.ToInt64()
        dwm = ctypes.windll.dwmapi
        on = ctypes.c_int(1)
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(on), ctypes.sizeof(on))
        colour = ctypes.c_int(TITLE_BAR)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(colour), ctypes.sizeof(colour))
    except Exception:
        pass


def window_box(webview):
    """(width, height, x, y): the default size, shrunk to the main screen's free area (no taskbar), centred."""
    try:
        screens = list(webview.screens)
        screen = next((sc for sc in screens if sc.x == 0 and sc.y == 0), screens[0])
        frame = getattr(screen, "frame", None)
        if frame is not None:
            ax, ay, aw, ah = int(frame.X), int(frame.Y), int(frame.Width), int(frame.Height)
        else:
            ax, ay, aw, ah = int(screen.x), int(screen.y), int(screen.width), int(screen.height) - 80
        w = max(min(WIDTH, aw - 40), MIN_SIZE[0])
        h = max(min(HEIGHT, ah - 40), MIN_SIZE[1])
        return w, h, ax + max(0, (aw - w) // 2), ay + max(0, (ah - h) // 2)
    except Exception:
        return WIDTH, HEIGHT, None, None


def smoke(window, out):
    """FACEOFF_SMOKE=<folder>: once the page has drawn, save page facts (smoke.json) and window pictures
    (play.png, multi.png), then close."""
    import json
    import time
    window.events.loaded.wait(60)
    time.sleep(4)
    os.makedirs(out, exist_ok=True)
    facts = window.evaluate_js(
        "JSON.stringify({title: document.querySelector('#title').textContent,"
        " status: document.querySelector('#status').textContent.trim(),"
        " play: !document.querySelector('#play').disabled, label: document.querySelector('#playlabel').textContent,"
        " cache: document.querySelector('#cachesize').textContent + ' ' + document.querySelector('#cachetag').textContent,"
        " saves: document.querySelector('#savelist').textContent,"
        " seg: [...document.querySelectorAll('.seg button.on')].map(b => b.textContent),"
        " art: document.querySelector('#art').classList.contains('on')})")
    with open(os.path.join(out, "smoke.json"), "w", encoding="utf-8") as f:
        f.write(facts or "null")
    try:
        from PIL import ImageGrab
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(window.native.Handle.ToInt64(), ctypes.byref(rect))
        box = (rect.left, rect.top, rect.right, rect.bottom)
        ImageGrab.grab(box, all_screens=True).save(os.path.join(out, "play.png"))
        window.evaluate_js("document.querySelector('[data-tab=multi]').click()")
        time.sleep(1.5)
        ImageGrab.grab(box, all_screens=True).save(os.path.join(out, "multi.png"))
    except Exception as e:
        with open(os.path.join(out, "smoke_error.txt"), "w") as f:
            f.write(repr(e))
    window.destroy()


def main():
    if not webview2_installed():
        message("Faceoff", "Faceoff needs Microsoft's WebView2 Runtime, which this PC does not have.\n\n"
                           f"Install it from {WEBVIEW2_DOWNLOAD} and start Faceoff again.")
        return 1
    import webview

    api = Api(home())
    w, h, x, y = window_box(webview)
    window = webview.create_window(f"Faceoff {__version__}", os.path.join(WEB, "index.html"), js_api=api,
                                   width=w, height=h, x=x, y=y, min_size=MIN_SIZE, background_color="#070c14")
    api._window = window
    window.events.shown += lambda: dark_title_bar(window)
    smoke_out = os.environ.get("FACEOFF_SMOKE")      # build check: write what the page shows + a picture, then close
    webview.start(func=(lambda: smoke(window, smoke_out)) if smoke_out else None,
                  debug=bool(os.environ.get("FACEOFF_DEBUG")), private_mode=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
