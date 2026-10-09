# Detect and apply validated embedded lens distortion for Sony α6700 RAWs

Published as [fork issue #1](https://github.com/ralfboltshauser/lightcraft/issues/1), label `ready-for-agent`. Original acceptance criteria retained below; implementation evidence and outstanding positive distributable-real-file regression are recorded in [the validation summary](../sony-lens-corrections.md).

## What to build

A photographer opening a supported Sony α6700 ARW should see the lens identified from the file, know which corrections LightCraft can apply, and get an independently verified distortion correction in preview and export without guessing manual values. Finish the existing experimental fork implementation rather than starting a second correction pipeline.

The reported capture is an ILCE-6700 with an E 70–350mm F4.5–6.3 G OSS at 70 mm, f/4.5. Lens identity and Sony correction tables were found in the RAW, but the original app displayed a misleading DNG-only/no-data warning. The fork now reads the signed 11-sample distortion layout and has passing synthetic probe/render/toggle/DNG tests; its actual geometric interpretation still needs held-out real-photo validation. Recognition of a lens name, presence of correction metadata, acceptance by the decoder, and application of a correction must be distinct states.

## Research basis

- [Adobe Lightroom Optics documentation](https://helpx.adobe.com/lightroom/desktop/edit-photos/edit-photos.html): automatic profile selection uses capture metadata; manual make/model/profile selection is available when matching fails. Built-in correction is reported separately. Distortion and vignetting have separate amount controls.
- [Adobe lens-profile support](https://helpx.adobe.com/x-productkb/multi/lens-profile-support.html): RAW and non-RAW profiles differ, and applying a RAW-style correction to an already processed image may produce unexpected results.
- [Affinity Photo 2 RAW development](https://affinity.help/photo2/en-US.lproj/pages/Raw/raw.html): the Develop Assistant can select installed profiles automatically; its own RAW engine and Apple Core Image RAW have different correction behavior. Auto-select therefore does not prove that Affinity interprets Sony's embedded table.
- [Affinity Lens Correction](https://affinity.help/photo2/en-US.lproj/pages/Adjustments/adjustment_lensCorrection.html) and [Lens panel](https://affinity.help/photo2/en-US.lproj/pages/Raw/raw_panelLens.html): database matching, searchable manual profile selection, independent manual controls, and explanations for insufficient metadata or previously applied corrections.
- [Adobe supported lenses](https://helpx.adobe.com/camera-raw/desktop/dng-and-file-formats/supported-lenses.html) lists the E 70–350mm G OSS; this establishes advertised availability, not the result on this actual ARW.
- LightCraft's rules permit clean-room embedded-data decoding and original measurements; they exclude copying Adobe profiles/assets or Lensfun implementation/data. A general profile database is separate work.

These sources establish product behavior, not the undocumented geometry of this Sony table. No Lightroom/Affinity comparison on the reported ARW has been performed.

## Acceptance criteria

- [ ] Show the camera and lens identity already obtainable from the RAW, preserving the distinction between unknown identity and unavailable correction. Include focal length/aperture when present; do not invent missing metadata.
- [ ] For each correction component, expose whether it is available and whether it is applied. State that the automatic distortion source is camera-embedded data. Do not enable or imply Sony vignetting or lateral-CA profile correction merely because distortion is supported. Existing image-based CA removal must remain distinct from a camera-provided CA profile.
- [ ] Explain unsupported or rejected embedded correction data accurately. Retain manual distortion/vignetting controls as the usable fallback; a checkbox or moved pixels alone must not be treated as proof of correct geometry.
- [ ] Independently establish sample positions, units, mapping direction, optical centre, crop normalization, interpolation and framing for the ILCE-6700 11-sample layout. The prototype's interpretation is a hypothesis to verify, not an oracle.
- [ ] Validate the E 70–350mm target using multiple files and focal lengths, including both zoom extremes and held-out files. Use a documented independent reference with correction known to be enabled, such as Sony correction On/Off exports or suitable calibration captures. Embedded camera JPEGs are supplementary evidence unless their correction state is established.
- [ ] Publish a reproducible measurement method and summary: dimensions, focal lengths, crop/aspect and compression variants, centre/edge/corner coverage, median and 95th-percentile pixel residuals, and observed framing. Establish and justify tolerances before evaluating held-out files. Only enable configurations supported by that evidence; clearly document exclusions and preserve other bodies' current behavior.
- [ ] Verify the complete engine path: fresh import, Optics toggle/strength and undo/redo, preview and full-size export, orientation/crop, and DNG correction preservation. The original ARW remains byte-for-byte unchanged; unsupported/malformed inputs fail safely.
- [ ] Verify an already-imported photo can gain the new correction through the established reload workflow while preserving edits, deliberate correction-off choices, and virtual copies. Reuse the upstream reload work where appropriate instead of duplicating its design; upstream merge is not required to demonstrate behavior on the fork.
- [ ] Add meaningful synthetic and distributable real-file regressions that fail without the behavior. Keep private photos/exports local; public fixtures must meet repository licensing and checksum rules. Inspect the Optics UI through the supported control channel or headless snapshots and update localized wording and the partial coverage documentation.
- [ ] Run the required project checks and report their exact outcome. The current CPU-mode CI pass and reproduced Metal denoise failures are baseline facts; do not describe them as a full GPU validation pass.

## Blocked by

None (can start immediately on the fork's existing experimental branch).

## Scope and related work

Initial delivery is independently validated α6700 embedded distortion, beginning with the reported E 70–350mm lens, and honest correction availability through the complete user workflow. A general camera/lens profile database, manual profile picker, profile import, calibration-authoring UI, Sony vignetting/CA decoding and arbitrary Sony-model support are excluded from this ticket.

Related upstream work, not parent issues or assumed completed dependencies:
- [PR #498](https://github.com/storytold/lightcraft/pull/498): exact ILCE-7RM4A embedded distortion; the fork already builds on this work. Its maintainer requires independent evidence or restricted coverage.
- [PR #571](https://github.com/storytold/lightcraft/pull/571): refresh embedded corrections through Reload from Disk while preserving settings.
- [Issue #329](https://github.com/storytold/lightcraft/issues/329): broader original lens profiles and profile generation; this ticket does not close it.
- [Experimental fork branch](https://github.com/ralfboltshauser/lightcraft/tree/codex/sony-a6700-distortion): existing implementation and validation limits.
