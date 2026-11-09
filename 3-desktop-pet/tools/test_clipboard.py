import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clipboard as clip

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / "Oktopet" / "debug.cmd"
STATUS = ROOT / "Oktopet" / "status.json"

CASES = [
    ("link", "https://example.com/articles/octopus-facts", "react_link"),
    ("number", "1234567890", "react_number"),
    ("code", "def toss(pet):\n    pet.vy = -760\n    return pet.fly()", "react_code"),
    ("text", "Это очень длинный текст, который я скопировал, чтобы проверить, как настольный "
             "осьминог отреагирует на простыню символов. Он наверняка обнимет её всеми восемью "
             "щупальцами и всё равно не удержит, потому что букв слишком много, а рук всего восемь, "
             "пусть и очень ловких. Но он всё равно постарается, ведь он такой.", "react_text"),
]
EXPECTED_WORDS = {
    "link": ["Ссылка", "гиперссылка"],
    "number": ["Число", "Складываю"],
    "code": ["Код", "Компилирую", "точку"],
    "text": ["Простыня", "букв", "Столько"],
}


def cmd(text):
    CMD.write_text(text + "\n", encoding="utf-8")
    time.sleep(0.4)


def st():
    return json.loads(STATUS.read_text(encoding="utf-8"))


def main():
    r = []
    cmd("pos:600,808")
    for kind, text, sprite in CASES:
        clip.set_text(text)
        time.sleep(1.0)
        s = st()
        ok = (s["mode"] == "react" and s["sprite"] == sprite
              and s["last_clip_kind"] == kind and bool(s["bubble"]))
        bubble_ok = any(word in s["bubble"] for word in EXPECTED_WORDS[kind])
        r.append(ok and bubble_ok)
        print(("PASS  " if ok and bubble_ok else "FAIL  ") +
              f"clip:{kind:6s} -> mode={s['mode']} sprite={s['sprite']} "
              f"kind={s['last_clip_kind']} bubble={s['bubble']!r}")
        time.sleep(0.4)
    print("RESULT:", sum(r), "/", len(r))


if __name__ == "__main__":
    main()
