import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import input as inp

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / "Oktopet" / "debug.cmd"
STATUS = ROOT / "Oktopet" / "status.json"


def cmd(text):
    CMD.write_text(text + "\n", encoding="utf-8")
    time.sleep(0.45)


def st():
    return json.loads(STATUS.read_text(encoding="utf-8"))


def check(label, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + label + ("  " + detail if detail else ""))
    return ok


def main():
    r = []
    inp.up()
    time.sleep(0.15)
    inp.wake()
    cmd("pos:600,808")
    s = st()
    r.append(check("pet placed on taskbar", abs(s["x"] - 600) < 3 and abs(s["y"] - 808) < 3,
                   f"x={s['x']} y={s['y']}"))

    inp.move_to(720, 950)
    time.sleep(0.12)
    inp.down()
    time.sleep(0.25)
    s = st()
    r.append(check("grabbed", s["dragging"] and s["mode"] == "drag" and s["sprite"] == "grab",
                   f"mode={s['mode']} sprite={s['sprite']} dragging={s['dragging']}"))

    for i in range(1, 21):
        t = i / 20
        inp.move_to(720 + 130 * t, 950 - 430 * t)
        time.sleep(0.022)
    time.sleep(0.35)
    s = st()
    want_x, want_y = 720 + 130 - 120, 950 - 430 - 142
    r.append(check("pet follows cursor while held",
                   abs(s["x"] - want_x) < 25 and abs(s["y"] - want_y) < 25,
                   f"x={s['x']} y={s['y']} expected~({want_x},{want_y})"))

    inp.up()
    samples = []
    for _ in range(14):
        time.sleep(0.07)
        samples.append(st())
    air = [s for s in samples if s["mode"] == "air" and (abs(s["vx"]) > 20 or abs(s["vy"]) > 20)]
    r.append(check("release becomes a toss (air mode + velocity)", bool(air),
                   f"air_samples={len(air)} sample0={samples[0]['mode']}"))
    min_y = min(s["y"] for s in samples)
    for _ in range(18):
        time.sleep(0.09)
        s = st()
        min_y = min(min_y, s["y"])
    r.append(check("pet actually flies above the ground", min_y < 808 - 40, f"min_y={round(min_y)}"))

    time.sleep(2.2)
    s = st()
    r.append(check("pet lands back on the taskbar", abs(s["y"] - 808) < 4 and s["mode"] in ("walk", "land"),
                   f"y={s['y']} mode={s['mode']}"))
    inp.up()
    print("RESULT:", sum(r), "/", len(r))


if __name__ == "__main__":
    main()
