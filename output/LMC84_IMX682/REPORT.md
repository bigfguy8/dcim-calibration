LMC 8.4 IMX682 CANDIDATE — REPORT
===================================

CANDIDATE FILE
--------------
Path: output/LMC84_IMX682/llmc84_actioncam_candidate.xml
Source: profiles/lmc84/LXX521_IMX682_ActionCam.xml
SHA-256: 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360
File size: 1767 bytes
Created: 2026-11-02 (copy of original source profile; no modifications)

XML VALIDATION
--------------
Level A (Syntax): PASS
  - Well-formed XML
  - Root element: <map>
  - 27 entries
  - No duplicate 'name' attributes
  - All child elements have 'name' attribute

Level B (Schema): PASS
  - Schema family: LMC (LMC 8.4)
  - LMC markers: frame_count_b_photo_0, pref_config_nickname_key,
    pref_qjpg_key, ptchr_chroma_denoise_0, ptchr_contrast_0,
    ptchr_luma_denoise_0, ptchr_saturation_0, ptchr_sharp_outline_0,
    ptchr_sharp_radius_small_0, ptchr_sharpness_0
  - BSG markers: NONE
  - Key namespace: LMC 8.4 on MT6878/IMX682 uses pref_qjpg_key,
    frame_count_b_photo_0, ptchr_* markers

Level C (Compatibility): PASS (with explicit disclaimer)
  - Statement: "XML syntax validation and LMC schema identification passed.
    This does NOT prove that LMC 8.4 on MT6878/IMX682 accepts every key.
    Some keys (see UNSUPPORTED_LMC_KEYS) are known not to be part of the
    valid parameter space for this device.  Runtime compatibility requires
    on-device testing; syntax validation alone is insufficient."
  - Critical: Level C PASS does NOT imply application compatibility.
    Runtime compatibility requires on-device testing.

Level D (Device): BLOCKED
  - Reason: No device attached in Termux/repo environment.
  - Must not be inferred from XML syntax or schema alone
    (mission rule: never confuse levels A-C with level D).

OVERALL: FAIL (due to Level D blocked; not a profile defect)

PRESERVED PARAMETER SUMMARY
---------------------------
All 10 LMC marker keys preserved from source profile:
  frame_count_b_photo_0, pref_config_nickname_key, pref_qjpg_key,
  ptchr_chroma_denoise_0, ptchr_contrast_0, ptchr_luma_denoise_0,
  ptchr_saturation_0, ptchr_sharp_outline_0, ptchr_sharp_radius_small_0,
  ptchr_sharpness_0

NO BSG marker keys present (confirmed family separation).

COMPATIBILITY LIMITATIONS
------------------------
1. LMC 8.4 key family is NOT interchangeable with BSG/MGC family
   - Different key namespace: LMC uses pref_qjpg_key, ptchr_*,
     pref_hdr_key; BSG uses pref_quality_key, camera_id_back,
     pref_hdr_plus_frames_key
   - Mixing families may cause app to ignore keys from the other family
   - May cause crashes in some configurations

2. Level C PASS does NOT prove LMC 8.4 on MT6878/IMX682 acceptance
   - Syntax validation + schema identification ≠ runtime compatibility
   - Some keys known not to be part of the valid parameter space for this
     device/SOC combination (see UNSUPPORTED_LMC_KEYS)
   - On-device Camera2 characteristics testing required

3. 10 LMC marker keys structurally identified but unverified
   - frame_count_b_photo_0 (frame count for photo mode)
   - pref_config_nickname_key (profile nickname)
   - pref_qjpg_key (JPEG quality key)
   - ptchr_chroma_denoise_0 (chrominance denoise strength)
   - ptchr_contrast_0 (contrast parameter)
   - ptchr_luma_denoise_0 (luminance denoise strength)
   - ptchr_saturation_0 (saturation parameter)
   - ptchr_sharp_outline_0 (sharpness outline)
   - ptchr_sharp_radius_small_0 (sharpness radius small)
   - ptchr_sharpness_0 (sharpness strength)

UNVERIFIED PARAMETER LIST
-------------------------
All 10 LMC markers are structurally present but runtime compatibility is unverified:
  - frame_count_b_photo_0 (frame count for photo mode)
  - pref_config_nickname_key (profile nickname/label)
  - pref_qjpg_key (JPEG quality setting)
  - ptchr_chroma_denoise_0 (chroma denoise strength)
  - ptchr_contrast_0 (contrast control)
  - ptchr_luma_denoise_0 (luminance denoise control)
  - ptchr_saturation_0 (saturation control)
  - ptchr_sharp_outline_0 (sharpness outline control)
  - ptchr_sharp_radius_small_0 (sharpness radius small)
  - ptchr_sharpness_0 (sharpness control)

APP COMPATIBILITY STATUS
------------------------
- XML-validated: YES (Level A pass)
- Schema-verified: YES (Level B: LMC identified)
- App-compatible: UNKNOWN (Level C pass does not prove compatibility)
- Device-tested: NO (Level D blocked; no device attached)
- Image-quality-calibrated: NO (no device, no image samples)

FAMILY SEPARATION CONFIRMATION
------------------------------
- LMC markers present: YES (10/10)
- BSG markers present: NONE (confirmed)
- MIXED profile exclusion: YES (this candidate has no BSG markers;
  MIXED profiles containing both LMC and BSG keys are excluded)
- BSG family profiles not imported into LMC candidate: CONFIRMED