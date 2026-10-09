# RAW lens identification and correction behavior

Researched 2026-10-09 using first-party product documentation. This is behavioral research, not copied correction coefficients or implementation code. No Adobe app assets, lens profiles, or GPL/LGPL implementations were inspected.

## What automatic detection means

Lens identity and a correction model are different facts. Knowing the lens name does not supply the numerical distortion, vignetting, or chromatic-aberration correction. The documented Lightroom/Affinity workflows combine metadata-based identification with a supported correction source; they do not promise to recover every lens's distortion from an arbitrary scene. The following product facts support this distinction; this paragraph is our inference rather than a vendor algorithm specification.

## Lightroom and Camera Raw

- Lightroom desktop selects a matching profile using metadata including camera model, focal length, aperture, and focus distance. Its Optics panel offers lens corrections, separate chromatic-aberration removal, and independent profile-strength adjustments for distortion and vignetting. If automatic matching fails, users can choose a Make, Model, and Profile manually. The available profiles depend on RAW versus non-RAW input. Some cameras instead have automatic built-in support, displayed as “Built-in Lens Profile Applied,” with an information control. [Lightroom desktop editing documentation](https://helpx.adobe.com/lightroom/desktop/edit-photos/edit-photos.html).
- Adobe documents separate profiles for RAW and non-RAW files, and warns that applying a profile to a JPEG can produce unexpected results because processing varies with how that file was created. Its built-in-support guidance is camera dependent; it does not establish a universal behavior for Sony RAWs. [Adobe lens-profile support](https://helpx.adobe.com/x-productkb/multi/lens-profile-support.html).
- Adobe explicitly described an automatic, opcode-based built-in correction route for RAW files in Camera Raw 9.12. This is evidence that a bundled selectable profile and file-supplied correction instructions are distinct routes, not evidence that all Sony MakerNote tables use DNG opcodes. [Camera Raw 9.12 release announcement](https://blog.adobe.com/en/publish/2017/07/18/camera-raw-9-12-now-available).
- Adobe's supported-lenses table, updated 2026-09-29, lists **Sony E 70–350mm F4.5–6.3 G OSS**, as well as E 18–135mm, E 35mm F1.8 OSS, and E PZ 16–50mm OSS II. Some profiles are RAW only. These rows establish advertised profile availability, not successful automatic matching or numerical output on our actual files. [Supported lenses](https://helpx.adobe.com/camera-raw/desktop/dng-and-file-formats/supported-lenses.html).

## Affinity Photo 2 desktop

- Develop Persona automatically applies a database lens profile when possible and enabled by Develop Assistant settings. Users can disable that profile, search/select another one manually, or inspect a Detected category when automatic selection is disabled. Separate manual controls adjust distortion, perspective, rotation, and scale; the latter can remove transparent borders. Photo Persona also provides camera/lens/focal-length selection in its Lens Correction filter. [Lens Correction documentation](https://affinity.help/photo2/en-US.lproj/pages/Adjustments/adjustment_lensCorrection.html).
- The Lens panel distinguishes automatic-selection success from failure. Warnings can indicate unsuccessful matching, insufficient metadata, or corrections already applied. A manually selected profile clears Assistant-related indicators. Even with a suitable profile, some adjustments can be disabled for non-linear RAW, non-RAW input, Apple's RAW engine, insufficient focal-length/aperture metadata, or a previously corrected image. It also exposes chromatic-aberration reduction, defringe, and lens-vignette removal as separate adjustments. [Lens panel documentation](https://affinity.help/photo2/en-US.lproj/pages/Raw/raw_panelLens.html).

## Current Affinity desktop documentation

The current first-party guide, published 2026-05-28, says Affinity reads lens data from file metadata and applies automatic corrections, alongside manual distortion, rotation, chromatic-aberration, defringe, and vignette controls. This corroborates the metadata-based user workflow but does not specify the matching algorithm, correction-source precedence, or support for our exact Sony tables. [Current Affinity RAW editing guide](https://www.affinity.studio/blog/editing-raw-images-and-working-with-raw-files).

Current Help Center documentation distinguishes the Affinity and Apple Core Image RAW engines on Mac. Apple's engine supplies predetermined lens-correction/cropping behavior. Affinity's allows lens-correction overrides and preserves sensor data outside the camera-selected crop. The selected engine therefore matters when comparing results. Photo 2's exact UI labels should not be assumed to match the current app. [Current Affinity RAW development documentation](https://www.affinity.studio/help/raw-raw/).

## Our Sony α6700 case: known facts and remaining evidence

Earlier local inspection of the user's ARW established **SONY ILCE-6700**, **E 70–350mm F4.5–6.3 G OSS**, **70mm**, **f/4.5**, and Sony distortion, chromatic-aberration, and vignetting tables. The original LightCraft UI nevertheless reported no embedded lens data and DNG-only support. This observation means lens identification was available while the relevant correction decoding was absent; it does not prove the numerical meaning of those tables. The local branch now contains a guarded α6700 distortion implementation and regressions, now independently checked on E 70–350mm held-out captures; other lenses and a distributable positive E 70–350mm RAW regression remain outstanding (see [measurement summary](sony-lens-corrections.md)). See the existing [local α6700 specification](spec-sony-a6700-lens-corrections.md) and [contribution research](contribution-research-sony-lens.md) for local implementation context.

This research did **not** open the user's file in Lightroom or Affinity. It has not established which source either application chooses for that file, which corrections are applied, or whether the existing LightCraft correction numerically agrees. A camera JPEG preview is also a processed reference, not ground-truth uncorrected geometry.

## Consequences for a bounded ticket

Complete one demoable α6700 distortion path: preserve lens identity independently of correction support; show which correction is available/applied; validate the guarded model against independent geometric evidence on multiple focal lengths/lenses; ensure preview, toggle, persisted settings, and export agree. Report unsupported/malformed/crop-incompatible data honestly rather than as missing lens identity. Do not imply that distortion support also enables Sony vignetting or chromatic-aberration decoding.

Database matching, manual profile selection, general manual distortion controls, and Sony vignetting/chromatic-aberration decoding are additional user-visible paths. They should be separately scoped if desired. Equivalent user behavior does not require adopting Adobe profiles or Affinity's database, which would conflict with LightCraft's clean-room rules.
