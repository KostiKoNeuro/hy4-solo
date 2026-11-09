import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "verify"
VERIFY.mkdir(exist_ok=True)
LOG = VERIFY / "clicks.log"
HWND_FILE = VERIFY / "target_hwnd.txt"


class Target(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oktopet Click Target")
        self.setGeometry(320, 690, 1100, 370)
        self.setStyleSheet("background-color: #123b2c; color: #eaffef; font: 18pt 'Segoe UI';")
        self.label = QLabel("clicks: 0")
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.n = 0
        LOG.write_text("", encoding="utf-8")
        self.show()
        HWND_FILE.write_text(str(int(self.winId())), encoding="utf-8")

    def mousePressEvent(self, event):
        self.n += 1
        p = event.globalPosition()
        self.label.setText(f"clicks: {self.n}   last: {int(p.x())},{int(p.y())}")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{time.time():.3f} {int(p.x())} {int(p.y())}\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    target = Target()
    sys.exit(app.exec())
