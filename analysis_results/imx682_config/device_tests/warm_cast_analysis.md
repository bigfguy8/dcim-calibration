# Warm Color Cast Analysis — IMX682

## Hypothesis Status: UNVERIFIED (sensor-level warm cast is a hypothesis, not confirmed)

### Observed Data
| Source | R-G (warm cast) | R/B ratio | Conditions |
|--------|-----------------|-----------|------------|
| LMC V2 Release (3 photos) | +3.3 to +6.8 | 1.078-1.096 | Outdoor, EV ~8.0 |
| LMC V2 Release (37 batch) | +5.3 to +9.4 | 1.047-1.085 | Mixed, EV 4.9-8.9 |
| Stock camera (LavaPlayUltra) | +8.1 to +12.2 | 1.053-1.073 | Outdoor, EV ~8.3 |
| Stock camera (IMG_*) | +4.2 to +7.4 | 1.011-1.075 | Mixed |

### Possible Causes (not yet distinguished)
1. **Sensor spectral response** — IMX682 may have inherent red bias in its CFA/quantum efficiency
2. **Lens coating** — 5.43mm f/1.89 lens may transmit more red
3. **AWB algorithm** — LMC's auto AWB may not fully correct for this sensor
4. **Illuminant** — outdoor daylight in capture location may be warm (golden hour)
5. **Display rendering** — JPEG viewing on monitor may exaggerate warmth
6. **ISP processing** — MediaTek MT6878 ISP may apply warm tone curve

### Required Tests to Distinguish
1. **Neutral gray card** under D65 (6500K) illuminant — measure R-G deviation from 0
2. **Multiple illuminants** (tungsten, fluorescent, daylight, shade) — check if cast is consistent
3. **RAW capture** — bypass ISP/JPEG to isolate sensor response
4. **AWB preset comparison** — auto vs daylight vs cloudy vs tungsten
5. **Display calibration** — view on calibrated monitor to rule out display

### AWB Controls Available in LMC
- pref_awb_key: 0=auto, 1=daylight, 2=cloudy, 3=incandescent, 4=fluorescent
- cw_rg_key: manual R/G correction (0.0-1.0, lower = less red)
- cw_bg_key: manual B/G correction (if present)

### BSG GCam Consideration
- BSG 9.2.113+ supports AWB correction modules (.gawb files)
- Requires: device compatibility check, camera ID mapping, config format verification
- **Not yet verified** — do not assume switching forks will solve the issue
- Current LMC config format (`<map>` with `lib_*`/`pref_*`) is NOT compatible with BSG's format

### Conclusion
The warm cast hypothesis (sensor-level) is plausible but unverified. Further testing with neutral references and multiple illuminants is required before concluding the cast is irreducible via software tuning.
