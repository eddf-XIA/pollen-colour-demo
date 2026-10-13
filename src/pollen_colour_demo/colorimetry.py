"""
Colour-science conversions (single source of truth).

  8-bit sRGB --(IEC 61966-2-1 decoding, exact 256-entry LUT)--> linear RGB
  linear RGB --(scikit-image sRGB->XYZ matrix, D65)--> XYZ --(scikit-image xyz2lab, D65 / 2 deg)--> CIELAB

Colour distances are CIEDE2000 in CIELAB, never Euclidean distances in sRGB or OpenCV's 8-bit Lab.
"""
import numpy as np
from skimage.color import colorconv, deltaE_ciede2000, lab2rgb, xyz2lab

M_RGB_TO_XYZ = np.array(colorconv.xyz_from_rgb, dtype=np.float64)      # sRGB (D65) primaries, scikit-image


def srgb_decode(v):
    """IEC 61966-2-1 inverse transfer function for values in [0, 1] (float64)."""
    v = np.asarray(v, dtype=np.float64)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def srgb_encode(lin):
    lin = np.asarray(lin, dtype=np.float64)
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)


SRGB8_TO_LINEAR = srgb_decode(np.arange(256) / 255.0)   # exact LUT, float64


def srgb8_to_linear(u8):
    u8 = np.asarray(u8)
    if u8.dtype != np.uint8:
        raise TypeError('expected uint8 sRGB values')          # guards against silent integer wrap/clip upstream
    return SRGB8_TO_LINEAR[u8]


def linear_to_xyz(lin):
    return np.asarray(lin, dtype=np.float64) @ M_RGB_TO_XYZ.T


def linear_to_lab(lin):
    xyz = linear_to_xyz(lin)
    shp = xyz.shape
    return xyz2lab(xyz.reshape(-1, 1, 3), illuminant='D65', observer='2').reshape(shp)


def srgb8_to_lab(u8):
    return linear_to_lab(srgb8_to_linear(u8))


def lab_to_linear(lab):
    """CIELAB (D65) -> linear sRGB, out-of-gamut values clipped to [0, 1]. Used to render synthetic scenes."""
    lab = np.asarray(lab, dtype=np.float64)
    enc = lab2rgb(lab.reshape(-1, 1, 3), illuminant='D65', observer='2').reshape(lab.shape)
    return srgb_decode(enc)


def linear_to_srgb8(lin):
    return np.clip(np.round(srgb_encode(np.clip(lin, 0, 1)) * 255), 0, 255).astype(np.uint8)


def lab_to_lch(lab):
    lab = np.asarray(lab)
    C = np.hypot(lab[..., 1], lab[..., 2])
    h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360.0
    return C, h


def delta_e00(lab1, lab2):
    return deltaE_ciede2000(np.asarray(lab1, float), np.asarray(lab2, float))
