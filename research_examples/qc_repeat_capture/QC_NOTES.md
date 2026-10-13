# QC illustration: a repeat-capture photo (colour extraction v2)

> **Real research photo.** It is shown with the lab's permission to illustrate the method and is not licensed for reuse.
> Image ID, sample ID, filename, the printed sample label and everything else outside the dish have been removed.

| File | Content |
|---|---|
| `qc_panel_full.png` | The complete 16-panel QC diagnostic (5600 × 4200 px) |
| `qc_excerpt.png` | Panels 5–11: measurement mask, rejected pixels, centre and edge zooms, raw vs calibrated colour |
| `qc_centre_edge_zooms.png` | Panels 7–8 alone: native-resolution zooms with and without the class overlay |

## Why this photo

- **It is a repeat capture.** This is a second, separate exposure of an already-photographed pooled sample, taken
  seconds before that sample's primary photo.
- **QC only.** Repeat captures go through the same pipeline (v2, pipeline 2.0.0) as all 48 photos. They are used
  only for test–retest QC and are never analysis units.
- **It is a hard case.** The sample is very dark, the lighting varies across the dish, and the pipeline raised
  four automatic flags on this photo (below). It shows where the mask rules work and where their known limits are.

## Reading the zooms (panels 7 and 8)

Each zoom is a 320 × 320 px window at native resolution (1 image pixel = 1 display pixel before the panel was
scaled for legibility). The left image shows the original pixels. The right image shows the same pixels with each
rejected class tinted. **Measured pixels are shown untinted, in their original colour.**

**Panel 7: dish centre.** Of the window, 87.1% is measured, 10.8% is crevice shadow and 2.1% is clipped.
- **Green (interstitial shadow):** narrow, dark gaps between loads. They are found by a size rule (black top-hat on
  L\*). A pixel is rejected when it is much darker than its surroundings *and* lies in a gap narrower than the
  structuring element. Being dark is not enough on its own.
- **Grey (outside the chart's calibrated range):** pixels with every channel at or below the ColorChecker black
  patch. Calibration cannot measure them, so they are classed as clipped. Pixels with only one clipped channel stay
  measured and are flagged.
- **Kept as measured:** dark brown loads, pale and whitish loads, and the highlights on them. No pixel is excluded
  for being dark, grey or pale.
- **Wide dark voids** (wider than the crevice element) also stay measured. They cannot be told apart from dark
  loads by size and contrast alone. This is a stated limitation, discussed below.

**Panel 8: bed edge.** The pipeline places this zoom where the bed meets the most exposed dish floor. This dish has
no exposed floor, so the zoom defaults to 0° (the right-hand side), at the 0.89 R rim-zone boundary.
Of the window, 47.9% is measured, 27.9% dish wall/rim, 10.1% boundary band, 6.7% outside the dish, 4.9% clipped
and 2.6% crevice shadow.
- **Purple (dish wall / rim zone):** everything at ρ ≥ 0.89 R, where ρ is the distance from the fitted rim centre
  and R is the outer-rim radius. The original image shows why: the glass wall refracts and reflects the loads behind
  it, which creates "ghost" pollen that is not on the dish floor.
- **Blue (boundary band):** bed pixels at ρ ≥ 0.85 R, where veiling glare from the glass wall raises lightness and
  lowers chroma, and a 0.02 R band along the bed edge. The width of each band was set from where the low-chroma
  excess decays, before any downstream result was looked at.
- **Grey patches inside the bed:** clipped dark voids, as in panel 7.
- **Far right:** outside the dish. In the original zoom this was the paper background; it is shown here as flat
  grey because everything outside the dish was redacted.

## QC notes for this photo (unchanged from the frozen research output)

- **Mask.**
  - The outer rim fits with 0.7 px RMS (R = 804 px).
  - Of the candidate pollen bed, 80.1% is measured: 1,288,030 px. The boundary band takes 8.8%, crevice shadow 8.5%
    and fully clipped pixels 2.6%.
- **Automatic QC flags.** Each is an outlier against the other photos from the same year.
  - **Dark fraction.** 16.2% of measured pixels have raw L\* < 20; the year median is 2.3%.
  - **Lightness gradient.** The plane fitted to raw L\* across the dish rises 14.3 L\* per R; the year median is 7.7.
    Raw ΔE00 is 7.0 between the left and right halves and 4.3 between inner and outer zones. The gradient combines
    illumination and composition, and it is reported, not corrected.
  - **Low-chroma fraction.** 0.2% of measured pixels are low-chroma (C\* < 15 with L\* ≥ 20); the year median is 0.03%.
  - **Low-chroma share in the mask.** 1.3% of all low-chroma pixels in the dish are measured; the year median is
    0.15%. The other 98.4% are the dish wall and floor, so the glass is excluded as intended.
- **Dark voids.**
  - Some wide black voids between loads stay measured, by design.
  - 14.0% of measured pixels are dark (L\* < 20) *and* have a void depth above the crevice-depth threshold. A stored void-depth feature
    lets a pre-specified sensitivity analysis exclude them without reprocessing.
- **Clipping.**
  - The source JPEG was Levels-stretched against the colour chart. 22.8% of measured pixels have a channel at 0
    (blue = 0 in 21.0%), and 1.6% have a channel at 255.
  - Chroma is a lower bound for pixels with blue = 0.
- **Calibration.**
  - Warm-patch error on the in-frame ColorChecker is 7.5 ΔE00 raw, 5.4 after the tone map only and 3.8 fully
    calibrated (held out from the matrix fit).
  - Calibration is extrapolated beyond the chart, or out of gamut, for 35.5% of measured pixels.
  - Calibrated values are image-derived colour, not reflectance.
- **Agreement with the primary photo of the same sample.**

  | | Raw | Calibrated |
  |---|---|---|
  | ΔE00 between the two photos' median L\*a\*b\* | 1.65 | 0.40 |
  | Overlap of fixed-bin (2-unit) L\*a\*b\* histograms (1 = identical) | 0.76 | 0.75 |

  - The measured share of the bed is 80.1% here and 80.5% in the primary photo. Crevice shadow is 8.5% and 8.7%.
  - Calibration brings the median colours together, but the full distributions overlap slightly less. Calibration
    does not improve every measure.

## How these files were made (no re-extraction)

- **Same code and data.** The panel was redrawn by the research pipeline's own QC plotting function from its frozen
  outputs. The inputs were first verified against the run manifest checksums. An unredacted redraw was then checked
  to be pixel-identical to the archived panel.
- **Display-only changes:**
  - image ID, sample ID and filename removed from the title;
  - every pixel outside the dish rim set to grey, except the ColorChecker patch grid. This removes the printed
    sample label, the chart branding and serial number, and the background;
  - the automatic-flag text no longer names the primary photo or the sample;
  - the panel is saved at twice the original resolution so its text is readable;
  - `qc_excerpt.png` and `qc_centre_edge_zooms.png` are pixel crops of the redacted panel.
- **Unchanged:** masks, colour values, metrics, QC flags and every measurement setting.
