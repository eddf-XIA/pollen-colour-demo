# Research examples: real photos

> **Not synthetic, and not licensed for reuse.** Everything in this folder comes from a university research
> project's colour-extraction pipeline (v2). The photos and figures are shown with the lab's permission to
> illustrate the method and workflow. The outputs are review-stage research outputs, not published results.

## What is here

| Folder / file | Content |
|---|---|
| `workflow/real_photo_workflow.png` | The workflow on three pooled samples (apple, cranberry, pumpkin crop systems): dish-only photo → measured area → colour-state fingerprint, with each example's measurement limits |
| `examples/` | The same three examples as separate files: dish-only photo crop, measured-area overlay and fingerprint table (CSV) for each. `examples_metadata.csv` gives crop system, collection window, sampling note and measurement limits |
| `qc_repeat_capture/` | The pipeline's 16-panel QC diagnostic for one **repeat-capture** photo, an excerpt, and the centre/edge zooms on their own. Start with `qc_repeat_capture/QC_NOTES.md` |
| `comparison/` | The original (v1) and current (v2) methods on the same three example photos: figure and numbers. The concise comparison is in section 3 of the root README |

**What the examples are and are not:**
- They are **examples, not representative** of any crop system.
- Colours are image-derived colour states, **not plant taxa** and not reflectance.
- Crop system describes where the hive was placed. It does not identify the plants the pollen came from.
- No biological, ecological or DNA comparison is shown or implied.
- They illustrate measurement and QC. They are **not** independent ground-truth accuracy validation: there are no
  pixel-level ground-truth labels for real photos, and the mask classes are image-measurement classes, not a
  botanical classification of pollen.

## Research workflow vs the runnable demo

| | Research v2 extraction (this folder) | Synthetic demo (`src/`, `demo_outputs/`) |
|---|---|---|
| Input | Real photos (JPEG, sRGB profile verified) | Generated images only |
| Dish geometry and pixel measurement/exclusion classes | Full pipeline | Same core steps, adapted |
| ColorChecker calibration (tone map + session matrix) | Yes (raw and calibrated colour kept) | **Omitted** |
| QC panels, automatic flags, replicate-photo checks, v1 comparison | Yes | **Omitted** |
| Colour summary | Frozen 21-state colour basis (fingerprints) | Fixed-bin CIELAB histograms |

The demo was not used to make anything in this folder. Every mask, colour value and fingerprint here comes from
the frozen research outputs; nothing was re-extracted or re-tuned.

## What was removed

- **Not in this folder:** sample IDs, site names, coordinates, photo filenames, label text, camera timestamps and
  file metadata.
- **In the photos and the QC panel:** everything outside the dish was replaced by grey, including the printed
  label, the colour-chart branding and serial number, and the background. The QC panel keeps the chart's patch
  grid. Its title and flag text no longer name the photo or the sample.
- **In the figures:** the review-stage title banner was cropped off. Nothing else in the figures was changed.
