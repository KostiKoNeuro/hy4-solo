import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_SHIFT = 0x10
KEYEVENTF_KEYUP = 0x0002

user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                               wintypes.DWORD, ctypes.c_size_t]
user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, wintypes.DWORD,
                               ctypes.c_size_t]
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL


def pos():
    p = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def tick():
    user32.mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, 0)


def move_to(x, y):
    user32.SetCursorPos(int(x), int(y))
    tick()


def wake():
    tick()
    user32.keybd_event(VK_SHIFT, 0, 0, 0)
    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)


def down():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)


def up():
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def click(x, y):
    move_to(x, y)
    time.sleep(0.05)
    down()
    time.sleep(0.05)
    up()


def drag(x0, y0, x1, y1, seconds=0.6, steps=28):
    move_to(x0, y0)
    time.sleep(0.08)
    down()
    for i in range(1, steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * (t ** 1.35)
        user32.SetCursorPos(int(x), int(y))
        tick()
        time.sleep(seconds / steps)
    up()


def main():
    cmd = sys.argv[1]
    if cmd == "wake":
        wake()
    elif cmd == "move":
        move_to(float(sys.argv[2]), float(sys.argv[3]))
    elif cmd == "click":
        click(float(sys.argv[2]), float(sys.argv[3]))
    elif cmd == "drag":
        drag(float(sys.argv[2]), float(sys.argv[3]),
             float(sys.argv[4]), float(sys.argv[5]),
             float(sys.argv[6]) if len(sys.argv) > 6 else 0.6)
    elif cmd == "pos":
        print(pos())
    else:
        raise SystemExit("unknown command: " + cmd)


if __name__ == "__main__":
    main()
