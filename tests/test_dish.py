"""Dish geometry on synthetic scenes with known rim circles."""
import numpy as np
import pytest

from pollen_colour_demo import colorimetry as CM
from pollen_colour_demo import dish as DI
from pollen_colour_demo import synthetic as SY

IDS = [s['scene_id'] for s in SY.SCENES]


@pytest.mark.parametrize('sid', IDS)
def test_outer_rim_recovered(scene_runs, sid):
    _, truth, r = scene_runs[sid]
    d, T = r['dish'], truth['dish']
    assert abs(d['R'] - T['R']) / T['R'] < 0.01                       # outer rim radius within 1%
    assert np.hypot(d['cx'] - T['cx'], d['cy'] - T['cy']) < 5          # centre within 5 px
    assert d['rim_rays_used'] >= 0.5 * d['rim_rays_total']


@pytest.mark.parametrize('sid', IDS)
def test_refinement_recovers_rim_when_hough_locks_onto_bed_edge(scene_runs, sid):
    # Hough can lock onto a crisp pollen-bed edge (~0.86 R) instead of the rim; the refinement window
    # (params refine_search_rho) must still reach the outer rim from there.
    rgb, truth, _ = scene_runs[sid]
    T = truth['dish']
    d = DI.refine_outer_rim(rgb, T['cx'], T['cy'], 0.86 * T['R'])
    assert abs(d['R'] - T['R']) / T['R'] < 0.01


def test_blank_paper_has_no_dish():
    paper = np.broadcast_to(CM.linear_to_srgb8(CM.lab_to_linear(SY.PAPER_LAB)), (600, 600, 3)).copy()
    with pytest.raises(DI.DishError):
        DI.detect_dish(paper)
