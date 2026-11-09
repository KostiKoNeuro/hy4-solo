import ctypes
import json
import math
import random
import re
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPainterPath,
    QPen, QPixmap, QTransform, QGuiApplication,
)
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon, QWidget

HERE = Path(__file__).resolve().parent
SPRITES = HERE / "sprites"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TRANSPARENT = 0x00000020
WM_NCHITTEST = 0x0084
SPI_GETWORKAREA = 0x0030
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
VK_LBUTTON = 0x01
HWND_TOPMOST = ctypes.c_void_p(-1)


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetLastInputInfo.restype = wintypes.BOOL
kernel32.GetTickCount.restype = wintypes.DWORD
user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT,
                                         ctypes.c_void_p, wintypes.UINT]
user32.SystemParametersInfoW.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL


def work_area():
    rc = RECT()
    user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rc), 0)
    return rc


def idle_seconds():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    delta = (kernel32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF
    return delta / 1000.0


def cursor_pos():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


SPRITE_NAMES = [
    "idle", "blink", "walk1", "walk2", "sleep", "yawn", "grab", "toss",
    "land", "eat", "react_link", "react_number", "react_code", "react_text",
]
WALK_FRAMES = ("walk1", "walk2")

BUBBLES = {
    "grab": ["Ой! Куда мы?", "Восемь рук, а удержаться не за что!"],
    "toss": ["А-а-а! Летим!", "Ещё раз! Ещё р-раз!"],
    "land": ["Приземлился. Кажется, я стал блином.", "Нормально. Я упругий."],
    "eat": ["Ммм, байты! Моя любимая диета.", "Вкусно. Ещё?"],
    "yawn": ["А? Я не спал!.. Ладно, спал.", "Просыпаюсь. Где мои восемь рук?"],
    "react_link": ["Ссылка! Уже держу двумя щупальцами.", "О, гиперссылка! Восемь рук — восемь вкладок!"],
    "react_number": ["Число? Считаю на щупальцах… восемь! Опять восемь!",
                     "Складываю, вычитаю… получилось восемь. Совпадение?"],
    "react_code": ["Код! Параллелю на восемь потоков.", "Вижу точку с запятой. Она лишняя. Наверное."],
    "react_text": ["Простыня! Обнимаю всеми руками… не помещается.",
                   "Столько букв. Я их уже перепутал."],
    "misc": ["Что-то скопировал. Я заметил. Я всегда замечаю."],
    "sleep": ["…"],
}

LINK_RE = re.compile(r"^\s*(https?://|www\.|ftp://)\S+", re.I)
NUMBER_RE = re.compile(r"^\s*[+-]?\d[\d\s.,:_/-]*\s*$")
CODE_RE = re.compile(
    r"(def\s+\w+|function\s*\(|=>|\bimport\s|\bfrom\s+\w+\s+import|#include|"
    r"\bclass\s+\w+|console\.log|print\s*\(|SELECT\s+.+\s+FROM|<\/?[A-Za-z][^>]*>|"
    r"\breturn\b|\{\s*$|\}\s*$)",
    re.I | re.M,
)


def classify_clip(text):
    t = text.strip()
    if not t:
        return None
    if LINK_RE.match(t) and "\n" not in t:
        return "link"
    if CODE_RE.search(t) and len(t) > 12:
        return "code"
    if NUMBER_RE.match(t) and len(t) <= 40:
        return "number"
    if len(t) > 220 or t.count("\n") >= 3:
        return "text"
    return "misc"


class Oktopet(QWidget):
    def __init__(self, debug=False, sleep_after=60.0):
        super().__init__()
        self.debug = debug
        self.sleep_after = float(sleep_after)
        self.canvasi = 240
        self.ground = 222
        self.center_x = 120
        atlas = SPRITES / "atlas.json"
        if atlas.is_file():
            cfg = json.loads(atlas.read_text(encoding="utf-8"))
            self.canvasi = int(cfg.get("canvas", self.canvasi))
            self.ground = int(cfg.get("ground", self.ground))
            self.center_x = int(cfg.get("center_x", self.center_x))

        self.pixmaps = {}
        self.images = {}
        for name in SPRITE_NAMES:
            path = SPRITES / (name + ".png")
            pm = QPixmap(str(path))
            if pm.isNull():
                raise RuntimeError("missing sprite: " + str(path))
            self.pixmaps[name] = pm
            self.images[name] = pm.toImage()
        self.mirrored = {}
        mirror_transform = QTransform()
        mirror_transform.scale(-1, 1)
        for name in SPRITE_NAMES:
            self.mirrored[name] = self.pixmaps[name].transformed(mirror_transform)

        rc = work_area()
        self.area = (rc.left, rc.top, rc.right, rc.bottom)
        self.ground_screen_y = rc.bottom - 2
        self.x = float(rc.left + 140)
        self.y = float(self.ground_screen_y - self.ground)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.mode = "walk"
        self.sprite = "walk1"
        self.flip = False
        self.sleeping = False
        self.forced_sleep = False
        self.dragging = False
        self.prev_left_down = False
        self.grab_dx = 0
        self.grab_dy = 0
        self.samples = []
        self.state_until = 0.0
        self.anim_time = 0.0
        self.walk_phase = 0.0
        self.pause_until = 0.0
        self.next_blink = time.monotonic() + random.uniform(2.0, 5.0)
        self.blink_until = 0.0
        self.bubble_text = ""
        self.bubble_alpha = 0.0
        self.bubble_until = 0.0
        self._about = None
        self.particles = []
        try:
            self.last_clip = QGuiApplication.clipboard().text()
        except Exception:
            self.last_clip = ""
        self.last_clip_kind = ""
        self.last_react_at = 0.0
        self.last_tick = time.monotonic()
        self.launch_time = self.last_tick
        self.tick_count = 0
        self.click_through = None
        self.hwnd = 0
        self.left_down_state = False
        self.status_path = HERE / "status.json"
        self.cmd_path = HERE / "debug.cmd"
        self.fps = 0.0
        self.menu_items = []

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(self.canvasi, self.canvasi)
        self.setWindowTitle("Окто")
        self.setMouseTracking(True)
        self.move(int(self.x), int(self.y))

        self.set_bubble(random.choice(BUBBLES["misc"]), 2.6)
        self.build_tray()

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def build_tray(self):
        self.tray = QSystemTrayIcon(QIcon(str(SPRITES / "tray.ico")), self)
        self.tray.setToolTip("Окто — настольный осьминог")
        menu = QMenu()
        title = menu.addAction("Окто · настольный осьминог")
        title.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Покормить", self.feed)
        menu.addAction("Уложить спать", self.put_to_sleep)
        menu.addSeparator()
        menu.addAction("О программе…", self.show_about)
        menu.addSeparator()
        menu.addAction("Выход", self.quit_app)
        self.menu_items = [a.text() for a in menu.actions()]
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def showEvent(self, event):
        super().showEvent(event)
        self.hwnd = int(self.winId())
        ex = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        ex |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex)
        self.assert_topmost()

    def assert_topmost(self):
        if self.hwnd:
            user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def set_click_through(self, transparent):
        if transparent == self.click_through or not self.hwnd:
            return
        self.click_through = transparent
        ex = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        if transparent:
            ex |= WS_EX_TRANSPARENT
        else:
            ex &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex)

    def sprite_alpha(self, gx, gy, name, flip):
        lx = int(gx - self.x)
        ly = int(gy - self.y)
        if lx < 0 or ly < 0 or lx >= self.canvasi or ly >= self.canvasi:
            return 0
        if flip:
            lx = self.canvasi - 1 - lx
        return self.images[name].pixelColor(lx, ly).alpha()

    def set_bubble(self, text, duration=3.0):
        self.bubble_text = text
        self.bubble_alpha = 1.0
        self.bubble_until = time.monotonic() + duration

    def react(self, kind):
        now = time.monotonic()
        if now - self.last_react_at < 0.7:
            return
        self.last_react_at = now
        self.last_clip_kind = kind
        self.sleeping = False
        self.forced_sleep = False
        self.mode = "react"
        self.state_until = now + 3.3
        bubble_key = "react_" + kind if kind in ("link", "number", "code", "text") else "misc"
        self.set_bubble(random.choice(BUBBLES[bubble_key]), 3.2)

    def feed(self):
        now = time.monotonic()
        self.sleeping = False
        self.forced_sleep = False
        self.mode = "eat"
        self.state_until = now + 2.6
        self.set_bubble(random.choice(BUBBLES["eat"]), 2.5)
        for _ in range(9):
            self.particles.append({
                "x": self.center_x + random.uniform(-48, 48),
                "y": self.ground - random.uniform(45, 90),
                "vx": random.uniform(-22, 22),
                "vy": random.uniform(-70, -35),
                "life": 1.0,
                "r": random.uniform(3, 6),
            })

    def put_to_sleep(self):
        self.forced_sleep = True
        self.sleeping = True
        self.mode = "sleep"
        self.set_bubble("Сплю. Не буди… ладно, буди.", 2.4)

    def wake(self):
        now = time.monotonic()
        self.forced_sleep = False
        self.sleeping = False
        self.mode = "yawn"
        self.state_until = now + 1.7
        self.set_bubble(random.choice(BUBBLES["yawn"]), 1.9)

    def toss(self, vx=340.0, vy=-760.0):
        now = time.monotonic()
        self.sleeping = False
        self.forced_sleep = False
        self.dragging = False
        self.mode = "air"
        self.vx, self.vy = vx, vy
        self.set_bubble(random.choice(BUBBLES["toss"]), 1.6)

    def show_about(self):
        box = QMessageBox()
        box.setWindowTitle("О программе")
        box.setText(
            "Окто — настольный осьминог\n\n"
            "Маленький осьминог живёт прямо на вашей панели задач: гуляет, "
            "подбрасывается, засыпает, когда вы отходите, и комментирует всё, "
            "что вы копируете. Восемь щупалец — восемь дел одновременно.\n\n"
            "Ни активации окна, ни фокуса, ни интернета. Только удовольствие."
        )
        box.setWindowFlags(box.windowFlags() | Qt.WindowStaysOnTopHint)
        self._about = box
        box.show()

    def quit_app(self):
        self.tray.hide()
        if self.debug and self.status_path.is_file():
            self.status_path.unlink()
        QApplication.quit()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.sleeping:
                self.wake()
            else:
                self.put_to_sleep()
        elif reason == QSystemTrayIcon.Trigger:
            self.set_bubble("Привет! Я тут, на панели задач.", 2.6)

    def check_clipboard(self):
        try:
            text = QGuiApplication.clipboard().text()
        except Exception:
            return
        if not text or text == self.last_clip:
            return
        self.last_clip = text
        kind = classify_clip(text)
        if kind:
            self.react(kind)

    def process_debug_commands(self):
        if not self.debug or not self.cmd_path.is_file():
            return
        try:
            lines = self.cmd_path.read_text(encoding="utf-8").splitlines()
            self.cmd_path.unlink()
        except Exception:
            return
        for raw in lines:
            cmd = raw.strip()
            if not cmd:
                continue
            if cmd == "feed":
                self.feed()
            elif cmd == "sleep":
                self.put_to_sleep()
            elif cmd == "wake":
                self.wake()
            elif cmd == "toss":
                self.toss()
            elif cmd == "exit":
                self.quit_app()
            elif cmd.startswith("react:"):
                self.react(cmd.split(":", 1)[1].strip())
            elif cmd == "hide":
                self.hide()
            elif cmd == "show":
                self.show()
            elif cmd == "freeze":
                self.pause_until = time.monotonic() + 3600.0
            elif cmd == "unfreeze":
                self.pause_until = 0.0
            elif cmd.startswith("pos:"):
                try:
                    sx, sy = cmd[4:].split(",")
                    self.x, self.y = float(sx), float(sy)
                    self.vx = self.vy = 0.0
                    self.mode = "walk"
                    self.sleeping = False
                    self.forced_sleep = False
                    self.dragging = False
                    self.pause_until = time.monotonic() + 3600.0
                except ValueError:
                    pass
            elif cmd == "menu":
                self.tray.contextMenu().popup(QPointF(self.x + 40, self.y - 10).toPoint())

    def write_status(self):
        if not self.debug:
            return
        data = {
            "mode": self.mode,
            "sprite": self.sprite,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "vx": round(self.vx, 1),
            "vy": round(self.vy, 1),
            "sleeping": self.sleeping,
            "forced_sleep": self.forced_sleep,
            "idle_sec": round(min(idle_seconds(), time.monotonic() - self.launch_time), 2),
            "raw_idle_sec": round(idle_seconds(), 2),
            "sleep_after": self.sleep_after,
            "bubble": self.bubble_text,
            "last_clip_kind": self.last_clip_kind,
            "click_through": bool(self.click_through),
            "dragging": self.dragging,
            "tray_available": QSystemTrayIcon.isSystemTrayAvailable(),
            "tray_visible": self.tray.isVisible(),
            "menu_visible": self.tray.contextMenu().isVisible(),
            "menu_items": self.menu_items,
            "fps": round(self.fps, 1),
            "hwnd": self.hwnd,
        }
        try:
            self.status_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def tick(self):
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self.last_tick))
        self.last_tick = now
        self.anim_time += dt
        self.tick_count += 1
        self.fps = 0.9 * self.fps + 0.1 * (1.0 / max(dt, 1e-4))

        self.process_debug_commands()
        raw_idle = idle_seconds()
        idle = min(raw_idle, now - self.launch_time)

        if self.forced_sleep or idle >= self.sleep_after:
            if not self.sleeping:
                self.sleeping = True
                self.mode = "sleep"
                self.dragging = False
                self.set_bubble("…", 2.0)
        elif self.sleeping:
            self.wake()

        cx, cy = cursor_pos()
        left_down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        self.left_down_state = left_down

        if not self.dragging:
            over = self.sprite_alpha(cx, cy, self.sprite, self.flip) > 40
            if left_down and not self.prev_left_down and over:
                if self.sleeping:
                    self.forced_sleep = False
                    self.wake()
                else:
                    self.dragging = True
                    self.grab_dx = cx - self.x
                    self.grab_dy = cy - self.y
                    self.samples = [(now, cx, cy)]
                    self.mode = "drag"
                    self.set_bubble(random.choice(BUBBLES["grab"]), 1.4)
        if self.dragging:
            self.x = cx - self.grab_dx
            self.y = cy - self.grab_dy
            self.samples.append((now, cx, cy))
            self.samples = [s for s in self.samples if now - s[0] < 0.11]
            if self.prev_left_down and not left_down:
                self.release_drag(now)
        self.prev_left_down = left_down

        should_pass = not (self.sprite_alpha(cx, cy, self.sprite, self.flip) > 40 or self.dragging)
        self.set_click_through(should_pass)

        if self.sleeping:
            self.mode = "sleep"
            self.y += (self.ground_screen_y - self.ground - self.y) * min(1.0, dt * 8)
            self.x = max(self.area[0], min(self.area[2] - self.canvasi, self.x))
        elif self.dragging:
            self.mode = "drag"
        elif self.mode == "air":
            self.integrate_air(dt, now)
        elif self.mode in ("react", "eat", "land", "yawn"):
            target_y = self.ground_screen_y - self.ground
            self.y += (target_y - self.y) * min(1.0, dt * 8)
            if now >= self.state_until:
                self.mode = "walk"
                self.vx = self.vy = 0.0
        else:
            self.walk(dt, now)

        self.choose_sprite(now)
        self.update_bubble(dt, now)
        self.update_particles(dt)
        if self.tick_count % 10 == 0:
            self.check_clipboard()
        if self.tick_count % 120 == 0:
            self.assert_topmost()
        if self.tick_count % 12 == 0:
            self.write_status()
        self.move(int(self.x), int(self.y))
        self.update()

    def release_drag(self, now):
        self.dragging = False
        recent = [s for s in self.samples if now - s[0] <= 0.09]
        vx = vy = 0.0
        if len(recent) >= 2:
            span = recent[-1][0] - recent[0][0]
            if span > 1e-4:
                vx = (recent[-1][1] - recent[0][1]) / span
                vy = (recent[-1][2] - recent[0][2]) / span
        vx = max(-1700.0, min(1700.0, vx))
        vy = max(-1700.0, min(1700.0, vy))
        if abs(vx) < 60 and abs(vy) < 60:
            vy = -230.0
        self.mode = "air"
        self.vx, self.vy = vx, vy
        self.set_bubble(random.choice(BUBBLES["toss"]), 1.6)

    def integrate_air(self, dt, now):
        self.vy += 2100.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        left, top, right, bottom = self.area
        if self.x < left:
            self.x = left
            self.vx = abs(self.vx) * 0.55
        if self.x + self.canvasi > right:
            self.x = right - self.canvasi
            self.vx = -abs(self.vx) * 0.55
        if self.y < top - 40:
            self.y = top - 40
            self.vy = abs(self.vy) * 0.5
        feet = self.y + self.ground
        if feet >= self.ground_screen_y:
            self.y = self.ground_screen_y - self.ground
            if self.vy > 260:
                self.mode = "land"
                self.state_until = now + 0.95
                self.set_bubble(random.choice(BUBBLES["land"]), 1.5)
                self.vy = -self.vy * 0.28
                self.vx *= 0.62
            elif abs(self.vx) < 45:
                self.vx = self.vy = 0.0
                self.mode = "walk"
            else:
                self.vy = -abs(self.vy) * 0.35
                self.vx *= 0.78

    def walk(self, dt, now):
        self.y += (self.ground_screen_y - self.ground - self.y) * min(1.0, dt * 10)
        if now < self.pause_until:
            return
        self.walk_phase += dt
        self.x += self.facing * 44.0 * dt
        left, _, right, _ = self.area
        if self.x <= left:
            self.x = left
            self.facing = 1
        if self.x + self.canvasi >= right:
            self.x = right - self.canvasi
            self.facing = -1
        if random.random() < dt * 0.12:
            self.pause_until = now + random.uniform(1.2, 3.0)

    def choose_sprite(self, now):
        mode = self.mode
        if mode == "sleep":
            self.sprite, self.flip = "sleep", False
        elif mode == "drag":
            self.sprite, self.flip = "grab", False
        elif mode == "air":
            self.sprite, self.flip = "toss", False
        elif mode == "land":
            self.sprite, self.flip = "land", False
        elif mode == "eat":
            self.sprite, self.flip = "eat", False
        elif mode == "yawn":
            self.sprite, self.flip = "yawn", False
        elif mode == "react":
            key = {"link": "react_link", "number": "react_number",
                   "code": "react_code", "text": "react_text",
                   "misc": "idle"}.get(self.last_clip_kind, "idle")
            self.sprite, self.flip = key, False
        else:
            self.flip = self.facing < 0
            if now >= self.next_blink:
                self.blink_until = now + 0.16
                self.next_blink = now + random.uniform(2.4, 6.0)
            if now < self.blink_until or now < self.pause_until:
                self.sprite = "blink" if now < self.blink_until else "idle"
            else:
                self.sprite = WALK_FRAMES[int(self.walk_phase * 6.0) % 2]

    def update_bubble(self, dt, now):
        if now > self.bubble_until:
            self.bubble_alpha = max(0.0, self.bubble_alpha - dt * 2.4)
        else:
            self.bubble_alpha = min(1.0, self.bubble_alpha + dt * 6)
        if self.bubble_alpha <= 0:
            self.bubble_text = ""

    def update_particles(self, dt):
        for part in self.particles:
            part["x"] += part["vx"] * dt
            part["y"] += part["vy"] * dt
            part["vy"] += 40 * dt
            part["life"] -= dt * 0.75
        self.particles = [p for p in self.particles if p["life"] > 0]

    def current_pixmap(self):
        return self.mirrored[self.sprite] if self.flip else self.pixmaps[self.sprite]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if self.mode not in ("air", "drag"):
            p.setBrush(QColor(35, 20, 60, 42))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(self.center_x - 52, self.ground - 6, 104, 13))

        self.draw_bubble(p)
        self.draw_particles(p)

        pix = self.current_pixmap()
        bob = 0.0
        if self.mode == "walk":
            bob = -abs(math.sin(self.walk_phase * 12.0)) * 2.0
        p.save()
        if self.mode == "air":
            angle = max(-30.0, min(30.0, self.vx * 0.022))
            cx, cy = self.center_x, self.ground - 70
            p.translate(cx, cy)
            p.rotate(angle)
            p.translate(-cx, -cy)
        p.drawPixmap(0, int(bob), pix)
        p.restore()

        if self.sleeping:
            self.draw_zzz(p)

    def draw_bubble(self, p):
        if not self.bubble_text or self.bubble_alpha <= 0:
            return
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        fm = QFontMetrics(font)
        max_w = self.canvasi - 44
        words = self.bubble_text.split()
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if fm.horizontalAdvance(trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        line_h = fm.height() + 2
        h = 16 + line_h * len(lines) + 10
        rect = QRectF(12, 4, self.canvasi - 24, h)
        p.save()
        p.setOpacity(self.bubble_alpha)
        shadow = QRectF(rect.adjusted(2, 3, 2, 3))
        path = QPainterPath()
        path.addRoundedRect(QRectF(shadow), 12, 12)
        p.fillPath(path, QColor(30, 20, 55, 55))
        tail = QPainterPath()
        tail.moveTo(self.center_x - 9, rect.bottom() - 1)
        tail.lineTo(self.center_x + 9, rect.bottom() - 1)
        tail.lineTo(self.center_x, rect.bottom() + 10)
        tail.closeSubpath()
        p.fillPath(tail, QColor(255, 255, 255, 240))
        round_path = QPainterPath()
        round_path.addRoundedRect(QRectF(rect), 12, 12)
        p.fillPath(round_path, QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(126, 104, 196), 2))
        p.drawPath(round_path)
        p.setPen(QColor(52, 38, 92))
        p.setFont(font)
        text_rect = QRectF(rect.x() + 10, rect.y() + 8, rect.width() - 20, rect.height() - 14)
        p.drawText(text_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap,
                   self.bubble_text)
        p.restore()

    def draw_particles(self, p):
        p.save()
        p.setPen(Qt.NoPen)
        for part in self.particles:
            alpha = int(220 * max(0.0, min(1.0, part["life"])))
            p.setBrush(QColor(255, 132, 168, alpha))
            r = part["r"]
            p.drawEllipse(QRectF(part["x"] - r, part["y"] - r, r * 2, r * 2))
        p.restore()

    def draw_zzz(self, p):
        p.save()
        for i in range(3):
            phase = (self.anim_time * 0.55 + i * 0.72) % 2.16
            frac = phase / 2.16
            alpha = int(230 * (1.0 - frac))
            if alpha <= 0:
                continue
            size = 11 + i * 5
            font = QFont("Segoe UI", size)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QColor(120, 96, 200, alpha))
            px = self.center_x + 48 + i * 13 + frac * 12
            py = self.ground - 118 - frac * 46 - i * 6
            p.drawText(QRectF(px, py, 40, 34), Qt.AlignCenter, "z")
        p.restore()


def main():
    debug = "--debug" in sys.argv
    sleep_after = 60.0
    for arg in sys.argv[1:]:
        if arg.startswith("--sleep-after="):
            try:
                sleep_after = float(arg.split("=", 1)[1])
            except ValueError:
                pass
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("system tray is not available", file=sys.stderr)
    pet = Oktopet(debug=debug, sleep_after=sleep_after)
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
