"""
Colour distributions and descriptive metrics of the measured pixels.

The distribution is a fixed-edge CIELAB histogram (edges in params.PARAMS['distribution']), so histograms from
different images are directly comparable bin by bin and the bins never depend on the data. Shannon entropy over
these bins is a descriptive statistic of this particular binning; a different bin size gives different values.
"""
import numpy as np

from . import colorimetry as CM
from .params import PARAMS

D = PARAMS['distribution']


def bin_edges():
    return [np.arange(lo, hi + step / 2, step, dtype=float) for lo, hi, step in (D['L_edges'], D['a_edges'], D['b_edges'])]


def lab_histogram(lab):
    """Counts over the fixed (L*, a*, b*) grid; values outside the edges raise (they cannot occur for sRGB)."""
    lab = np.asarray(lab, float).reshape(-1, 3)
    edges = bin_edges()
    for j, e in enumerate(edges):
        if len(lab) and (lab[:, j].min() < e[0] - 1e-6 or lab[:, j].max() > e[-1] + 1e-6):
            raise ValueError(f'CIELAB channel {j} outside the fixed histogram edges')
    clipped = np.column_stack([np.clip(lab[:, j], e[0], e[-1]) for j, e in enumerate(edges)])
    counts, _ = np.histogramdd(clipped, bins=edges)
    return counts.astype(np.int64), edges


def histogram_long(counts, edges):
    """Non-empty bins as rows: L/a/b lower and upper edges, count, fraction."""
    idx = np.argwhere(counts > 0)
    total = counts.sum()
    rows = []
    for i, j, k in idx:
        c = int(counts[i, j, k])
        rows.append(dict(L_lo=edges[0][i], L_hi=edges[0][i + 1], a_lo=edges[1][j], a_hi=edges[1][j + 1],
                         b_lo=edges[2][k], b_hi=edges[2][k + 1], count=c, fraction=c / total))
    return rows


def shannon(counts):
    p = np.asarray(counts, float).ravel()
    p = p[p > 0] / p.sum()
    return float(-(p * np.log(p)).sum())


def circular_mean_deg(h_deg):
    h = np.radians(np.asarray(h_deg, float))
    if h.size == 0:
        return float('nan')
    return float(np.degrees(np.arctan2(np.sin(h).mean(), np.cos(h).mean())) % 360)


def colour_metrics(lab):
    """Descriptive metrics of a set of CIELAB pixel values (N x 3)."""
    lab = np.asarray(lab, float).reshape(-1, 3)
    n = len(lab)
    out = dict(n_measured_px=int(n))
    if n == 0:
        return out
    L = lab[:, 0]
    C, h = CM.lab_to_lch(lab)
    for name, v in (('L', L), ('a', lab[:, 1]), ('b', lab[:, 2]), ('C', C)):
        out[f'{name}_median'] = float(np.median(v))
    for name, v in (('L', L), ('C', C)):
        out[f'{name}_p10'], out[f'{name}_p90'] = (float(x) for x in np.quantile(v, [0.1, 0.9]))
    chromatic = C >= D['hue_min_chroma']
    out['hue_circular_mean_deg'] = circular_mean_deg(h[chromatic])
    out['frac_hue_defined'] = float(chromatic.mean())
    out['frac_low_chroma'] = float(((C < D['low_chroma_C_max']) & (L >= D['dark_L_max'])).mean())
    out['frac_dark'] = float((L < D['dark_L_max']).mean())
    counts, _ = lab_histogram(lab)
    H = shannon(counts)
    out['hist_occupied_bins'] = int((counts > 0).sum())
    out['hist_shannon_nats'] = H
    out['hist_exp_shannon'] = float(np.exp(H))
    return out
