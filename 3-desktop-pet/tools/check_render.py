import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "Oktopet" / "sprites"


def main():
    bg_path, fg_path, status_path = sys.argv[1], sys.argv[2], sys.argv[3]
    st = json.loads(Path(status_path).read_text(encoding="utf-8"))
    x, y = int(round(st["x"])), int(round(st["y"]))
    sprite = st["sprite"]
    canvas = 240
    bg = np.array(Image.open(bg_path).convert("RGB")).astype(np.int16)[y:y + canvas, x:x + canvas]
    fg = np.array(Image.open(fg_path).convert("RGB")).astype(np.int16)[y:y + canvas, x:x + canvas]
    if bg.shape != fg.shape or bg.shape[:2] != (canvas, canvas):
        print("CROP FAILED", bg.shape, fg.shape, x, y)
        return
    diff = np.abs(bg - fg).max(axis=2) > 24
    sp = np.array(Image.open(SPRITES / (sprite + ".png")).convert("RGBA"))[:, :, 3] > 40
    inter = np.logical_and(diff, sp).sum()
    union = np.logical_or(diff, sp).sum()
    iou = inter / union if union else 0.0
    recall = inter / sp.sum() if sp.sum() else 0.0
    precision = inter / diff.sum() if diff.sum() else 0.0
    ys, xs = np.where(diff)
    print(json.dumps({
        "window": [x, y],
        "sprite": sprite,
        "changed_in_window": int(diff.sum()),
        "sprite_ink": int(sp.sum()),
        "IoU": round(float(iou), 3),
        "recall": round(float(recall), 3),
        "precision": round(float(precision), 3),
        "diff_bbox_local": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
        "sprite_bbox_local": [int(np.where(sp)[1].min()), int(np.where(sp)[0].min()),
                              int(np.where(sp)[1].max()), int(np.where(sp)[0].max())],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
