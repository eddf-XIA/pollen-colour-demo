"""End-to-end run: files, consistency between tables, reproducibility, synthetic labelling, no path leakage."""
import json
import os

import numpy as np
import pandas as pd
import pytest

from pollen_colour_demo import io as IO
from pollen_colour_demo import pipeline as PL
from pollen_colour_demo import segmentation as SG
from pollen_colour_demo import synthetic as SY

TABLES = ('colour_metrics.csv', 'colour_distribution_lab_histogram.csv', 'synthetic_truth_check.csv')


@pytest.fixture(scope='module')
def two_runs(tmp_path_factory):
    a, b = tmp_path_factory.mktemp('run_a'), tmp_path_factory.mktemp('run_b')
    PL.run(str(a), figure=True)
    PL.run(str(b), figure=False)
    return a, b


def test_expected_files(two_runs):
    a, _ = two_runs
    for f in TABLES + ('demo_figure.png', 'run_info.json', 'OUTPUTS_ARE_SYNTHETIC.md'):
        assert (a / f).is_file(), f
    for s in SY.SCENES:
        assert (a / 'inputs' / f"{s['scene_id']}.png").is_file()
        assert (a / 'label_maps' / f"{s['scene_id']}_labels.png").is_file()


def test_every_row_is_labelled_synthetic(two_runs):
    a, _ = two_runs
    for f in TABLES:
        d = pd.read_csv(a / f)
        assert (d['data_origin'] == PL.DATA_ORIGIN).all(), f
        assert set(d['scene_id']) == {s['scene_id'] for s in SY.SCENES}


def test_tables_are_mutually_consistent(two_runs):
    a, _ = two_runs
    m = pd.read_csv(a / 'colour_metrics.csv').set_index('scene_id')
    h = pd.read_csv(a / 'colour_distribution_lab_histogram.csv')
    for sid, g in h.groupby('scene_id'):
        assert g['count'].sum() == m.loc[sid, 'n_measured_px']
        assert abs(g['fraction'].sum() - 1) < 1e-4                    # CSV floats carry 6 significant digits
        assert len(g) == m.loc[sid, 'hist_occupied_bins']
    fr = m[[c for c in m.columns if c.startswith('frac_') and c[5:] in SG.CLASS_NAMES.values()]]
    assert np.allclose(fr.sum(axis=1), 1, atol=1e-5)
    assert np.allclose(m['frac_measured'] * m['n_dish_px'], m['n_measured_px'], rtol=1e-5)


def test_label_maps_match_classes(two_runs):
    a, _ = two_runs
    for s in SY.SCENES:
        lab = IO.load_rgb(a / 'label_maps' / f"{s['scene_id']}_labels.png")[..., 0]
        img = IO.load_rgb(a / 'inputs' / f"{s['scene_id']}.png")
        assert lab.shape == img.shape[:2]
        assert set(np.unique(lab)) <= set(SG.CLASS_NAMES)


def test_outputs_are_reproducible(two_runs):
    a, b = two_runs
    for f in TABLES + ('run_info.json',):
        assert (a / f).read_bytes() == (b / f).read_bytes(), f
    for s in SY.SCENES:
        for sub, suffix in (('inputs', ''), ('label_maps', '_labels')):
            p = f"{s['scene_id']}{suffix}.png"
            assert np.array_equal(IO.load_rgb(a / sub / p), IO.load_rgb(b / sub / p)), p


def test_no_local_paths_in_outputs(two_runs):
    a, _ = two_runs
    needles = [str(a), os.path.expanduser('~'), ':\\', 'C:/', '/home/', '/Users/']
    for f in TABLES + ('run_info.json', 'OUTPUTS_ARE_SYNTHETIC.md'):
        text = (a / f).read_text(encoding='utf-8')
        for n in needles:
            assert n not in text, (f, n)
    info = json.loads((a / 'run_info.json').read_text(encoding='utf-8'))
    assert info['data_origin'] == PL.DATA_ORIGIN
