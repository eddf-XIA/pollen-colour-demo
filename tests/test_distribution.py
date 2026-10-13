"""Fixed-edge CIELAB histogram and descriptive metrics."""
import numpy as np
import pytest

from pollen_colour_demo import colorimetry as CM
from pollen_colour_demo import distribution as DS


def test_every_srgb_colour_falls_inside_the_fixed_edges():
    v = np.array(sorted(set(range(0, 256, 5)) | {255}), np.uint8)   # includes every gamut corner (0 / 255)
    grid = np.stack(np.meshgrid(v, v, v, indexing='ij'), -1).reshape(-1, 3)
    lab = CM.srgb8_to_lab(grid)
    counts, _ = DS.lab_histogram(lab)                                 # raises if anything falls outside
    assert counts.sum() == len(grid)


def test_edges_are_fixed_and_independent_of_data():
    a = DS.lab_histogram(np.array([[50, 0, 0]], float))[1]
    b = DS.lab_histogram(np.array([[90, 60, 70], [10, -40, -80]], float))[1]
    assert all(np.array_equal(x, y) for x, y in zip(a, b))
    assert [len(e) - 1 for e in a] == [10, 22, 22]


def test_out_of_range_values_raise():
    with pytest.raises(ValueError):
        DS.lab_histogram(np.array([[50, 150, 0]], float))


def test_histogram_long_counts_and_fractions():
    rng = np.random.default_rng(3)
    lab = np.column_stack([rng.uniform(0, 100, 5000), rng.uniform(-50, 50, 5000), rng.uniform(-50, 80, 5000)])
    counts, edges = DS.lab_histogram(lab)
    rows = DS.histogram_long(counts, edges)
    assert sum(r['count'] for r in rows) == 5000
    assert abs(sum(r['fraction'] for r in rows) - 1) < 1e-12
    r = rows[0]
    inside = ((lab[:, 0] >= r['L_lo']) & (lab[:, 0] < r['L_hi']) & (lab[:, 1] >= r['a_lo']) & (lab[:, 1] < r['a_hi'])
              & (lab[:, 2] >= r['b_lo']) & (lab[:, 2] < r['b_hi']))
    assert inside.sum() == r['count']


def test_shannon_reference_cases():
    assert DS.shannon([7]) == 0.0
    assert abs(DS.shannon([5, 5, 5, 5]) - np.log(4)) < 1e-12
    assert abs(DS.shannon([1, 0, 1]) - np.log(2)) < 1e-12              # empty bins are ignored


def test_circular_hue_mean_wraps():
    assert abs((DS.circular_mean_deg([350, 10]) + 180) % 360 - 180) < 1e-9
    assert abs(DS.circular_mean_deg([80, 100]) - 90) < 1e-9


def test_colour_metrics_on_known_values():
    lab = np.array([[60, 0, 40]] * 70 + [[15, 2, 3]] * 20 + [[55, 1, -2]] * 10, float)
    m = DS.colour_metrics(lab)
    assert m['n_measured_px'] == 100
    assert m['L_median'] == 60 and m['b_median'] == 40
    assert abs(m['frac_dark'] - 0.20) < 1e-12                            # L* < 20
    assert abs(m['frac_low_chroma'] - 0.10) < 1e-12                      # C* < 15 and L* >= 20
    assert abs(m['hue_circular_mean_deg'] - 90) < 1e-9                   # only C* >= 5 pixels (the 70 at h = 90)
    assert m['hist_occupied_bins'] == 3
