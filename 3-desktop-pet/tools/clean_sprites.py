import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tools" / "raw"
OUT = ROOT / "Oktopet" / "sprites"
OUT.mkdir(parents=True, exist_ok=True)

CANVAS = 240
GROUND = 222
CENTER_X = 120
TARGET_H = 150
IDLE_CORE_FRAC = 940.0 / 1254.0

NAMES = [
    "idle", "blink", "walk1", "walk2", "sleep", "yawn", "grab", "toss",
    "land", "eat", "react_link", "react_number", "react_code", "react_text",
]


def clean_rgba(path):
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    A = a[:, :, 3].astype(np.float32)
    RGB = a[:, :, :3].astype(np.float32)

    if (A == 0).mean() < 0.05:
        light = RGB.min(axis=2) > 225
        A = np.where(light, 0.0, 255.0)

    core = (A >= 235).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(core, 8)
    if n > 1:
        keep = np.zeros_like(core)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] >= 80:
                keep[labels == i] = 1
        core = keep

    coref = core.astype(np.float32)
    blur_m = cv2.GaussianBlur(coref, (5, 5), 0)
    premul = RGB * coref[:, :, None]
    blur_p = np.stack(
        [cv2.GaussianBlur(premul[:, :, c], (5, 5), 0) for c in range(3)], axis=2
    )
    rgb_clean = blur_p / np.maximum(blur_m[:, :, None], 1e-5)
    A_clean = np.clip(blur_m * 255.0 * 1.18, 0, 255)
    A_clean[core > 0] = 255.0
    A_clean[A_clean < 8] = 0.0

    out = np.dstack([np.clip(rgb_clean, 0, 255), A_clean]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def normalized(name):
    src = clean_rgba(RAW / (name + ".png"))
    W = src.width
    scale = TARGET_H / (IDLE_CORE_FRAC * W)

    alpha = np.array(src)[:, :, 3]
    ys, xs = np.where(alpha >= 8)
    if len(xs) == 0:
        raise RuntimeError(name + ": empty sprite after cleanup")
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    cropped = src.crop(box)
    nw = max(1, round(cropped.width * scale))
    nh = max(1, round(cropped.height * scale))
    scaled = cropped.resize((nw, nh), Image.LANCZOS)

    if nw > CANVAS - 8 or nh > CANVAS - 8:
        k = min((CANVAS - 8) / nw, (CANVAS - 8) / nh)
        nw2, nh2 = max(1, round(nw * k)), max(1, round(nh * k))
        scaled = scaled.resize((nw2, nh2), Image.LANCZOS)
        nw, nh = nw2, nh2

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = CENTER_X - nw // 2
    y = GROUND - nh
    canvas.alpha_composite(scaled, (int(x), int(y)))
    return canvas


def main():
    info = {}
    for name in NAMES:
        img = normalized(name)
        dest = OUT / (name + ".png")
        img.save(dest, optimize=True)
        a = np.array(img)[:, :, 3]
        ys, xs = np.where(a >= 8)
        info[name] = {
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "size": list(img.size),
        }
        print(f"{name:14s} -> {dest.name:20s} bbox={info[name]['bbox']}")

    idle = Image.open(OUT / "idle.png").convert("RGBA")
    sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)]
    idle.save(OUT / "tray.ico", format="ICO", sizes=sizes)
    idle.save(ROOT / "Oktopet" / "icon.ico", format="ICO", sizes=sizes)
    print("tray.ico / icon.ico written")

    (OUT / "atlas.json").write_text(json.dumps({
        "canvas": CANVAS, "ground": GROUND, "center_x": CENTER_X,
        "target_h": TARGET_H, "sprites": info,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
