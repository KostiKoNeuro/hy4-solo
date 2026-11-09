import numpy as np
from PIL import Image

for name in ["idle", "react_link", "walk2", "grab", "react_number"]:
    im = Image.open(f"tools/raw/{name}.png").convert("RGBA")
    a = np.array(im)
    A, RGB = a[:, :, 3], a[:, :, :3]
    edge = np.zeros(A.shape, bool)
    edge[:6, :] = edge[-6:, :] = edge[:, :6] = edge[:, -6:] = True
    low = (A > 0) & (A < 40)
    print(f"--- {name}: size={im.size}")
    print("  alpha hist:", np.histogram(A, bins=[0, 1, 16, 40, 128, 235, 250, 256])[0].tolist())
    print("  corner alphas:", A[0, 0], A[0, -1], A[-1, 0], A[-1, -1])
    print("  edge nonzero frac:", round(float(((A > 0) & edge).mean() * 100), 2), "%")
    print("  low-alpha mean rgb:", RGB[low].mean(0).round(1) if low.any() else "none")
    print("  mid-alpha(40-235) mean rgb:", RGB[(A >= 40) & (A < 235)].mean(0).round(1))
    print("  high-alpha mean rgb:", RGB[A >= 235].mean(0).round(1))
