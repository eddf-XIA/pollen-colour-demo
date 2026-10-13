"""Overview figure: one row per synthetic scene (input, pixel classes, a*b* distribution, L* distribution)."""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from . import segmentation as SG  # noqa: E402

INK, MUTED, GRID = '#1f1f1f', '#5c5c5c', '#e3e3e3'
BAR = '#6b6b6b'
AB_EDGES = (np.arange(-20, 51, 10), np.arange(-20, 81, 10))   # the CSV's 10-unit a*/b* bins (display window)


def class_rgb(label):
    out = np.zeros(label.shape + (3,), np.uint8)
    for c, col in SG.CLASS_COLORS.items():
        out[label == c] = col
    return out


def crop(img, dish, m=1.04):
    H, W = img.shape[:2]
    y0, y1 = int(max(0, dish['cy'] - m * dish['R'])), int(min(H, dish['cy'] + m * dish['R']))
    x0, x1 = int(max(0, dish['cx'] - m * dish['R'])), int(min(W, dish['cx'] + m * dish['R']))
    return img[y0:y1, x0:x1]


def ab_image(lab, srgb):
    """RGBA grid over AB_EDGES: each cell shows the mean measured colour of its pixels, opacity ~ sqrt(share)."""
    ea, eb = AB_EDGES
    ia = np.digitize(lab[:, 1], ea) - 1
    ib = np.digitize(lab[:, 2], eb) - 1
    ok = (ia >= 0) & (ia < len(ea) - 1) & (ib >= 0) & (ib < len(eb) - 1)
    na, nb = len(ea) - 1, len(eb) - 1
    flat = ib[ok] * na + ia[ok]
    n = np.bincount(flat, minlength=na * nb).astype(float)
    rgba = np.ones((nb * na, 4))
    rgba[:, 3] = 0
    for ch in range(3):
        s = np.bincount(flat, weights=srgb[ok, ch].astype(float), minlength=na * nb)
        rgba[n > 0, ch] = s[n > 0] / n[n > 0] / 255.0
    share = n / max(1, len(lab))
    rgba[n > 0, 3] = np.clip(np.sqrt(share[n > 0] / share.max()), 0.15, 1)
    return rgba.reshape(nb, na, 4), float(ok.mean()) if len(lab) else float('nan')


def _style(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def make_figure(panels, path):
    n = len(panels)
    fig, axes = plt.subplots(n, 4, figsize=(13, 3.05 * n + 1.6), gridspec_kw=dict(width_ratios=[1, 1, 1.05, 1.25]))
    axes = np.atleast_2d(axes)
    titles = ['Synthetic input', 'Pixel classes', 'a*b* distribution (measured px)', 'L* distribution (measured px)']
    for i, p in enumerate(panels):
        a0, a1, a2, a3 = axes[i]
        a0.imshow(crop(p['rgb'], p['dish']))
        a1.imshow(crop(class_rgb(p['label']), p['dish']))
        for a in (a0, a1):
            a.set_xticks([]); a.set_yticks([])
            for s in a.spines.values():
                s.set_visible(False)
        mix = ', '.join(f'{k} {v:.0%}' for k, v in p['mix'].items())
        a0.set_xlabel(f"{p['scene_id']}\ngenerated mix: {mix}", fontsize=7.5, color=INK, loc='left')
        img, inside = ab_image(p['lab'], p['srgb'])
        ea, eb = AB_EDGES
        a2.set_facecolor('#f4f4f2')
        a2.imshow(img, origin='lower', extent=(ea[0], ea[-1], eb[0], eb[-1]), interpolation='nearest', aspect='auto')
        a2.set_xticks(ea[::2]); a2.set_yticks(eb[::2])
        a2.set_xlabel('a*', color=MUTED, fontsize=8); a2.set_ylabel('b*', color=MUTED, fontsize=8)
        a2.axhline(0, color=GRID, lw=0.8, zorder=0); a2.axvline(0, color=GRID, lw=0.8, zorder=0)
        a2.text(0.02, 0.97, f'{inside:.1%} of px in window', transform=a2.transAxes, va='top', fontsize=7, color=MUTED)
        _style(a2)
        w = np.full(len(p['lab']), 1.0 / max(1, len(p['lab'])))
        a3.hist(p['lab'][:, 0], bins=np.arange(0, 101, 2), weights=w, color=BAR, edgecolor='white', linewidth=0.5)
        a3.set_xlim(0, 100)
        a3.set_xlabel('L*', color=MUTED, fontsize=8); a3.set_ylabel('share of measured px', color=MUTED, fontsize=8)
        a3.grid(axis='y', color=GRID, lw=0.6); a3.set_axisbelow(True)
        a3.text(0.98, 0.95, f"n = {len(p['lab']):,} measured px\nmedian L* {np.median(p['lab'][:, 0]):.1f}",
                transform=a3.transAxes, ha='right', va='top', fontsize=7, color=MUTED, zorder=5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=GRID, alpha=0.92))
        _style(a3)
        if i == 0:
            for a, t in zip(axes[0], titles):
                a.set_title(t, fontsize=10, color=INK, loc='left')
    shown = [1, 2, 3, 6, 10, 0]
    handles = [Patch(facecolor=np.array(SG.CLASS_COLORS[c]) / 255, edgecolor=MUTED, lw=0.4,
                     label=SG.CLASS_NAMES[c].replace('_', ' ')) for c in shown]
    handles.append(Patch(facecolor='white', edgecolor=MUTED, lw=0.4, label='clipped (white / black)'))
    fig.legend(handles=handles, loc='lower center', ncol=7, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.012))
    fig.suptitle('SYNTHETIC DEMONSTRATION: computer-generated images. Not research data; no biological meaning.',
                 fontsize=12, color=INK, fontweight='bold', x=0.01, ha='left', y=0.995)
    fig.text(0.01, 0.045, 'a*b* cells: 10-unit bins as in the CSV, coloured by the mean measured sRGB of their pixels; '
             'opacity ~ sqrt(share). Values are raw (uncalibrated) CIELAB D65 of the synthetic sRGB pixels.',
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.06, 1, 0.975))
    fig.savefig(path, dpi=130, facecolor='white', metadata={'Software': None})
    plt.close(fig)
