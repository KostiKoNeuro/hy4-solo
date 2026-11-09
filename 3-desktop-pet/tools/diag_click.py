import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

import input as inp
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parent.parent
user32 = ctypes.WinDLL("user32", use_last_error=True)


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]

hwnd = int((ROOT / "verify" / "target_hwnd.txt").read_text().strip())
rc = RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rc))
buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(hwnd, buf, 512)
print("target hwnd", hwnd, "visible", bool(user32.IsWindowVisible(hwnd)),
      "rect", [rc.left, rc.top, rc.right, rc.bottom], "title", buf.value)

print("cursor before", inp.pos())
inp.move_to(500, 750)
print("cursor after move_to", inp.pos())

img = ImageGrab.grab()
img.save(ROOT / "verify" / "diag_screen.png")
print("pixel(500,750) =", img.getpixel((500, 750)))
print("pixel(400,900) =", img.getpixel((400, 900)))
print("pixel(720,950) =", img.getpixel((720, 950)))

inp.down()
import time
time.sleep(0.15)
print("left button state while down:", user32.GetAsyncKeyState(0x01) & 0x8000 != 0)
inp.up()
time.sleep(0.4)
log = ROOT / "verify" / "clicks.log"
print("clicks after direct down/up at (500,750):", log.read_text(encoding="utf-8").strip() or "(none)")
