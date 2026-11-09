import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab

user32 = ctypes.WinDLL("user32", use_last_error=True)

WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
GWL_EXSTYLE = -20

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long

found = []


def cb(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    cls = ctypes.create_unicode_buffer(256)
    txt = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(hwnd, cls, 256)
    user32.GetWindowTextW(hwnd, txt, 512)
    if "Qt6" in cls.value and txt.value == "Окто":
        found.append((int(hwnd), cls.value, txt.value))
    return True


user32.EnumWindows(EnumWindowsProc(cb), 0)
print("pet windows found:", len(found))
if not found:
    print("RESULT: FAIL (no pet window)")
    sys.exit(1)

hwnd = found[0][0]
rc = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rc))
ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
print("hwnd:", hwnd, "rect:", [rc.left, rc.top, rc.right, rc.bottom], "EXSTYLE: 0x%08X" % ex)
topmost = bool(ex & WS_EX_TOPMOST)
noactivate = bool(ex & WS_EX_NOACTIVATE)

img = ImageGrab.grab().convert("RGB")
w, h = rc.right - rc.left, rc.bottom - rc.top
crop = np.array(img.crop((rc.left, rc.top, rc.right, rc.bottom)))
r = crop[:, :, 0].astype(np.int16)
g = crop[:, :, 1].astype(np.int16)
b = crop[:, :, 2].astype(np.int16)
lavender = (b > r + 14) & (b > g + 24) & (r > 85) & (b > 145)
ink = int(lavender.sum())
print("pet-body pixels inside window:", ink)
print("RESULT:", "PASS" if (topmost and noactivate and ink > 3000 and w == 240 and h == 240) else "FAIL",
      f"(topmost={topmost} noactivate={noactivate} size={w}x{h})")
