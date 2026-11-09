import numpy as np
from PIL import Image
from pathlib import Path

OUT = Path("Oktopet/sprites")
base = np.array(Image.open(OUT / "idle.png").convert("RGBA")).astype(np.float32)
names = sorted(p.stem for p in OUT.glob("*.png"))
for n in names:
    a = np.array(Image.open(OUT / (n + ".png")).convert("RGBA")).astype(np.float32)
    d = np.abs(a - base).mean()
    mask = (a[:, :, 3] > 40) | (base[:, :, 3] > 40)
    dmask = np.abs(a - base)[mask].mean()
    print(f"{n:15s} mean_abs_diff={d:6.2f}  on_ink={dmask:6.2f}")
