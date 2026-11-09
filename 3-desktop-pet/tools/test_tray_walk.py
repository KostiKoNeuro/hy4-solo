import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / "Oktopet" / "debug.cmd"
STATUS = ROOT / "Oktopet" / "status.json"


def cmd(text, wait=0.45):
    CMD.write_text(text + "\n", encoding="utf-8")
    time.sleep(wait)


def st():
    return json.loads(STATUS.read_text(encoding="utf-8"))


def check(label, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + label + ("  " + detail if detail else ""))
    return ok


def main():
    r = []
    names = [s for s in st()["menu_items"] if s]
    r.append(check("tray menu has all requested actions",
                   all(x in names for x in ["Покормить", "Уложить спать", "Выход"]),
                   repr(names)))

    cmd("feed", 0.6)
    s = st()
    r.append(check("feed action", s["mode"] == "eat" and s["sprite"] == "eat" and bool(s["bubble"]),
                   f"mode={s['mode']} sprite={s['sprite']}"))

    cmd("sleep", 0.6)
    s = st()
    r.append(check("put-to-sleep action",
                   s["sleeping"] and s["forced_sleep"] and s["mode"] == "sleep" and s["sprite"] == "sleep",
                   f"sleeping={s['sleeping']} forced={s['forced_sleep']} sprite={s['sprite']}"))

    cmd("wake", 0.6)
    s = st()
    r.append(check("wake action", s["mode"] == "yawn" and not s["sleeping"] and not s["forced_sleep"],
                   f"mode={s['mode']} sleeping={s['sleeping']}"))

    cmd("pos:1660,808")
    cmd("unfreeze", 0.2)
    xs = []
    for _ in range(20):
        time.sleep(0.2)
        xs.append(st()["x"])
    r.append(check("walks along taskbar and turns at the right edge",
                   max(xs) <= 1681 and min(xs) < max(xs) - 8,
                   f"x_range=[{round(min(xs))},{round(max(xs))}]"))

    cmd("pos:600,808")
    cmd("menu", 0.8)
    s = st()
    r.append(check("tray context menu opens", s["menu_visible"], f"menu_visible={s['menu_visible']}"))
    print("RESULT:", sum(r), "/", len(r))


if __name__ == "__main__":
    main()
