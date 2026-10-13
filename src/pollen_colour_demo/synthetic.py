"""
Synthetic pooled-pollen dish scenes with per-pixel ground truth.

Scene model: white paper; a glass dish (outer rim radius R, wall band 0.95-1.0 R with thin refraction lines); a
glass floor over the paper; a bed of shaded, anti-aliased round "loads" in known colours, packed over a dark deep
layer so that narrow crevices and a few wider voids remain; optionally an empty floor crescent on one side.

The colours are invented for the demo and do not represent any plant taxon or any real sample. The palette
deliberately includes a near-neutral grey load and a dark load that is larger than a crevice, because a segmenter
must not remove pollen just for being grey or dark.

Ground-truth codes (truth['gt']): 0 paper, 1 dish wall, 2 empty floor, 3 crevice / void, 4 load.
"""
import numpy as np
from scipy import ndimage as ndi

from . import colorimetry as CM

# name: (L*, a*, b*), load radius range in px at R = 600 (scaled with R)
COLOURS = {
    'orange': ((64, 30, 60), (12, 17)),
    'yellow': ((78, 2, 66), (12, 17)),
    'brown': ((44, 14, 28), (12, 17)),
    'cream': ((84, 1, 18), (12, 17)),
    'grey': ((57, -1, -3), (12, 17)),      # near-neutral load: must NOT be removed
    'dark': ((23, 5, 8), (16, 22)),        # dark load larger than a crevice: must NOT be removed
}
GAP_LAB = (9, 2, 3)
PAPER_LAB = (92, 0, 2)
FRAME = 1200

# Four scenes with different colour mixes and dish placements. IDs are deliberately generic.
SCENES = [
    dict(scene_id='synthetic_01', seed=101, R=400.0, cx=610.0, cy=590.0, crescent_deg=0.0,
         mix={'orange': .25, 'yellow': .20, 'brown': .15, 'cream': .15, 'grey': .15, 'dark': .10}),
    dict(scene_id='synthetic_02', seed=102, R=380.0, cx=585.0, cy=620.0, crescent_deg=140.0,
         mix={'orange': .50, 'yellow': .40, 'brown': .10}),
    dict(scene_id='synthetic_03', seed=103, R=420.0, cx=630.0, cy=605.0, crescent_deg=250.0,
         mix={'cream': .35, 'grey': .35, 'dark': .20, 'brown': .10}),
    dict(scene_id='synthetic_04', seed=104, R=395.0, cx=600.0, cy=602.0, crescent_deg=None,
         mix={'brown': .60, 'dark': .40}),
]


def make_scene(seed=0, R=400.0, cx=560.0, cy=545.0, crescent_deg=0.0, mix=None, H=FRAME, W=FRAME,
               paper_lab=PAPER_LAB, noise=0.003, coverage=0.93, scene_id='synthetic'):
    """Return (rgb uint8 HxWx3, truth dict). Deterministic for a given seed and arguments."""
    rng = np.random.default_rng(seed)
    mix = mix or {n: 1.0 for n in COLOURS}
    names = list(mix)
    probs = np.array([mix[n] for n in names], float)
    probs /= probs.sum()
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    rr = np.hypot(xx - cx, yy - cy)
    rho = rr / R
    ang = np.degrees(np.arctan2(yy - cy, xx - cx))
    img = np.broadcast_to(CM.lab_to_linear(paper_lab), (H, W, 3)).copy()
    gt = np.zeros((H, W), np.uint8)
    wall = (rho >= 0.95) & (rho < 1.0)
    img[wall] *= 0.86
    for rl, f in ((0.955, 0.55), (0.972, 1.06), (0.985, 0.6), (0.997, 0.5)):   # refraction / reflection lines
        img[np.abs(rr - rl * R) < 1.5] *= f
    gt[wall] = 1
    floor = rho < 0.95
    img[floor] *= 0.9
    gt[floor] = 2
    bed_region = rho < 0.86
    if crescent_deg is not None:
        dang = (ang - crescent_deg + 180) % 360 - 180
        bed_region &= ~((np.abs(dang) < 50) & (rho > 0.70))
    img[bed_region] = CM.lab_to_linear(GAP_LAB)
    gt[bed_region] = 3
    grain_id = np.zeros((H, W), np.int32)
    grain_col = np.full((H, W), -1, np.int8)
    cover = np.zeros((H, W), bool)
    ys_b, xs_b = np.nonzero(bed_region)
    gid = 0
    # painter's algorithm, like a multi-layer bed: loads overlap freely until `coverage` of the bed is covered;
    # what remains uncovered is the dark deep layer seen through interstices
    for it in range(60000):
        if it % 500 == 0 and cover[bed_region].mean() > coverage:
            break
        k = rng.choice(len(names), p=probs)
        lab, (rlo, rhi) = COLOURS[names[k]]
        r = rng.uniform(rlo, rhi) * R / 600.0
        j = rng.integers(len(ys_b))
        gy, gx = ys_b[j] + rng.uniform(-0.5, 0.5), xs_b[j] + rng.uniform(-0.5, 0.5)
        y0, y1 = int(max(0, gy - r - 2)), int(min(H, gy + r + 3))
        x0, x1 = int(max(0, gx - r - 2)), int(min(W, gx + r + 3))
        d = np.hypot(xx[y0:y1, x0:x1] - gx, yy[y0:y1, x0:x1] - gy)
        if not bed_region[y0:y1, x0:x1][d < r + 0.5].all():
            continue                                       # loads stay inside the bed region
        gid += 1
        alpha = np.clip(r - d + 0.5, 0, 1)[..., None]      # 1-px anti-aliased edge (mixed pixels)
        shade = (1 - 0.18 * np.clip(d / r, 0, 1) ** 2)[..., None]
        sub = img[y0:y1, x0:x1]
        img[y0:y1, x0:x1] = (1 - alpha) * sub + alpha * CM.lab_to_linear(lab) * shade
        full = alpha[..., 0] > 0.5
        gt[y0:y1, x0:x1][full] = 4
        grain_id[y0:y1, x0:x1][full] = gid
        grain_col[y0:y1, x0:x1][full] = k
        cover[y0:y1, x0:x1] |= alpha[..., 0] > 0
    # load interior = >= 3 px from any non-load pixel and from any load-load transition (unmixed pixels)
    dist_to_nonload = ndi.distance_transform_edt(gt == 4)
    transitions = ndi.morphological_gradient(grain_id, size=3) > 0
    interior = (gt == 4) & (dist_to_nonload >= 3) & (ndi.distance_transform_edt(~transitions) >= 3)
    lin = img + (rng.normal(0, noise, img.shape) if noise else 0)
    rgb = CM.linear_to_srgb8(lin)
    truth = dict(scene_id=scene_id, gt=gt, grain_id=grain_id, grain_col=grain_col, names=names, interior=interior,
                 rho=rho, bed_region=bed_region, dish=dict(cx=float(cx), cy=float(cy), R=float(R)), n_loads=gid,
                 mix=dict(mix))
    return rgb, truth


def make_demo_scenes(scenes=None):
    for spec in scenes or SCENES:
        yield make_scene(**spec)
