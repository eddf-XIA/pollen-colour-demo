"""
Dish geometry: coarse Hough circle, then refinement to the OUTER RIM EDGE.

A glass dish photographed slightly off-axis shows its wall as a band of concentric lines, and a Hough transform can
lock onto any of them. The one edge that is sharp and consistently defined is the outermost one, where the glass
rim meets the paper. For each of 720 angles we take the outermost strong radial edge that is followed by at least
0.04 R of smooth paper, then fit a circle to those points with iterative 3-MAD outlier rejection (rays that leave
the frame or hit clutter drop out as outliers or give no point).
"""
import cv2
import numpy as np
from scipy import ndimage as ndi

from .params import PARAMS

P = PARAMS['dish']


class DishError(RuntimeError):
    pass


def hough_dish(rgb):
    H, W = rgb.shape[:2]
    s = P['scale']
    gray = cv2.cvtColor(cv2.resize(rgb, (W // s, H // s), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (P['blur_ksize'], P['blur_ksize']), 0)
    lo, hi = P['radius_range_frac_of_min_side']
    rmin, rmax = int(lo * min(H, W) / s), int(hi * min(H, W) / s)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=P['dp'], minDist=rmin, param1=P['param1'],
                               param2=P['param2'], minRadius=rmin, maxRadius=rmax)
    if circles is None:
        raise DishError('no Hough circle')
    cx, cy, r = (circles[0][0] * s + (s - 1) / 2.0).tolist()
    return cx, cy, r


def _fit_circle(x, y):
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    b = x * x + y * y
    (a, bb, c), *_ = np.linalg.lstsq(A, b, rcond=None)
    return a, bb, np.sqrt(c + a * a + bb * bb)


def refine_outer_rim(rgb, cx0, cy0, r0, n_theta=None):
    n_theta = n_theta or P['refine_n_rays']
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    H, W = gray.shape
    th = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    lo, hi = P['refine_search_rho']
    rr = np.arange(int(lo * r0), int(hi * r0), dtype=np.float64)
    X = cx0 + rr[None, :] * np.cos(th[:, None])
    Y = cy0 + rr[None, :] * np.sin(th[:, None])
    inside = (X >= 0) & (X <= W - 1) & (Y >= 0) & (Y <= H - 1)
    pol = ndi.map_coordinates(gray, [Y, X], order=1, cval=np.nan)   # geometry only; never used for colour
    pol[~inside] = np.nan
    sm = ndi.gaussian_filter1d(np.nan_to_num(pol, nan=0.0), 1.5, axis=1)
    grad = np.abs(np.gradient(sm, axis=1))
    grad[~inside] = np.nan
    run = int(0.04 * r0)          # paper must stay smooth for 0.04 R beyond the rim
    gap = int(0.015 * r0)         # the smoothed edge itself spills a few px outward
    idx = np.arange(len(rr))
    xs, ys = [], []
    for i in range(n_theta):
        g = grad[i]
        if np.isnan(g).any():
            continue                                   # ray leaves the frame: no clean paper to verify
        quiet = g < 1.5                                # smooth paper
        cs = np.concatenate([[0], np.cumsum(quiet)])
        run_ok = np.zeros(len(g), bool)
        run_ok[:len(g) - run] = (cs[run:len(g)] - cs[:len(g) - run]) == run
        starts = np.nonzero(run_ok)[0]
        if len(starts) == 0:
            continue
        nxt = np.searchsorted(starts, idx, side='right')
        has = nxt < len(starts)
        ok = np.zeros(len(g), bool)
        ok[has] = starts[nxt[has]] - idx[has] <= gap
        cand = np.nonzero((g > 4.0) & ok)[0]
        if len(cand) == 0:
            continue
        j = cand.max()
        xs.append(X[i, j]); ys.append(Y[i, j])
    xs, ys = np.array(xs), np.array(ys)
    if len(xs) < 0.25 * n_theta:
        raise DishError(f'rim refinement: only {len(xs)} usable rays')
    keep = np.ones(len(xs), bool)
    for _ in range(10):
        a, b, R = _fit_circle(xs[keep], ys[keep])
        res = np.hypot(xs - a, ys - b) - R
        mad = np.median(np.abs(res[keep] - np.median(res[keep]))) * 1.4826
        new = np.abs(res - np.median(res[keep])) <= max(3 * mad, 2.0)
        if np.array_equal(new, keep):
            break
        keep = new
    a, b, R = _fit_circle(xs[keep], ys[keep])
    res = np.hypot(xs[keep] - a, ys[keep] - b) - R
    return dict(cx=float(a), cy=float(b), R=float(R), rim_fit_rms_px=float(np.sqrt(np.mean(res ** 2))),
                rim_rays_used=int(keep.sum()), rim_rays_with_edge=int(len(xs)), rim_rays_total=n_theta,
                hough_cx=float(cx0), hough_cy=float(cy0), hough_R=float(r0))


def detect_dish(rgb):
    cx0, cy0, r0 = hough_dish(rgb)
    return refine_outer_rim(rgb, cx0, cy0, r0)
