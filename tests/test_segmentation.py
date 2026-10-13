"""
Pixel classification against synthetic ground truth.

Criteria are the expected behaviour of the method (what it must and must not do), carried over from the research
pipeline's synthetic validation. Scenes 01-03 are the main test scenes. Scene 04 (only brown and dark loads) is a
documented operating limit for two criteria: its dark loads are only ~14 L* above the crevice layer, less than the
crevice-depth threshold, so dark-on-dark crevices cannot be told from dark pollen and stay measured. Its values are
reported in synthetic_truth_check.csv rather than asserted.
"""
import numpy as np
import pytest

from pollen_colour_demo import colorimetry as CM
from pollen_colour_demo import pipeline as PL
from pollen_colour_demo import segmentation as SG
from pollen_colour_demo import synthetic as SY
from pollen_colour_demo.params import PARAMS

ALL = [s['scene_id'] for s in SY.SCENES]
MAIN = ['synthetic_01', 'synthetic_02', 'synthetic_03']


def check(scene_runs, sid):
    rgb, truth, r = scene_runs[sid]
    return PL.truth_check(r['seg']['label'], r['dish'], truth, r['seg']['shadow_se_radius_px'])


@pytest.mark.parametrize('sid', ALL)
def test_every_pixel_has_exactly_one_known_class(scene_runs, sid):
    rgb, _, r = scene_runs[sid]
    label = r['seg']['label']
    assert label.shape == rgb.shape[:2] and label.dtype == np.uint8
    assert set(np.unique(label)) <= set(SG.CLASS_NAMES)
    reasons = r['seg']['band_reason_crop'][r['seg']['cls_crop'] == SG.BED_BOUNDARY_BAND]
    assert reasons.size and set(np.unique(reasons)) <= {1, 2, 3}      # every band pixel carries its reason


@pytest.mark.parametrize('sid', ALL)
def test_no_background_is_measured(scene_runs, sid):
    c = check(scene_runs, sid)
    assert c['measured_frac_background'] <= 0.001                    # no paper / wall / floor pixel measured
    if np.isfinite(c['floor_not_measured']):
        assert c['floor_not_measured'] >= 0.999                       # the empty floor crescent is excluded


@pytest.mark.parametrize('sid', ALL)
def test_grey_and_dark_loads_are_not_removed(scene_runs, sid):
    # no darkness / greyness rule: load interiors of every colour are kept, with no colour-dependent loss
    c = check(scene_runs, sid)
    names = scene_runs[sid][1]['names']
    for n in names:
        assert c[f'retention_{n}'] >= 0.85, n
    assert c['retention_spread'] <= 0.10


@pytest.mark.parametrize('sid', ALL)
def test_segmentation_does_not_shift_composition(scene_runs, sid):
    # share of each generated colour among measured load pixels vs among all visible load pixels
    c = check(scene_runs, sid)
    for n in scene_runs[sid][1]['names']:
        assert abs(c[f'share_measured_{n}'] - c[f'share_true_{n}']) <= 0.02, n


@pytest.mark.parametrize('sid', MAIN)
def test_measured_pixels_are_load_pixels(scene_runs, sid):
    assert check(scene_runs, sid)['measured_purity_load'] >= 0.97     # remainder: anti-aliased load edges


@pytest.mark.parametrize('sid', MAIN)
def test_narrow_crevices_are_excluded(scene_runs, sid):
    assert check(scene_runs, sid)['narrow_crevice_not_measured'] >= 0.80


def test_scene_04_limit_is_what_the_docs_say():
    # the documented reason for treating scene 04 as an operating limit must stay true
    dark_L, gap_L = SY.COLOURS['dark'][0][0], SY.GAP_LAB[0]
    assert dark_L - gap_L < PARAMS['segmentation']['shadow_depth_L']


def test_measured_values_are_the_decoded_pixels(scene_runs):
    rgb, _, r = scene_runs['synthetic_01']
    seg = r['seg']
    y0, _, x0, _ = seg['box']
    ys, xs = np.nonzero(seg['cls_crop'] == SG.MEASURED)
    assert np.array_equal(r['srgb'], rgb[ys + y0, xs + x0])            # never resampled
    assert np.allclose(r['lab'], CM.srgb8_to_lab(r['srgb']), atol=1e-12)


@pytest.mark.parametrize('factor', [0.8, 1.25])
def test_exposure_change_keeps_the_mask(scene_runs, factor):
    rgb, truth, r = scene_runs['synthetic_01']
    rgb2 = CM.linear_to_srgb8(CM.srgb8_to_linear(rgb) * factor)       # global exposure change, same dish
    lab2 = SG.classify(rgb2, r['dish'])['label']
    a, b = r['seg']['label'] == SG.MEASURED, lab2 == SG.MEASURED
    assert (a & b).sum() / (a | b).sum() >= 0.90                      # Jaccard of the measurement masks
    assert np.isin(truth['gt'][b], [0, 1, 2]).mean() <= 0.001


def test_uniform_dark_bed_stays_measured():
    # a flat, very dark load filling the bed (no crevices) is pollen, not shadow: nothing excludes it by darkness
    rgb, truth = SY.make_scene(seed=7, crescent_deg=None, coverage=0.0, mix={'dark': 1.0})
    bed = truth['bed_region']
    lin = CM.srgb8_to_linear(rgb)
    lin[bed] = CM.lab_to_linear((15, 3, 5))
    rgb = CM.linear_to_srgb8(lin)
    label = SG.classify(rgb, truth['dish'])['label']
    # the only exclusions allowed are geometric: the boundary band (here up to 0.08 R in from the empty floor
    # ring at 0.86-0.89 R, i.e. to ~0.78 R); never shadow / clipping / background
    assert set(np.unique(label[bed])) <= {SG.BED_BOUNDARY_BAND, SG.MEASURED}
    assert (label[bed & (truth['rho'] < 0.75)] == SG.MEASURED).mean() >= 0.99
