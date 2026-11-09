import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    a = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(np.int16)
    b = np.array(Image.open(sys.argv[2]).convert("RGB")).astype(np.int16)
    d = np.abs(a - b).max(axis=2)
    m = d > 24
    ys, xs = np.where(m)
    print("changed pixels:", int(m.sum()))
    if len(xs):
        print("diff bbox:", [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
        print("diff centroid:", [round(float(xs.mean()), 1), round(float(ys.mean()), 1)])
    else:
        print("diff bbox: None")


if __name__ == "__main__":
    main()
