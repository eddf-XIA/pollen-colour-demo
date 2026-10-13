# pollen-colour-demo

An image-analysis workflow for photographs of pooled honey-bee pollen loads in a glass dish:
**photo → measurement mask → colour distribution.**

- **Sections 1–3** show the method on real research photos: the workflow, a detailed QC illustration, and a
  comparison with the original (v1) method. They come from a university research project's colour-extraction
  pipeline (v2), are shown with the lab's permission, and are redacted (no sample IDs, site names, filenames,
  labels or file metadata).
- **Section 4** is a small, runnable, **synthetic-only** demo of the same core steps, with a test suite.

Colours throughout are **image-derived colour, not reflectance**, and colour states are **not plant taxa**. No
biological or ecological conclusion is drawn here.

## 1. Real-photo workflow: photo → measurement mask → colour distribution

![Three real pooled-pollen photos: dish-only photo, measured area, colour-state fingerprint](research_examples/workflow/real_photo_workflow.png)

Each row is one pooled sample, from three crop systems (apple, cranberry, pumpkin).

1. **Photo.** The dish region of the original JPEG. The sRGB profile is verified and the EXIF orientation applied.
   Everything outside the dish is shown as grey.
2. **Measurement mask.** Every pixel gets exactly one class with a reason. The measured pollen pixels are shown
   in photo colour. The rejected classes are:
   - **purple**: dish wall/rim (ρ ≥ 0.89 R);
   - **pink**: empty dish floor, region-grown inward from the wall;
   - **blue**: boundary band of mixed and glare-affected pixels;
   - **green**: narrow crevice shadows;
   - **white**: clipped pixels, or pixels in colour states excluded from the fingerprint.
3. **Colour distribution.** All measured pixels are calibrated to the in-frame ColorChecker and converted to
   CIELAB. They are then assigned to one frozen 21-state colour basis that is shared by every photo. Each bar is a
   state's share of the retained pixels; error bars are ±1.96 block-bootstrap SE.

**Limits beside each example** (shares of retained pixels):

| Example | Blue channel clipped to 0 (chroma is a lower bound) | Calibration extrapolated / out of gamut | Chart warm-patch error, held out |
|---|---|---|---|
| A, apple | 12.9% | 15.2% | 2.8 ΔE00 |
| B, cranberry | 5.8% | 6.1% | 2.7 ΔE00 |
| C, pumpkin | 22.9% | 3.1% | 2.7 ΔE00 |

- **Example C** also has 6.6% of measured pixels in the excluded near-black state.
- **Not representative.** The examples were chosen by a fixed rule: the analysed sample closest to its crop
  system's median v1 colour diversity.
- **Crop system** describes where the hive was placed. It does not identify the plants the pollen came from.

**Files:** the photo crops, overlays and fingerprint tables are in
[`research_examples/examples/`](research_examples/examples/), with
[`examples_metadata.csv`](research_examples/examples/examples_metadata.csv).

## 2. QC illustration: one repeat-capture photo in detail

The pipeline draws a 16-panel QC diagnostic for every photo it processes. The photo shown here is a **repeat
capture**: a second exposure of an already-photographed sample, taken seconds before its primary photo. It is used
only for test–retest QC. It is a deliberately hard case: a very dark sample, uneven lighting, and four automatic QC
flags.

**Centre and edge zooms (panels 7–8):** 320 × 320 px windows at native resolution. Each is shown as the original
pixels (left) and with the class overlay (right). **Measured pixels are untinted.**

![Native-resolution zooms of the dish centre and the bed edge, with class overlays](research_examples/qc_repeat_capture/qc_centre_edge_zooms.png)

**Panel 7, dish centre:** 87.1% of the window is measured, 10.8% crevice shadow and 2.1% clipped.
- **Green: narrow crevices.** They are removed by a size rule: a black top-hat on L\*. A pixel must be darker than
  its surroundings *and* lie in a gap narrower than the structuring element. Being dark alone is never a reason to
  exclude a pixel.
- **Grey: fully clipped pixels.** Every channel is at or below the chart's black patch, so calibration cannot
  measure them. Pixels with only one clipped channel stay measured and are flagged.
- **Kept as measured:** dark brown loads, pale and whitish loads, and their highlights.
- **Also kept: wide dark voids** (wider than the crevice element). They cannot be told from dark loads by size and
  contrast alone. This is a known limitation, carried as a stored feature for a pre-specified sensitivity
  analysis.

**Panel 8, bed edge:** 47.9% of the window is measured, 27.9% dish wall/rim, 10.1% boundary band and 6.7% outside
the dish. This dish has no exposed floor, so the zoom sits at its default position: 0°, at 0.89 R.
- **Purple: the dish wall/rim zone (ρ ≥ 0.89 R).** The original shows why it is excluded. The glass wall refracts
  and reflects the loads behind it, producing "ghost" pollen that is not on the dish floor.
- **Blue: the boundary band.** It covers bed pixels at ρ ≥ 0.85 R, where veiling glare from the glass raises
  lightness and lowers chroma, plus a 0.02 R band along the bed edge. The widths were set from where the
  low-chroma excess decays, not from any downstream result.
- **Far right: outside the dish**, flat grey after redaction.

**QC excerpt:** the measurement mask, rejected pixels by reason, the zooms, and raw vs calibrated colour.

![QC panel excerpt: measurement mask, rejected pixels, zooms, raw and calibrated colour](research_examples/qc_repeat_capture/qc_excerpt.png)

**Key QC notes for this photo** (from the frozen research output):
- **Mask.** 80.1% of the candidate bed is measured. The boundary band takes 8.8%, crevice shadow 8.5% and fully
  clipped pixels 2.6%. The rim fit RMS is 0.7 px.
- **Automatic flags** (outliers against same-year photos):
  - dark pixels: 16.2% of measured, against a median of 2.3%;
  - lightness gradient across the dish: 14.3 L\* per R, against 7.7;
  - two low-chroma metrics.
  - The low-chroma pixels are almost all in the dish wall and floor: 98.4% fall in those classes. The lighting
    gradient is reported, not corrected.
- **Clipping and calibration.**
  - Blue = 0 in 21.0% of measured pixels.
  - Chart warm-patch error is 7.5 ΔE00 raw and 3.8 calibrated (held out).
  - Calibration is extrapolated beyond the chart for 35.5% of measured pixels.
- **Agreement with the primary photo of the same sample.**
  - ΔE00 between median colours is 1.65 raw and 0.40 calibrated.
  - Histogram overlap is 0.76 raw and 0.75 calibrated.
  - The measured share of the bed is 80.1% here and 80.5% in the primary photo.
  - So calibration brings the medians together but does not improve every measure.

**Files:** [the full 16-panel diagnostic](research_examples/qc_repeat_capture/qc_panel_full.png) and
[all QC notes and how the files were made](research_examples/qc_repeat_capture/QC_NOTES.md).

## 3. v1 → v2 method comparison (concise)

| Stage | v1 (original) | v2 (current) |
|---|---|---|
| Dish and pollen mask | Hough circle shrunk by 9%; pixels with HSV V > 180 & S < 60 treated as background anywhere | Refined outer rim; empty floor region-grown from the wall; boundary band; every pixel gets one class and a reason code |
| Dark and grey pixels | Crevice shadows kept, forming "near-black" colours; dish and edge pixels can form grey/taupe colours | Narrow crevices removed by a size rule; nothing excluded for being dark, grey or pale |
| Colour space and distance | Clusters in sRGB; colours merged at a distance of 25 in OpenCV's 8-bit Lab encoding (lightness scaled ×2.55, so not a CIE ΔE) | sRGB → linear RGB → XYZ → CIELAB (D65, 2°); distances in CIEDE2000 |
| Calibration | Delivered (Levels-stretched) JPEG values used as is | Per-image tone map plus a per-session 3 × 3 matrix fitted to the in-frame ColorChecker; raw values kept alongside |
| Pixels used | 200,000-pixel random subsample | All measured pixels at full resolution |
| Colour summary | Per photo: k = 15 KMeans clusters merged into 8–10 colours | One frozen colour-state basis shared by all photos; shares with block-bootstrap SE |

![The same three photos under v1 and v2: v1 mask by v2 class, v2-only pixels, and both colour summaries](research_examples/comparison/v1_vs_v2_same_photos.png)

**Observed on the three example photos** (numbers in
[`v1_vs_v2_same_photos.csv`](research_examples/comparison/v1_vs_v2_same_photos.csv)):
- **v1 mask.** Of v1's mask pixels, 3.4–6.0% fall in v2's dish wall/floor classes and 10.6–12.1% in its boundary
  band.
- **v1 grey/taupe colours.** 46–59% of their pixels fall in v2's dish wall/floor classes.
- **v1 near-black colours.** 22–58% of their pixels are v2 crevice shadow or clipped; the rest stay measured.
- **v1 HSV rule.** It removed at most 0.08% of the pixels v2 measures, so its effect on pale pollen is negligible
  in these photos.
- **Calibration.** Chart warm-patch error falls from 5.7–5.8 to 2.7–2.8 ΔE00 (held out).

**Caveats:**
- **No accuracy claim.** These are observed mask differences labelled with v2's own classes. Those classes are not
  ground truth, so no accuracy or "improvement" claim is made for either version on real photos.
- **Not like for like.** The two colour summaries use different definitions and are not directly comparable.
- **v1 was internally consistent.** It used its distance scale consistently: v2 changes the definition, not a
  numerical error.

## 4. Runnable synthetic demo

The code in `src/` reimplements the v2 core steps (dish geometry, pixel classification, CIELAB conversion) on
**synthetic, computer-generated images**. It exports fixed-bin CIELAB colour distributions, colour metrics and an
overview figure.
- It contains no real photographs and no research data.
- None of its numbers are research results, and the synthetic colours represent no plant taxon or sample.
- It **omits** the research pipeline's ColorChecker calibration, QC panels and replicate checks. Nothing in
  sections 1–3 was made with it.

### Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[test]"

python -m pollen_colour_demo --out demo_outputs     # about 10 s; writes the files listed below
pytest                                              # about 20 s, 57 tests
```

Without installing, run `pip install -r requirements.txt`, then `PYTHONPATH=src python -m pollen_colour_demo`.
`pytest` finds `src/` on its own through `pyproject.toml`.

### Outputs (`demo_outputs/`)

Every table row carries `data_origin = synthetic_demo`.

| File | Contents |
|---|---|
| `colour_metrics.csv` | One row per scene. **Dish geometry:** rim centre, radius and fit RMS. **Pixel classes:** the fraction in each class. **Measured-pixel colour (CIELAB):** medians and 10th/90th percentiles of L\* and C\*, circular mean hue, low-chroma and dark fractions. **Histogram:** occupied bins, Shannon entropy and exp(entropy). |
| `colour_distribution_lab_histogram.csv` | The colour distribution of each scene: every non-empty bin of a fixed 10 × 22 × 22 CIELAB grid (L\* 0–100, a\* and b\* −110 to 110, step 10), with its count and fraction. |
| `synthetic_truth_check.csv` | Segmentation compared with the generator's per-pixel ground truth. This is possible only because the images are synthetic. |
| `demo_figure.png` | One row per scene: the input, the pixel-class map, the a\*b\* distribution and the L\* distribution. |
| `run_info.json` | Package version, parameter hash, all parameters, scene specifications and library versions. |
| `inputs/`, `label_maps/` | The generated scenes and class maps as lossless PNG. Regenerated on every run, so they are git-ignored. |

![Synthetic demo figure](demo_outputs/demo_figure.png)

### How it works

- **Colour.** 8-bit sRGB is decoded through the exact IEC 61966-2-1 transfer function, then converted to linear
  RGB, XYZ and CIELAB (D65, 2°) with scikit-image. Colour differences are CIEDE2000. Colour is never measured in
  sRGB or OpenCV's 8-bit "Lab".
- **Segmentation is separate from colour measurement.** The measurement mask is decided by geometry and image
  evidence. Clustering never decides it.
  - The empty dish floor is region-grown inward from the wall through smooth, near-neutral, bright pixels. This
    runs first on a coarse copy, then at full resolution, but only near the coarse edge.
  - A boundary band (with a stored reason) removes mixed pixels at the bed edge, next to exposed floor, and near
    the glass wall.
  - Narrow crevices are removed by a morphological size criterion: a black top-hat on L\*.
- **No pixel is excluded just for being dark, grey or desaturated.** The synthetic palette includes a near-neutral
  grey load and a large dark load, and the tests check that both are kept.
- **No resampling of measured values.** Colour comes only from the full-resolution decoded array. Coarse masks
  are mapped back nearest-neighbour.
- **Fixed parameters.** All spatial parameters scale with the detected dish radius R, and the histogram bins are
  fixed in advance (`src/pollen_colour_demo/params.py`).

### What the tests check (`tests/`, 57 tests)

- **Colour conversions.**
  - The sRGB decoding table matches IEC 61966-2-1, and the 8-bit round trip is exact.
  - Known D65 Lab values are reproduced, and the neutral axis stays neutral.
  - CIEDE2000 matches the Sharma, Wu & Dalal (2005) test pairs.
  - If colour-science is installed, results agree with it as an independent check.
- **Histogram.** Every 8-bit sRGB colour falls inside the fixed bins, the bins don't depend on the data, and
  counts and fractions are consistent.
- **Dish.**
  - The outer rim is recovered within 1% of R and 5 px of the centre.
  - It is also recovered when refinement starts from the pollen-bed edge (about 0.86 R).
  - Blank paper raises an error.
- **Segmentation (against ground truth).**
  - No paper, wall or floor pixel is measured (≤ 0.1%), and the empty floor is excluded.
  - Load interiors of every colour are kept (≥ 85% each, spread ≤ 10 points). The composition of the measured
    pixels matches the visible composition within 2 points.
  - A uniform very dark bed stays measured.
  - The measurement mask is stable under ±20–25% exposure changes (Jaccard ≥ 0.90).
  - Measured values are exactly the decoded pixels.
- **End to end.** All files are produced, every row is labelled synthetic, and the tables agree with each other.
  Two runs give byte-identical tables, and no local file paths appear in the outputs.

### Demo limitations

- **Synthetic scenes only.** The test thresholds describe the expected behaviour on these generated scenes. They
  are **not** accuracy estimates for real photographs.
- **No colour calibration.** The values are the raw CIELAB of the synthetic sRGB pixels.
- **Dark-on-dark crevices (scene `synthetic_04`).** Here the dark loads are only about 14 L\* above the crevice
  layer, less than the 15 L\* crevice-depth threshold. Crevices between dark loads therefore stay measured: about
  62% of narrow-crevice pixels are excluded, against 81–95% in the other scenes, and measured purity is 0.96
  rather than ≥ 0.97. A size-and-contrast rule can't tell these crevices from dark pollen. Wider voids are not
  removed in any scene, by design. These values are reported in `synthetic_truth_check.csv` and are not asserted.
- **Small radius bias.** The detected rim radius is about 0.6–0.7% larger than the generated radius in every
  scene, which is within the 1% test tolerance.
- **Bin-dependent statistics.** Shannon entropy and occupied-bin counts depend on the chosen bin size. They are
  descriptive only.

## Background

The colour-conversion, dish-geometry and pixel-classification code is adapted from the colour-extraction pipeline
(v2) of a university research project on honey-bee pollen colour. It was developed with AI coding assistance
(Claude Code).

This repository adds:
- the synthetic scene generator with per-pixel ground truth;
- the fixed-bin distribution export;
- the figure;
- a standalone test suite;
- packaging.

The real-photo material in `research_examples/` comes from the frozen research outputs; nothing there was
re-extracted or re-tuned. See [`research_examples/README.md`](research_examples/README.md).

## Tested environment

Windows 11, Python 3.13.5, numpy 2.2.6, scipy 1.16.3, scikit-image 0.26.0, OpenCV 4.13.0, Pillow 11.3.0,
pandas 2.3.3, matplotlib 3.10.6, pytest 9.1.1 (optional: colour-science 0.4.7). The lower version bounds in
`pyproject.toml` have not been tested.

## License

**No license has been chosen.** All rights are reserved, and no permission to reuse is granted. The real photos
and figures in `research_examples/` are shown with the lab's permission for this portfolio only.
