import ctypes
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import input as inp

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "Oktopet" / "status.json"
CMD = ROOT / "Oktopet" / "debug.cmd"

user32 = ctypes.WinDLL("user32", use_last_error=True)
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
GWL_EXSTYLE = -20


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.WindowFromPoint.argtypes = [POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
GA_ROOT = 2


def describe(hwnd):
    if not hwnd:
        return "NULL"
    cls = ctypes.create_unicode_buffer(256)
    txt = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(hwnd, cls, 256)
    user32.GetWindowTextW(hwnd, txt, 512)
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return f"hwnd={int(hwnd)} root={int(root) if root else 0} class={cls.value!r} title={txt.value!r}"


def at(x, y):
    p = POINT(int(x), int(y))
    return user32.WindowFromPoint(p)


def main():
    results = []
    CMD.write_text("pos:600,808\n", encoding="utf-8")
    time.sleep(0.5)
    hwnd = json.loads(STATUS.read_text(encoding="utf-8"))["hwnd"]
    ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
    print("pet hwnd:", hwnd)
    print("EXSTYLE: 0x%08X" % ex)
    for label, bit in [("NOACTIVATE", WS_EX_NOACTIVATE), ("TOPMOST", WS_EX_TOPMOST),
                       ("TOOLWINDOW", WS_EX_TOOLWINDOW)]:
        ok = bool(ex & bit)
        results.append(ok)
        print(("PASS  " if ok else "FAIL  ") + label + " always set")

    inp.wake()
    inp.move_to(603, 811)
    time.sleep(0.35)
    ex1 = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
    w1 = at(603, 811)
    ok1 = bool(ex1 & WS_EX_TRANSPARENT) and (int(w1 or 0) != hwnd)
    results.append(ok1)
    print(("PASS  " if ok1 else "FAIL  ") +
          f"transparent-pixel hover -> click-through (transparent bit set, WindowFromPoint={describe(w1)})")

    inp.move_to(720, 950)
    time.sleep(0.35)
    ex2 = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
    w2 = at(720, 950)
    ok2 = not (ex2 & WS_EX_TRANSPARENT)
    results.append(ok2)
    print(("PASS  " if ok2 else "FAIL  ") +
          f"opaque-pixel hover -> interactive (transparent bit clear, WindowFromPoint={describe(w2)})")
    print("EXSTYLE away=0x%08X  over=0x%08X" % (ex1, ex2))
    print("RESULT:", sum(results), "/", len(results))


if __name__ == "__main__":
    main()
