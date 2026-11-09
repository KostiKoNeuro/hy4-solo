import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAMP = " .:-=+*#%@"


def classify(r, g, b):
    r, g, b = float(r), float(g), float(b)
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx / 255.0
    if mn > 215:
        return "o"
    if v < 0.33:
        return "#"
    if r > g + 35 and r > b + 15 and r > 140:
        return "p"
    if r > 175 and g > 155 and b < 145:
        return "*"
    if b > r + 28 and b > g + 18:
        return "c"
    if b > r + 10 and r > g + 10:
        return "L"
    if b > r + 5:
        return "l"
    return "+"


def preview(path, w=64):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((w, w))
    a = np.array(im)
    alpha, rgb = a[:, :, 3], a[:, :, :3]
    lines = []
    for row in range(a.shape[0]):
        line = []
        for col in range(a.shape[1]):
            A = alpha[row, col]
            if A < 40:
                line.append(" ")
            elif A < 150:
                line.append(".")
            else:
                line.append(classify(*rgb[row, col]))
        lines.append("".join(line).rstrip())
    return "\n".join(lines)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("=== " + Path(p).name + " ===")
        print(preview(p))
