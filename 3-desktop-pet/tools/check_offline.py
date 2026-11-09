import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "Oktopet"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kie

key = kie.load_key()
key_bytes = key.encode("utf-8")
needles = [b"KIE_API_KEY", b"api.kie.ai", b"Authorization", b"Bearer ",
           b"requests", b"urllib", b"socket", b"http://", b"https://"]

files = [p for p in APP.rglob("*") if p.is_file()]
leaks = []
hits = []
for p in files:
    data = p.read_bytes()
    if key_bytes in data:
        leaks.append(str(p.relative_to(ROOT)))
    for n in needles:
        if n in data:
            hits.append((str(p.relative_to(ROOT)), n.decode("ascii", "replace")))

print("app files scanned:", len(files))
print("KEY LEAK IN APP:", "YES " + repr(leaks) if leaks else "NO")
print("network/secret string hits:", hits if hits else "NONE")
print("dotenv inside app folder:", (APP / ".env").exists())
print("gitignore covers .env:", ".env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
print("sprites bundled:", len(list((APP / "sprites").glob("*.png"))), "PNG +",
      len(list((APP / "sprites").glob("*.ico"))), "ICO")
