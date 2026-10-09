## Problem Statement

A photographer importing Sony α6700 RAW files can see the correct lens name but cannot apply the camera's embedded lens corrections. The Optics panel reports that no lens data is embedded, even though the inspected ARW contains Sony distortion, vignetting, and chromatic-aberration tables. This confuses identification of the lens with support for its correction data.

The observed photo uses an ILCE-6700 and E 70–350mm F4.5–6.3 G OSS at 70mm, f/4.5. Its plain raw-IFD distortion table declares 11 meaningful samples. Open PR #498 supports only independently validated A7R IVA files with 16 samples; it does not solve this case.

## Solution

Enable accurate, non-destructive embedded distortion correction for independently validated α6700 RAW configurations through the existing Optics controls. Explain unsupported correction data accurately, and keep vignetting and lateral chromatic aberration explicitly unsupported until independently verified. Preserve originals and existing edits.

Treat this as a focused extension of the Sony work in #498, rather than a competing general Sony decoder or lens-profile database. Support boundaries must follow measured geometry, not table presence alone.

## User Stories

1. As an α6700 photographer, I want LightCraft to identify the lens recorded in my RAW file, so that I can confirm which equipment produced the image.
2. As an α6700 photographer, I want supported embedded distortion data to be detected, so that I do not have to guess manual correction values.
3. As an α6700 photographer, I want the camera's per-image correction to be used, so that the correction matches the recorded shooting conditions.
4. As a photographer, I want corrected geometry to agree with an independent camera-rendered reference, so that enabling correction improves the image reliably.
5. As a photographer, I want Enable Lens Corrections to control the supported correction, so that I can choose the intended rendering.
6. As a photographer, I want to adjust distortion correction strength, so that I can tune the result deliberately.
7. As a photographer, I want correction changes to participate in undo and redo, so that I can experiment safely.
8. As a photographer, I want my original ARW to remain untouched, so that my capture is preserved.
9. As a photographer, I want preview and export geometry to agree, so that the exported image matches my editing decisions.
10. As a photographer, I want correction to respect crop offsets and orientation, so that the image is not displaced or warped around the wrong centre.
11. As a photographer, I want corrected framing to avoid unintended empty borders, so that the image remains usable.
12. As a photographer, I want already-imported photos to gain supported correction data through the existing reload workflow, so that I need not delete and reimport them.
13. As a photographer, I want refreshing source metadata to preserve my existing edits, so that added decoder support does not reset my work.
14. As a photographer, I want unsupported tables to produce an accurate explanation, so that I can distinguish missing data from missing software support.
15. As a photographer, I want unsupported correction controls to remain unavailable, so that enabled sliders do not falsely imply a correction is applied.
16. As a photographer, I want unsupported camera models and capture variants to remain uncorrected, so that an unverified interpretation does not distort my photos.
17. As a photographer, I want malformed metadata to be handled without a crash, so that one damaged file cannot interrupt my library session.
18. As an agent or CLI user, I want correction to use the same engine controls as the desktop app, so that automation produces consistent results.
19. As a photographer exporting DNG, I want supported correction information to survive the existing export path, so that the correction is preserved as documented.
20. As a maintainer, I want public, reproducible validation and explicit coverage limits, so that I can review new camera support confidently.
21. As a contributor, I want to reuse the existing Sony correction work, so that this contribution advances supported coverage without duplicating the architecture.
22. As a photographer, I want my private photographs to stay local during validation, so that contributing evidence does not disclose my images or metadata.

## Implementation Decisions

- Extend the Sony RAW reader's embedded-distortion support, preferably building on #498 once its integration state is established. Recheck upstream before implementation or publication.
- Convert accepted plain raw-IFD signed correction tables into the existing WarpRectilinear / EmbeddedLens path. Reuse the engine, CPU/GPU optics pipeline, command system, and DNG export behavior rather than introducing a second correction system.
- Gate support by independently validated camera, table layout, lens/capture configurations, crop/aspect, and compression variants. The initial candidate is exact ILCE-6700 Bayer ARW with an 11-sample table. No general Sony support is implied.
- Independently establish table units, radial sample positions, direction of mapping, interpolation, framing, optical centre, and crop normalization. The prototype's 1/16384 interpretation and natural cubic interpolation are hypotheses supported by one RAW/JPEG comparison, not settled specifications.
- Distinguish polynomial approximation error from agreement with an independent renderer. Bound both input handling and accepted geometric error; reject implausible or folding mappings.
- Keep coordinates normalized so thumbnail, preview, full-resolution export, orientation, and crop agree.
- Preserve the existing profile toggle and strength controls. Determine availability separately for distortion and vignetting; detecting distortion must not enable an unsupported brightness correction.
- Replace the misleading DNG-only warning with wording that distinguishes unsupported embedded corrections from absent lens identification. Follow the existing localization conventions.
- Use the established source-metadata refresh workflow for previously imported files. Coordinate with #571; do not duplicate its catalog migration or silently reset user settings.
- Invalidate affected rendered caches according to existing cache-version conventions when decoder behavior changes.
- Do not add a new catalog schema or public API solely for table decoding. Any integration dependency on #571's schema change must be documented separately.
- Use clean-room pure Rust and original measurements or public specifications. Do not copy external RAW decoder implementations, Adobe assets/profiles, or Lensfun data.
- Update the partial optics coverage tracker and roadmap with the actual supported configurations; do not mark broad Sony lens correction complete.

## Testing Decisions

- **Proposed primary seam, pending user confirmation:** exercise the existing engine file-probe → import/render/export path. Assert externally visible correction availability, corrected geometry, preserved edits, and exported output rather than helper functions or particular coefficient arrays.
- Prefer the existing embedded-correction integration tests that check probe/decode agreement, engine lens availability, rendered results, and DNG preservation. Use the RW2 tests and #498's Sony tests as prior art.
- Establish an independently measured geometry oracle using Sony correction On/Off exports where possible. Camera JPEGs are supplementary evidence when correction is known to be enabled; an Off JPEG cannot certify an On mapping.
- Validate multiple photographs and focal lengths, with features near the edges and corners, across every configuration proposed for support. Report median and 95th-percentile residuals, output dimensions, spatial coverage, and the supported lens/capture range. Numerical acceptance thresholds must be established from the independent evidence before enabling support.
- Include held-out photographs not used to choose the mapping or fit parameters.
- Verify both header-only probing and full decoding expose the same accepted lens data, and that native preview and full-resolution export agree within documented tolerances.
- Verify fresh import and existing-library reload behavior, including preservation of edited settings, deliberate correction-off choices, and virtual copies, using the existing reload seam and #571's tests.
- Verify correction toggle/strength behavior, CPU/GPU consistency through existing optics coverage, orientation/crop handling, framing, and DNG preservation.
- Add negative cases for unvalidated models, unsupported table lengths/types, truncated data, invalid counts/values, non-native aspect crops, and unsupported linear YCbCr variants. Unsupported input must remain uncorrected without a panic.
- Keep synthetic fixtures small. Use public CC0 corpus sources with pinned checksums for distributable real-file regression tests; keep private photos and reference exports local.
- Verify Optics control availability and warning text through the existing control channel or headless snapshot, inspect the rendered result, and check performance.
- Require the project gate `cargo xtask ci` before committing. A passing targeted test alone is insufficient.

## Out of Scope

- Sony vignetting and lateral chromatic-aberration decoding until separately validated.
- A lens-profile database, Lensfun integration, manual profile selection, or calibration UI.
- Broad support for other Sony cameras, encrypted-only metadata, other table layouts, or unvalidated capture variants.
- Camera colour calibration, tone matching, denoising, and unrelated RAW decoder or GPU fixes.
- Publishing private photographs or copying commercial assets and correction profiles.
- Merging #498 or #571, or claiming this specification closes the broader issue #329.

## Further Notes

- [PR #498](https://github.com/storytold/lightcraft/pull/498) is the existing Sony embedded-distortion proposal. Its [maintainer review](https://github.com/storytold/lightcraft/pull/498#issuecomment-6084452062) requires independent validation across additional bodies or restriction to validated models.
- [PR #571](https://github.com/storytold/lightcraft/pull/571) addresses metadata refresh for previously imported photos.
- [Issue #329](https://github.com/storytold/lightcraft/issues/329) covers broader lens profiles; this spec addresses a narrower embedded-data gap.
- Follow the [project contribution rules](https://github.com/storytold/lightcraft/blob/main/AGENTS.md). No separate CONTRIBUTING document or PR template was found during the research.
- The fork extension is uninstalled. The α6700 regression failed against the original PR #498 decoder; validation of the extended decoder is recorded separately from the earlier prototype. A single 207-landmark RAW/JPEG comparison supports further investigation but does not establish general α6700 coverage. Broader geometry validation remains outstanding. The full eight-step CI gate passed in CPU mode; default Metal CI has two reproduced GPU denoise failures (see `docs/sony-lens-corrections.md`).
- The configured tracker is now GitHub Issues on `ralfboltshauser/lightcraft`, with the default triage labels. This specification has not yet been published as an issue. Upstream labels are unchanged.
