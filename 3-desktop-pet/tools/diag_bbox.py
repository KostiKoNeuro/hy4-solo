import glob
import os

import numpy as np
from PIL import Image

for p in sorted(glob.glob("tools/raw/*.png")):
    im = Image.open(p).convert("RGBA")
    A = np.array(im)[:, :, 3]
    core = A >= 235
    ys, xs = np.where(core)
    print(
        f"{os.path.basename(p):18s} core bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) "
        f"w={xs.max()-xs.min()+1:4d} h={ys.max()-ys.min()+1:4d} "
        f"cx={(xs.min()+xs.max())/2:6.0f} cy={(ys.min()+ys.max())/2:6.0f}"
    )
