# Sony embedded distortion corrections

LightCraft reads the signed 16-sample distortion table in the raw image IFD (`0x7037`) of
Sony **ILCE-7RM4A (A7R IVA)** Bayer ARWs, and reads the signed 11-sample table
in **ILCE-6700 (α6700)** Bayer ARWs with **E 70–350mm F4.5–6.3 G OSS**. Other camera models are deliberately left uncorrected,
even when they contain a table with the same layout.
It converts that table into `OpcodeList3` / `WarpRectilinear`, so the existing profile correction control,
CPU/GPU optics path, EXIF orientation handling, and DNG export use the same correction.

This adds **distortion only**. Sony vignetting and lateral chromatic-aberration tables are not decoded.
The independently validated combinations are ILCE-7RM4A with the FE 24–105mm F4 G OSS or
FE 200–600mm F5.6–6.3 G OSS, and ILCE-6700 with E 70–350mm F4.5–6.3 G OSS. Linear YCbCr ARWs and non-3:2 camera crops are excluded pending validation. An aspect crop may
retain the full-frame radial normalization; the decoder does not guess that relationship. Older files that carry
only encrypted correction metadata, different table lengths, and rejected tables remain uncorrected.
The camera's distortion Off setting does not erase its table. Newly imported photos use LightCraft's existing
embedded-profile default (enabled); the profile correction control can disable or adjust it.

## Clean-room evidence

The [ExifTool EXIF tag-name documentation](https://exiftool.org/TagNames/EXIF.html) identifies
`0x7037` as 17 signed 16-bit integers. The first value is the count, 16, followed by radial samples.
No external photo decoder implementation or Adobe lens profile was consulted.
Sony Imaging Edge Edit 4.1 was used only as a black-box reference on local scratch copies.

The observed inverse mapping, with radius `r` normalized to the default crop's half diagonal, is:

```
f(r) = 1 + interpolate(table, r) / 16384
source = center + (output - center) * zoom * f(r)
zoom = 1 / max(f(r)) over radii on the rectangular output boundary
```

The border radii range from the shorter half edge / half diagonal to 1. Table knots span 0 through 1.
Linear interpolation approximates the observed map closely; we do not claim to reproduce Sony's
internal interpolator. A fixed-size weighted least-squares fit expresses source radius as
`r * (k0 + k1*r² + k2*r⁴ + k3*r⁶)`. The fit is rejected if radial error exceeds 0.0005 of the
half diagonal (about 0.43 px at a 1440 px 3:2 preview), or the mapping folds. Table values are bounded
and the input must have precisely the supported signed-short layout. Crop offset and normalization
are converted into DNG's active-area coordinate system before creating the opcode. The standard
`DefaultCropOrigin` / `DefaultCropSize` take precedence over Sony crop tags: on the tested A7R IVA
files the former start at raw x=32 and the latter at x=0. The standard origin aligns with Sony
exports; the old precedence shifted content by eight pixels in a 2376-pixel-wide export.

The main raw-IFD table is important: the similarly named MakerNote table has different values and
must not be substituted into this formula. Main raw-IFD and SR2SubIFD values agreed in the test files.

## Validation

At 2376×1584, independent SIFT correspondences between Sony distortion On and Off TIFF exports gave:

| Lens / focal length | Median residual | 95th percentile | Maximum matched radius |
|---|---:|---:|---:|
| FE 200–600 / 200 mm | 0.043 px | 0.191 px | 0.97 half diagonals |
| FE 200–600 / 600 mm | 0.055 px | 0.231 px | 0.95 half diagonals |

These use the fixed 16384 scale and automatic border framing, not fitted per-image scale or zoom.
A median translation below 0.004 px was removed from the residuals. Correspondences do not cover
all pixels; these are geometric feature residuals, not photometric equality or a worst-case guarantee.
Across 20 sampled RAWs (16 at 24–105 mm, four at 200–600 mm), the polynomial's maximum deviation
from the interpolated file table was below 0.12 px at 1440 px. That measures approximation error,
not agreement with an independent renderer. Camera JPEG and Apple Core Image comparisons support
the wide-lens interpretation but are weaker evidence than same-renderer On/Off pairs.

Actual LightCraft exports after crop normalization were also compared directly with Sony's corrected
TIFFs. At 2376 px wide, median / 95th-percentile feature residuals were 0.35 / 1.04 px at 24 mm,
0.15 / 0.40 px at 200 mm, and 0.13 / 0.56 px at 600 mm (median translation below 0.024 px).
The uncorrected medians at 200 and 600 mm were 8.63 and 10.82 px respectively. Different colour,
sharpening, and demosaicing affect feature localization; these are geometry checks, not colour parity.
An isolated desktop run on Apple M1 Metal detected the profile, rendered without GPU fallback or
warnings, and exposed the existing Optics controls. Existing library edits are not reset: once the
source has loaded, enable lens corrections if they were previously disabled.

Tests cover signedness/length rejection, zero and malformed tables, independent 600 mm reference
geometry, barrel framing, offset crop normalization, both TIFF byte orders, header/full consistency,
and preservation through DNG export. No private photographs or reference TIFFs are committed.

## Camera coverage and regression boundary

The model check is exact: `ILCE-7RM4` (A7R IV without the A suffix), `ILCE-7M3`, unknown/missing
model names, and every other model remain unsupported by this distortion decoder. Matching tag
numbers and table lengths do not establish the scale, interpolation or crop normalization on another
body. Support can expand after independent geometry validation; do not add model-name prefix matching.

The original nine Sony samples listed by `cargo xtask corpus --download` were downloaded from its
CC0 URLs. The manifest now also includes CC0 samples 4822 (A7R IVA / 24–105 mm) and 3989
(A9 II / 200–600 mm), with their SHA-256 hashes recorded alongside the URLs. All eleven files
are checked with `sony_embedded_distortion_is_limited_to_validated_models`:

| Camera | Corpus samples | Raw-IFD table observed | Expected correction |
|---|---|---|---|
| ILCE-7RM4A | Compressed (4822) | 16 samples | One distortion warp |
| ILCE-9M2 | Compressed (3989) | 16 samples | None |
| ILCE-7M3 | Compressed, uncompressed | 16 samples | None |
| ILCE-7M4 | 14-bit, lossless L/M/S | 11 samples in the 14-bit file; 16 in L/M/S | None |
| ILCE-7RM2 | 12-bit uncompressed | 16 samples | None |
| DSC-RX100 | One | No raw-IFD table | None |
| DSC-RX100M3 | One | 11 samples | None |

These are **model-boundary regression checks, not new geometric validation of those models**. In particular,
refusing the A7 III tables resolves the unverified corner warp identified in review. The lossless M/S
files are linear YCbCr and remain excluded independently of the model check. Header and full decode
must agree for every sample. Synthetic tests also verify both TIFF byte orders, exact model matching,
standard crop precedence, and that DNG export preserves an accepted warp without adding one to rejected
models. The existing independent Sony geometry tests continue to cover the enabled A7R IVA path.
Re-exporting the 24, 200 and 600 mm reference files after the model restriction produced byte-identical
corrected PNGs to the earlier validated exports. Isolated headless app checks showed the A7R IVA profile
controls present and the A7 III profile controls absent, with no notices and completed RAW renders.

Before enabling another body, compare corrected and uncorrected renders against independent references
across multiple lenses/focal lengths and photographs with features near the edges and corners. Record
residuals and spatial coverage, and check crop/aspect and compression variants. Embedded JPEGs are
useful when the camera actually applied distortion correction; an Off JPEG cannot certify an On warp.
Prefer same-renderer Sony On/Off exports when the camera setting or geometry is ambiguous. Table-fit
error alone only checks our polynomial approximation, not whether the table's interpretation is correct.

## α6700 / E 70–350mm validation (2026-10-09)

[Fork issue #1](https://github.com/ralfboltshauser/lightcraft/issues/1) restricts the eleven-sample
mapping to the exact `ILCE-6700` and `E 70-350mm F4.5-6.3 G OSS` names. The raw-IFD contains
17 signed words: count 11, eleven useful samples, then padding. The mapping uses evenly spaced
radii from the default-crop centre to its corner, scale 16384, linear interpolation and the inverse
output-to-source direction described above. The crop offset is included before orientation. No
geometry coefficients, per-file translation, scaling or homography were adjusted against holdouts.
Six independent camera-JPEG-to-uncorrected-RAW landmark pairs are committed in the engine regression;
they distinguish direction, scale, centre and framing from merely fitting the table to itself.

The local test material comprised 115 private α6700 RAWs: 96 E 70–350mm, ten E 18–135mm,
seven E PZ 16–50mm OSS II and two E 35mm F1.8 OSS. Pilot comparisons informed the supported-lens
boundary. The E 18–135mm at 18mm had an edge 95th percentile of approximately 6.7 pixels, exceeding
the chosen limit; it and the other lenses remain excluded. E 35mm camera correction was Off, so
its JPEG cannot certify an On correction. Lens identity alone never enables an unvalidated lens.

Before examining the holdout residuals, the plan fixed limits at a 1600-pixel long edge: median ≤1px,
95th percentile ≤3px, and outer-radius (`r > 0.7`) 95th percentile ≤3px. These are engineering
acceptance limits, allowing feature-localisation differences between independently demosaiced,
sharpened and resized camera JPEGs and LightCraft output while discriminating the observed 8–22px
uncorrected displacements. They are not a guarantee at full resolution. A scorable image must have
at least 50 matches, ten outer-radius matches and a maximum matched radius ≥0.85 half diagonals.
Features in all corners of every photograph were not required; sparse coverage is reported below.

Holdouts were selected independently of residuals: SHA-256-sort the unused basenames within focal
bins 70mm, 71–149mm, 150–299mm and 300–350mm, then take three from each. Pilot files were excluded.
Of twelve captures, **eleven passed, none failed, one was inconclusive**. The 135mm photograph had
maximum matched radius 0.556 and no outer-radius features. The scorable results were:

| Metric at 1600px long edge | Range across eleven holdouts |
|---|---:|
| Median direct feature residual | 0.236–0.658px |
| 95th percentile direct residual | 0.667–2.359px |
| Outer-radius 95th percentile | 0.558–1.573px |

Spatial coverage (centre `r < 0.3`; corner columns count outer-radius features in each quadrant):

| Holdout | Focal mm | Centre | Top left | Top right | Bottom left | Bottom right |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 70 | 73 | 4 | 5 | 59 | 36 |
| 2 | 70 | 168 | 0 | 52 | 22 | 18 |
| 3 | 70 | 33 | 8 | 2 | 36 | 0 |
| 4 | 128 | 12 | 3 | 0 | 5 | 24 |
| 5 (inconclusive) | 135 | 104 | 0 | 0 | 0 | 0 |
| 6 | 105 | 658 | 5 | 0 | 264 | 314 |
| 7 | 172 | 118 | 0 | 0 | 77 | 56 |
| 8 | 244 | 186 | 0 | 0 | 22 | 15 |
| 9 | 193 | 208 | 0 | 0 | 7 | 4 |
| 10 | 350 | 1033 | 320 | 42 | 31 | 232 |
| 11 | 350 | 41 | 0 | 0 | 35 | 37 |
| 12 | 350 | 295 | 45 | 34 | 102 | 148 |

The batch covers all four corner quadrants in aggregate, with weaker upper-corner coverage at
intermediate focal lengths. Quadrant counts are not observations at the extreme corner pixel.

All captures tested lossless-compressed Bayer RAW, sensor 6656×4608, default crop origin (26,20),
size 6192×4128 and native 3:2 framing; both landscape and portrait EXIF orientation were exercised.
Other compression, reduced linear YCbCr and in-camera aspect crops have not been validated for
this camera/lens combination. The α6700 guard requires lossless compression (TIFF Compression 7);
linear RGB and non-3:2 crops are rejected. The A7R IVA path is unchanged. The camera JPEG reference
is accepted only when the file reports distortion correction Auto/On. This establishes geometric
agreement with the camera's embedded JPEG, not equivalence to Lightroom, Affinity or Imaging Edge.

### Reproduce locally

Build `lightcraft-cli` in release mode, install ExifTool, and use a separate Python 3.11+ analysis venv with
NumPy and OpenCV. Run `python docs/showcase/verify-sony-lens.py --cli target/release/lightcraft-cli
--out target/lens-check capture.ARW ...`. The tool explicitly toggles correction off/on, extracts
and orients the camera JPEG, and measures direct SIFT correspondences after resizing to the actual
render dimensions. A loose 40px RANSAC gate filters descriptor mismatches; its fitted homography
is never applied to measured coordinates. It reports centre and quadrant outer-radius coverage,
and checks input SHA-256 before/after. Clear other geometry edits in a scratch session first.
An exit code of zero means no scorable failures; inspect inconclusive counts separately. Private
filenames, hashes, images and measurement output stay under ignored `target/`.

### Native-app and persistence checks

An isolated library created by the old app was reopened with this build. Reload acquired distortion
without resetting an edited virtual copy (exposure +0.7, lens correction off). Undo/redo, explicit off
followed by reload, and reopening the library preserved their states. Preview 1600×1067, full-size
6192×4128 and DNG exports completed. Resizing the full render to preview dimensions gave median
0.150px and 95th percentile 0.532px across 1844 direct correspondences. Reimported DNG retained the
same warp planes, centre and radius. Native headless screenshots showed identified camera/lens,
applied distortion, unavailable vignetting/CA profiles, independent manual controls and no notices.
All original RAW hashes were unchanged; only scratch copies/library files were written.

The UI and `photo.inspect` distinguish accepted/application state from decoder diagnosis. Reload
refreshes source diagnostics as well as lens opcodes; edited settings remain intact. Sony vignetting
and CA metadata presence is reported without pretending those components are decoded. Catalog
format 4 protects the added operation and diagnostic metadata from older builds silently dropping them.

Synthetic fixtures and measured landmarks are distributable. Two CC0 real α6700 RAWs from
[raw.pixls.us](https://raw.pixls.us/) (6735 compressed, 6736 lossless-compressed) are added to the
checksum-pinned corpus manifest. Both use E 16–55mm F2.8 G: the regression checks probe/full agreement,
recognised component tables and an explicit unvalidated-lens diagnosis with no warp. This fails
without the lens restriction. The site's 4:3 label for 6736 describes the sensor dimensions; its
actual default crop is 6192×4128 (3:2). A distributable **positive** E 70–350mm real-file regression
is still missing; positive real-file coverage remains private, and issue #1 remains open for that
follow-up. No private photographs, proprietary reference exports or external profile data are
committed.

## Earlier fork baseline validation (2026-10-09, commit 218e6b4)

`LIGHTCRAFT_GPU_BACKEND=off CRAFT_FONTS_DIR=../craft-fonts cargo xtask ci` passed all eight
steps: formatting, workspace clippy, optional HEIF checks, workspace tests, parity,
layering, assets and WASM. Both new α6700 synthetic regressions passed.

With the default Metal backend, workspace CI failed two existing GPU denoise tests:
`nn::tests::the_gpu_gives_what_the_reference_gives` and
`nn::tests::a_runner_serves_many_tiles_from_many_threads`. Both failures reproduced
with `cargo test -p lightcraft-gpu --features denoise --lib nn::tests -- --test-threads=1`
on Apple M2 Max. GPU denoise source was not changed. CPU-mode success does not establish
Metal denoise correctness or α6700 real-photo geometry fidelity.

## Current implementation checks (2026-10-09)

`LIGHTCRAFT_GPU_BACKEND=off CRAFT_FONTS_DIR=../craft-fonts cargo xtask ci` passed all eight
steps after the implementation and review fixes: fmt, workspace Clippy, optional HEIF,
workspace tests, parity, layering, assets and WASM. The new lossless synthetic Sony engine
regressions and both public α6700 corpus cases passed. Release app and CLI builds and engine/UI
type checks passed. Python verification-tool syntax was checked without generating committed caches.

Latest native fresh-import E2E additionally checked explicit source diagnoses and the public
unvalidated E 16–55mm sample, along with toggle/reload/undo/redo, preview/DNG exports and unchanged
RAW hashes. Refreshing the legacy library's diagnostics preserved both photos' complete develop
settings and supported metadata undo/redo. Comparing the latest preview with the earlier validated
preview gave 6995 direct correspondences, median 0px and p95 0.00058px; minor pixel differences did
not change measured geometry. Native-app tests used isolated scratch libraries and no user-preference
writes. Private screenshots and media remain local.

The previously reproduced Metal-denoise failures above remain a baseline limitation; no full
Metal CI success is claimed. A positive public E 70–350mm RAW regression is still outstanding.
