import sys

import cv2

from privacy import PrivacyBlur

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_privacy.py <src_image> <dst_image>")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    img = cv2.imread(src)
    if img is None:
        print(f"Error: Could not load image from '{src}'")
        sys.exit(1)
    out, count = PrivacyBlur().apply(img)
    cv2.imwrite(dst, out)
    print(f"regions blurred: {count}")


if __name__ == "__main__":
    main()
