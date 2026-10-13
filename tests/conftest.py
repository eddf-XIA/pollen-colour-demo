import pytest

from pollen_colour_demo import pipeline as PL
from pollen_colour_demo import synthetic as SY


@pytest.fixture(scope='session')
def scene_runs():
    """Each demo scene generated once and measured once: {scene_id: (rgb, truth, measure() result)}."""
    out = {}
    for spec in SY.SCENES:
        rgb, truth = SY.make_scene(**spec)
        out[spec['scene_id']] = (rgb, truth, PL.measure(rgb))
    return out
