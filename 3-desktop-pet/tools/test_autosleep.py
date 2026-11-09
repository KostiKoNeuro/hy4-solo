import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import input as inp

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "Oktopet" / "status.json"


def st():
    return json.loads(STATUS.read_text(encoding="utf-8"))


def check(label, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + label + ("  " + detail if detail else ""))
    return ok


def main():
    r = []
    time.sleep(0.8)
    s = st()
    r.append(check("starts awake even on a long-idle machine",
                   not s["sleeping"] and s["sleep_after"] == 3.0,
                   f"sleeping={s['sleeping']} idle={s['idle_sec']} raw_idle={s['raw_idle_sec']} after={s['sleep_after']}"))

    slept = False
    peak_idle = 0.0
    for _ in range(18):
        time.sleep(0.4)
        s = st()
        peak_idle = max(peak_idle, s["idle_sec"])
        if s["sleeping"]:
            slept = True
            break
    r.append(check("falls asleep after the idle threshold with no input", slept,
                   f"peak_idle={round(peak_idle, 1)} sleeping={s['sleeping']}"))

    inp.wake()
    woke = False
    for _ in range(8):
        time.sleep(0.2)
        s = st()
        if not s["sleeping"] and s["mode"] in ("yawn", "walk"):
            woke = True
            break
    r.append(check("wakes on any input with a yawn", woke,
                   f"sleeping={s['sleeping']} mode={s['mode']}"))
    print("RESULT:", sum(r), "/", len(r))


if __name__ == "__main__":
    main()
