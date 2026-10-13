import argparse

from .pipeline import run


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m pollen_colour_demo',
                                 description='Run the synthetic segmentation + colour-distribution demo.')
    ap.add_argument('--out', default='demo_outputs', help='output folder (default: demo_outputs)')
    ap.add_argument('--no-figure', action='store_true', help='skip the PNG figure')
    a = ap.parse_args(argv)
    tables = run(a.out, figure=not a.no_figure)
    m = tables['colour_metrics.csv']
    print(f'Wrote synthetic demo outputs for {len(m)} scenes to {a.out}/')
    print(m[['scene_id', 'dish_R', 'n_measured_px', 'L_median', 'C_median', 'hist_occupied_bins']].to_string(index=False))


if __name__ == '__main__':
    main()
