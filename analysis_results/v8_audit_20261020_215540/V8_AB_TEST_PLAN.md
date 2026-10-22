# V8 A/B Test Plan (not executed)

1. Back up the currently active LMC config and record its exact path and SHA-256.
2. Confirm the app's actual import format; do not assume a full config is accepted as a small profile.
3. Keep baseline and candidate separate. Do not overwrite the active file.
4. Use the same Lava LXX521, rear IMX682 camera, LMC 8.4 Iris R18F1 version, lens, resolution, mode, framing, focus, and lighting.
5. Capture at least 3 baseline and 3 candidate images per scene: neutral gray/white target under controlled indoor light; daylight with highlights and shadows; textured fabric/leaves/text; indoor low light; night mode tested separately.
6. Keep original files and EXIF. Pair captures by scene and mode. Do not mix night/long-exposure images with standard-photo results.
7. Compare white balance/color cast, clipping, luminance/chroma noise, texture, halos, and consistency. Avoid claims of true MTF/distortion/color calibration without appropriate targets and controlled setup.
8. If candidate is worse or unstable, restore the backed-up baseline and verify its hash. Do not alter protected device partitions.
9. This plan is not evidence that a test has run or passed.
