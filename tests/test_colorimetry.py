"""Colour conversions against published reference values. Tolerances are stated with their reason."""
import numpy as np
import pytest

from pollen_colour_demo import colorimetry as CM


def test_srgb_decoding_lut_is_iec_61966_2_1():
    v = np.arange(256) / 255.0
    ref = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    assert np.array_equal(CM.SRGB8_TO_LINEAR, ref)
    assert CM.SRGB8_TO_LINEAR[0] == 0.0 and CM.SRGB8_TO_LINEAR[255] == 1.0
    assert np.all(np.diff(CM.SRGB8_TO_LINEAR) > 0)


def test_8bit_round_trip_is_exact():
    u8 = np.arange(256, dtype=np.uint8)
    assert np.array_equal(CM.linear_to_srgb8(CM.srgb8_to_linear(u8)), u8)


def test_lab_known_values_d65():
    # sRGB primaries / white / black under D65, 2 deg (published reference values); 0.05 = rounding of the references
    cases = {(255, 255, 255): (100.0, 0.0, 0.0), (255, 0, 0): (53.24, 80.09, 67.20), (0, 255, 0): (87.73, -86.18, 83.18),
             (0, 0, 255): (32.30, 79.19, -107.86), (0, 0, 0): (0.0, 0.0, 0.0)}
    for rgb, lab in cases.items():
        got = CM.srgb8_to_lab(np.array([rgb], np.uint8))[0]
        assert np.allclose(got, lab, atol=0.05), (rgb, got)
    grey = np.repeat(np.arange(256, dtype=np.uint8)[:, None], 3, 1)
    assert np.abs(CM.srgb8_to_lab(grey)[:, 1:]).max() < 0.01          # the neutral axis stays neutral


def test_lab_to_linear_inverts_linear_to_lab():
    rng = np.random.default_rng(0)
    lin = rng.uniform(0.01, 0.99, (5000, 3))
    assert np.allclose(CM.lab_to_linear(CM.linear_to_lab(lin)), lin, atol=1e-9)


def test_ciede2000_sharma_2005_reference_pairs():
    # Sharma, Wu & Dalal (2005), Color Res. Appl. 30(1), Table 1 test data
    pairs = [((50, 2.6772, -79.7751), (50, 0, -82.7485), 2.0425), ((50, 3.1571, -77.2803), (50, 0, -82.7485), 2.8615),
             ((50, 2.8361, -74.02), (50, 0, -82.7485), 3.4412), ((50, 0, 0), (50, -1, 2), 2.3669),
             ((50, 2.5, 0), (73, 25, -18), 27.1492)]
    for a, b, ref in pairs:
        assert abs(float(CM.delta_e00(np.array(a, float), np.array(b, float))) - ref) < 1e-4


def test_conversion_agrees_with_colour_science():
    colour = pytest.importorskip('colour')   # optional independent oracle
    rng = np.random.default_rng(0)
    u8 = rng.integers(0, 256, (20000, 3)).astype(np.uint8)
    ours = CM.srgb8_to_lab(u8)
    cs = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(u8 / 255.0),
                           colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65'])
    # two independent implementations; differences come only from matrix / white-point digits
    assert CM.delta_e00(ours, cs).max() < 0.05


def test_uint8_guard_no_silent_wrap_or_clip():
    with pytest.raises(TypeError):
        CM.srgb8_to_linear(np.array([[300, 0, 0]], np.int32))   # would wrap / clip silently if cast
    assert CM.srgb8_to_linear(np.array([[255, 128, 0]], np.uint8)).dtype == np.float64


def test_lch_hue_convention():
    C, h = CM.lab_to_lch(np.array([[50, 10, 0], [50, 0, 10], [50, -10, 0], [50, 0, -10]], float))
    assert np.allclose(C, 10) and np.allclose(h, [0, 90, 180, 270])
