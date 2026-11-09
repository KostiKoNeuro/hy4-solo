import sys
from pathlib import Path

import numpy as np
from PIL import Image


def pet_mask(arr):
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    lavender = (b > r + 14) & (b > g + 24) & (r > 85) & (b > 145)
    pink = (r > 195) & (g > 95) & (g < 195) & (b > 120) & (b < 215)
    yellow = (r > 195) & (g > 170) & (b < 165)
    return lavender | pink | yellow


def analyze(path, region=None):
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    if region:
        x0, y0, x1, y1 = region
        sub = arr[y0:y1, x0:x1]
    else:
        x0 = y0 = 0
        sub = arr
    m = pet_mask(sub)
    ys, xs = np.where(m)
    result = {
        "file": Path(path).name,
        "size": list(im.size),
        "ink_pixels": int(m.sum()),
    }
    if len(xs):
        result["bbox_global"] = [int(xs.min() + x0), int(ys.min() + y0),
                                 int(xs.max() + x0), int(ys.max() + y0)]
        result["centroid_global"] = [round(float(xs.mean() + x0), 1),
                                     round(float(ys.mean() + y0), 1)]
        result["height"] = int(ys.max() - ys.min() + 1)
        result["width"] = int(xs.max() - xs.min() + 1)
    else:
        result["bbox_global"] = None
    return result


if __name__ == "__main__":
    import json
    for p in sys.argv[1:]:
        print(json.dumps(analyze(p), ensure_ascii=False))
