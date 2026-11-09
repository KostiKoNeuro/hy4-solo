import sys
from pathlib import Path

from PIL import ImageGrab


def main():
    dest = Path(sys.argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab()
    img.save(dest)
    print(dest, img.size)


if __name__ == "__main__":
    main()
