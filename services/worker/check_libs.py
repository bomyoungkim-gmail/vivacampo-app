try:
    import cv2
    print("cv2: OK")
except ImportError:
    print("cv2: MISSING")

try:
    import scipy.ndimage
    print("scipy: OK")
except ImportError:
    print("scipy: MISSING")

try:
    import skimage.transform
    print("skimage: OK")
except ImportError:
    print("skimage: MISSING")
