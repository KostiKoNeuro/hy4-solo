import glob
import os

import numpy as np
from PIL import Image

print("name             size          a0%   a>=240%  a255%   bbox")
for p in sorted(glob.glob("tools/raw/*.png")):
    im = Image.open(p).convert("RGBA")
    a = np.array(im)[:, :, 3]
    print(
        f"{os.path.basename(p):16s} {str(im.size):12s} "
        f"{round(float((a == 0).mean() * 100), 1):5} "
        f"{round(float((a >= 240).mean() * 100), 1):7} "
        f"{round(float((a == 255).mean() * 100), 1):5}   {im.getbbox()}"
    )
