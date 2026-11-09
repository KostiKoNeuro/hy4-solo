import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import input as inp

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / "Oktopet" / "debug.cmd"
STATUS = ROOT / "Oktopet" / "status.json"
LOG = ROOT / "verify" / "clicks.log"
TARGET_HWND = int((ROOT / "verify" / "target_hwnd.txt").read_text().strip())

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foreground as fg


def cmd(text):
    CMD.write_text(text + "\n", encoding="utf-8")
    time.sleep(0.45)


def status():
    return json.loads(STATUS.read_text(encoding="utf-8"))


def clicks():
    lines = LOG.read_text(encoding="utf-8").splitlines()
    return len(lines), lines


def report(label, ok, detail=""):
    print(("PASS" if ok else "FAIL") + "  " + label + ("  " + detail if detail else ""))
    return ok


def main():
    results = []
    LOG.write_text("", encoding="utf-8")
    cmd("pos:600,808")
    st = status()
    results.append(report("frozen at target", abs(st["x"] - 600) < 2 and abs(st["y"] - 808) < 2,
                          f"x={st['x']} y={st['y']} mode={st['mode']}"))

    inp.click(400, 900)
    time.sleep(0.4)
    n, _ = clicks()
    results.append(report("click outside pet window reaches target", n == 1, f"clicks={n}"))

    before = fg.info()[0]
    inp.click(603, 811)
    time.sleep(0.4)
    n, _ = clicks()
    results.append(report("click on transparent pet pixel passes through", n == 2, f"clicks={n}"))

    inp.click(720, 950)
    time.sleep(0.4)
    n, lines = clicks()
    after = fg.info()[0]
    st = status()
    results.append(report("click on pet is captured, not passed through", n == 2, f"clicks={n}"))
    results.append(report("pet does not steal focus", after == before,
                          f"before={before} after={after} target={TARGET_HWND}"))
    results.append(report("pet reacted to grab", st["mode"] in ("air", "land", "walk", "drag"),
                          f"mode={st['mode']}"))
    print("clicks log:")
    for line in lines:
        print("   " + line)
    print("RESULT:", sum(results), "/", len(results))


if __name__ == "__main__":
    main()
