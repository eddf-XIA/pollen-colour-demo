"""
Pixel classification. Segmentation is decided here, never by colour clustering.

Every pixel of the image gets exactly one class (first matching rule wins):

  0 OUTSIDE_DISH        rho >= 1 (rho = distance to dish centre / outer-rim radius R)
  1 DISH_WALL_RIM       0.89 <= rho < 1: wall band seen in perspective, refraction, reflections
  2 DISH_FLOOR_EMPTY    rho < 0.89 and not pollen bed: background region-grown from the wall band through
                        smooth, near-neutral, bright pixels (empty glass floor over paper) on a coarse copy,
                        then refined at full resolution within refine_depth_R of the coarse edge
  3 BED_BOUNDARY_BAND   pollen bed within boundary_band_R * R of the bed edge, or within floor_margin_R * R of
                        exposed dish floor, or at rho >= rim_glare_rho; the reason is stored per pixel
                        (band_reason 1 edge / 2 floor margin / 3 rim glare)
  4 CLIPPED_WHITE       bed interior, every channel at/above the white reference (default 255)
  5 CLIPPED_BLACK       bed interior, every channel at/below the black reference (default 0)
  6 INTERSTITIAL_SHADOW bed interior, black top-hat depth of L* > shadow_depth_L with a structuring element
                        smaller than a pollen load: narrow crevices. Dark loads larger than the element are NOT
                        flagged (a size criterion, not a darkness criterion)
 10 MEASURED            everything else in the bed interior: the colour-measurement mask

No pixel is excluded only for being dark, grey or desaturated: every exclusion is geometric (outside the bed,
boundary band, narrow crevice) or optical (all channels clipped).

Per-pixel evidence flags (uint8 bitfield, independent of the class, so any rule can be re-applied later):
  1 any channel == 0 | 2 any channel == 255 | 4 all == 0 | 8 all == 255 | 16 shadow depth > threshold
  32 within boundary band distance | 128 background-like feature
Coarse-scale masks are mapped to full resolution with nearest-neighbour indexing; colour values are never resampled.
"""
import cv2
import numpy as np
from scipy import ndimage as ndi

from . import colorimetry as CM
from .params import PARAMS

S = PARAMS['segmentation']

OUTSIDE_DISH, DISH_WALL_RIM, DISH_FLOOR_EMPTY, BED_BOUNDARY_BAND = 0, 1, 2, 3
CLIPPED_WHITE, CLIPPED_BLACK, INTERSTITIAL_SHADOW, MEASURED = 4, 5, 6, 10
CLASS_NAMES = {0: 'outside_dish', 1: 'dish_wall_rim', 2: 'dish_floor_empty', 3: 'bed_boundary_band',
               4: 'clipped_white', 5: 'clipped_black', 6: 'interstitial_shadow', 10: 'measured'}
# display colours for the class map (categorical set, all pairs separable under colour-vision deficiency)
CLASS_COLORS = {0: (40, 40, 40), 1: (74, 58, 167), 2: (232, 123, 164), 3: (42, 120, 214), 4: (255, 255, 255),
                5: (255, 255, 255), 6: (0, 131, 0), 10: (237, 161, 0)}
F_ANY0, F_ANY255, F_ALL0, F_ALL255, F_SHADOW, F_BAND, F_BGLIKE = 1, 2, 4, 8, 16, 32, 128


def crop_box(shape, cx, cy, R, margin=1.02):
    H, W = shape[:2]
    y0, y1 = int(np.floor(max(0, cy - margin * R))), int(np.ceil(min(H, cy + margin * R + 1)))
    x0, x1 = int(np.floor(max(0, cx - margin * R))), int(np.ceil(min(W, cx + margin * R + 1)))
    return y0, y1, x0, x1


def coarse_features(crop_rgb, R):
    """Texture / chroma / lightness on a copy resampled so that R = coarse_R_px (features only)."""
    k = S['coarse_R_px'] / R
    h, w = crop_rgb.shape[:2]
    hc, wc = max(8, int(round(h * k))), max(8, int(round(w * k)))
    small = cv2.resize(crop_rgb, (wc, hc), interpolation=cv2.INTER_AREA)
    lab = CM.srgb8_to_lab(small)
    L, Cab = lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])
    g = S['feature_sigma_coarse_px']
    mu = ndi.gaussian_filter(L, g)
    sd = np.sqrt(np.clip(ndi.gaussian_filter(L * L, g) - mu * mu, 0, None))
    return dict(sd=sd, Cs=ndi.gaussian_filter(Cab, g), Ls=mu, k=k, shape=(hc, wc))


def _largest(mask):
    lbl, n = ndi.label(mask)
    if n == 0:
        return mask
    return lbl == (np.argmax(ndi.sum(mask, lbl, range(1, n + 1))) + 1)


def bed_mask_coarse(feat, cxc, cyc, Rc):
    hc, wc = feat['shape']
    yy, xx = np.mgrid[0:hc, 0:wc]
    rho = np.hypot(xx - cxc, yy - cyc) / Rc
    bglike = (feat['sd'] < S['bg_texture_max']) & (feat['Cs'] < S['bg_chroma_max']) & (feat['Ls'] > S['bg_lightness_min'])
    rim = S['rim_zone_rho']
    grow_domain = bglike & (rho < 1.0)
    lbl, n = ndi.label(grow_domain, structure=np.ones((3, 3)))
    seeds = np.unique(lbl[grow_domain & (rho >= rim)])
    seeds = seeds[seeds > 0]
    bg = np.isin(lbl, seeds)
    r = S['coarse_morph_radius']
    st = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    bg = cv2.morphologyEx(bg.astype(np.uint8), cv2.MORPH_CLOSE, st).astype(bool)
    bed = (rho < rim) & ~bg
    bed = cv2.morphologyEx(bed.astype(np.uint8), cv2.MORPH_OPEN, st).astype(bool)
    bed = ndi.binary_fill_holes(_largest(bed)) & (rho < rim)
    return bed, bglike, bg


def to_full(mask_c, full_shape):
    """Nearest-neighbour index mapping of a coarse mask onto the full-resolution crop grid."""
    h, w = full_shape
    hc, wc = mask_c.shape
    yi = np.minimum((np.arange(h) + 0.5) * hc / h, hc - 1).astype(int)
    xi = np.minimum((np.arange(w) + 0.5) * wc / w, wc - 1).astype(int)
    return mask_c[yi[:, None], xi[None, :]]


def classify(rgb, dish, black_ref=(0, 0, 0), white_ref=(255, 255, 255)):
    """Return dict with the full-frame label map, flags and crop-level arrays for the dish region.

    rgb: HxWx3 uint8 sRGB. dish: dict(cx, cy, R) of the outer rim (see dish.detect_dish).
    black_ref / white_ref: per-channel clip references (e.g. from a colour chart); defaults are 0 / 255.
    """
    H, W = rgb.shape[:2]
    cx, cy, R = dish['cx'], dish['cy'], dish['R']
    y0, y1, x0, x1 = crop_box(rgb.shape, cx, cy, R)
    crop = rgb[y0:y1, x0:x1]
    h, w = crop.shape[:2]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    rho = np.hypot(xx - cx, yy - cy) / R

    feat = coarse_features(crop, R)
    k = feat['k']
    bed_c, bglike_c, bg_c = bed_mask_coarse(feat, (cx - x0 + 0.5) * k - 0.5, (cy - y0 + 0.5) * k - 0.5, R * k)
    # the bed is everything inside the rim cut that is not grown background (using the opened coarse bed mask
    # instead would leave a thin artificial "floor" ring at the rim cut)
    bed = (rho < S['rim_zone_rho']) & ~to_full(bg_c, (h, w))
    bed = ndi.binary_fill_holes(_largest(bed))
    bglike = to_full(bglike_c, (h, w))

    lab = CM.srgb8_to_lab(crop)
    L = lab[..., 0].astype(np.float32)

    # full-resolution refinement of the bed edge: grow the background inward through smooth, near-neutral, bright
    # pixels, limited to refine_depth_R of the coarse edge (so interior grey loads can never be absorbed)
    sig_f = max(1.0, S['fine_sigma_R'] * R)
    L64 = lab[..., 0]
    mu_f = ndi.gaussian_filter(L64, sig_f)
    sd_f = np.sqrt(np.clip(ndi.gaussian_filter(L64 * L64, sig_f) - mu_f * mu_f, 0, None))
    C_f = ndi.gaussian_filter(np.hypot(lab[..., 1], lab[..., 2]), sig_f)
    fine_bglike = (sd_f < S['bg_texture_max']) & (C_f < S['bg_chroma_max']) & (mu_f > S['bg_lightness_min'])
    depth_coarse = ndi.distance_transform_edt(np.pad(bed, 1, constant_values=False))[1:-1, 1:-1]
    cand = bed & fine_bglike & (depth_coarse <= S['refine_depth_R'] * R)
    outside_bed = ~bed & (rho < 1.0)
    lbl, _ = ndi.label(cand | outside_bed, structure=np.ones((3, 3)))
    keep = np.unique(lbl[outside_bed])
    eaten = cand & np.isin(lbl, keep[keep > 0])
    bed = _largest(bed & ~eaten)
    n_refined = int(eaten.sum())
    rs = max(1, int(round(S['shadow_se_radius_R'] * R)))
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rs + 1, 2 * rs + 1))
    depth = cv2.morphologyEx(L, cv2.MORPH_CLOSE, se) - L
    rv = max(1, int(round(S['void_se_radius_R'] * R)))
    sev = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rv + 1, 2 * rv + 1))
    depth_large = cv2.morphologyEx(L, cv2.MORPH_CLOSE, sev) - L      # stored feature only (never a class)

    dist = ndi.distance_transform_edt(np.pad(bed, 1, constant_values=False))[1:-1, 1:-1]
    d_band = S['boundary_band_R'] * R
    # exposed dish floor inside the rim cut: the bed thins toward it, so the band is wider there (floor_margin_R)
    floor = (rho < S['rim_zone_rho']) & ~bed
    flbl, nfl = ndi.label(floor, structure=np.ones((3, 3)))
    if nfl:
        sizes = ndi.sum(floor, flbl, range(1, nfl + 1))
        big = np.nonzero(sizes >= np.pi * (S['floor_min_component_R'] * R) ** 2)[0] + 1
        floor = np.isin(flbl, big)
    d_floor = (ndi.distance_transform_edt(~floor) if floor.any() else np.full((h, w), np.inf)).astype(np.float32)

    all0 = (crop == 0).all(2)
    all255 = (crop == 255).all(2)
    below_black = (crop <= np.asarray(black_ref, float)).all(2)
    above_white = (crop >= np.asarray(white_ref, float)).all(2)
    any0 = (crop == 0).any(2)
    any255 = (crop == 255).any(2)
    shadow = depth > S['shadow_depth_L']
    band_edge = bed & (dist <= d_band)
    band_floor = bed & ~band_edge & (d_floor <= S['floor_margin_R'] * R)
    band_rim = bed & ~band_edge & ~band_floor & (rho >= S['rim_glare_rho'])
    band = band_edge | band_floor | band_rim
    band_reason = (band_edge * 1 + band_floor * 2 + band_rim * 3).astype(np.uint8)   # 1 edge, 2 floor margin, 3 rim glare

    cls = np.full((h, w), OUTSIDE_DISH, np.uint8)
    cls[rho < 1.0] = DISH_WALL_RIM
    cls[rho < S['rim_zone_rho']] = DISH_FLOOR_EMPTY
    interior = bed & ~band
    cls[band] = BED_BOUNDARY_BAND
    cls[interior] = MEASURED
    cls[interior & shadow] = INTERSTITIAL_SHADOW
    cls[interior & below_black] = CLIPPED_BLACK
    cls[interior & above_white] = CLIPPED_WHITE

    flags = (any0 * F_ANY0 | any255 * F_ANY255 | all0 * F_ALL0 | all255 * F_ALL255 | shadow * F_SHADOW
             | (bed & (dist <= d_band)) * F_BAND | bglike * F_BGLIKE).astype(np.uint8)

    label_full = np.zeros((H, W), np.uint8)
    label_full[y0:y1, x0:x1] = cls
    return dict(label=label_full, box=(y0, y1, x0, x1), cls_crop=cls, flags_crop=flags, rho_crop=rho,
                depth_crop=depth, depth_large_crop=depth_large, lab_crop=lab, bed_crop=bed,
                band_reason_crop=band_reason, n_band_edge=int(band_edge.sum()), n_band_floor=int(band_floor.sum()),
                n_band_rim=int(band_rim.sum()), shadow_se_radius_px=rs, void_se_radius_px=rv,
                n_edge_refined=n_refined)
