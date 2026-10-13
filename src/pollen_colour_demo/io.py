"""Lossless image I/O. Colour values are always taken from the full-resolution decoded array."""
import numpy as np
from PIL import Image, ImageOps


def save_png(rgb, path):
    Image.fromarray(np.ascontiguousarray(rgb, dtype=np.uint8)).save(path, 'PNG')


def load_rgb(path):
    """Decode to an HxWx3 uint8 sRGB array; the EXIF orientation (if any) is applied as a lossless permutation."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != 'RGB':
            im = im.convert('RGB')
        return np.asarray(im, dtype=np.uint8).copy()
