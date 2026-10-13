"""
Fixed parameters.

Spatial parameters are expressed in units of the detected dish radius R (outer rim, pixels), so they mean the same
physical size at any image resolution. Segmentation values are carried over unchanged from the research pipeline
this demo is adapted from; they are not tuned to the synthetic scenes. Distribution bins are fixed in advance and do
not depend on the data.
"""
import hashlib
import json

PARAMS = {
    'dish': {
        'scale': 2, 'blur_ksize': 7, 'dp': 1.2, 'param1': 80, 'param2': 40,
        'radius_range_frac_of_min_side': [0.25, 0.48],   # Hough search range (demo prior; no colour chart here)
        # radial window (in units of the Hough radius) searched for the outer rim edge. Without a chart-based radius
        # prior, Hough can lock onto a crisp pollen-bed edge (~0.86 R) instead of the rim; the upper limit must then
        # still reach the rim plus 0.04 R of smooth paper: 1 / 0.86 * 1.04 = 1.21, so 1.30 leaves a margin.
        'refine_search_rho': [0.90, 1.30],
        'refine_n_rays': 720,
    },
    'segmentation': {
        'coarse_R_px': 200,              # features computed on a resampled copy where R = 200 px (features only)
        'feature_sigma_coarse_px': 1.5,  # texture = local s.d. of L*
        'bg_texture_max': 4.0,           # background (paper / empty glass floor) is smooth ...
        'bg_chroma_max': 12.0,           # ... near-neutral ...
        'bg_lightness_min': 55.0,        # ... and bright
        'rim_zone_rho': 0.89,            # r / R_outer >= 0.89 is the dish wall seen in perspective
        'fine_sigma_R': 0.0025,          # full-resolution boundary refinement scale
        'refine_depth_R': 0.03,          # refinement may move the bed edge inward by at most 0.03 R
        'coarse_morph_radius': 2,        # coarse px: closes pinholes / removes one-pixel bridges
        'floor_margin_R': 0.08,          # wider band next to exposed dish floor (bed thins, glass shows through)
        'floor_min_component_R': 0.01,   # exposed-floor specks smaller than pi * (0.01 R)^2 are ignored
        'rim_glare_rho': 0.85,           # bed pixels at rho >= 0.85 are in the band (glare from the glass wall)
        'boundary_band_R': 0.02,         # band along the bed edge (mixed / low-confidence pixels)
        'shadow_se_radius_R': 0.0075,    # black top-hat element: fills narrow crevices, not whole loads
        'shadow_depth_L': 15.0,          # black top-hat depth in L* above which a pixel is a crevice shadow
        'void_se_radius_R': 0.02,        # stored feature only: depth of wider dark voids (never a class)
    },
    'distribution': {
        # fixed CIELAB histogram; every 8-bit sRGB colour falls inside these edges (tested)
        'L_edges': [0, 100, 10],         # start, stop, step
        'a_edges': [-110, 110, 10],
        'b_edges': [-110, 110, 10],
        'low_chroma_C_max': 15.0,        # descriptive "low-chroma" share: C* < 15 and L* >= 20
        'dark_L_max': 20.0,              # descriptive "dark" share: L* < 20
        'hue_min_chroma': 5.0,           # hue statistics use only pixels with C* >= 5 (hue undefined near neutral)
    },
}


def params_hash():
    return hashlib.sha256(json.dumps(PARAMS, sort_keys=True).encode()).hexdigest()[:16]
