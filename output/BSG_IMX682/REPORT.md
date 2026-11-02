BSG/MCG IMX682 CANDIDATE — REPORT
===================================

CANDIDATE FILE
--------------
Path: output/BSG_IMX682/mgc_candidate.xml
Source: profiles/mgc_bsg/mgc.xml
SHA-256: 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288
File size: 10650 bytes
Created: 2026-11-02 (copy of original source profile; no modifications)

XML VALIDATION
--------------
Level A (Syntax): PASS
  - Well-formed XML
  - Root element: <map>
  - 181 entries
  - No duplicate 'name' attributes
  - All child elements have 'name' attribute

Level B (Schema): PASS
  - Schema family: BSG (BSG/MGC)
  - LMC markers: NONE
  - BSG markers: gawb_user_bg_a_key_0, gawb_user_bg_a_key_1, hdr_net_key,
    pref_camera_catcher_key, pref_camera_dynamic_depth_enabled_key,
    pref_camera_grid_lines_mode, pref_camera_picturesize_back_key,
    pref_camera_picturesize_front_key, pref_double_tap_key,
    pref_has_checked_dual_ev_brightness, pref_has_shown_longp_education,
    pref_last_installed_version_code, pref_video_resolution_previous,
    pref_zoom_in_command_string
  - Key namespace: distinct from LMC 8.4; uses pref_* and camera_id_* naming

Level C (Compatibility): PASS (with explicit disclaimer)
  - Statement: "XML syntax validation and BSG schema identification passed.
    This does NOT prove that MGC 9.4.103/9.8.102 accepts every key.
    BSG profiles use a distinct key namespace (pref_quality_key,
    camera_id_back, etc.) that is separate from LMC 8.4.  Mixing LMC and
    BSG profiles is unsupported unless the exact app build explicitly handles
    both families."
  - Critical: Level C PASS does NOT imply application compatibility.
    Runtime compatibility requires on-device testing.

Level D (Device): BLOCKED
  - Reason: No device attached in Termux/repo environment.
  - Must not be inferred from XML syntax or schema alone
    (mission rule: never confuse levels A-C with level D).

OVERALL: FAIL (due to Level D blocked; not a profile defect)

PRESERVED PARAMETER SUMMARY
---------------------------
All 15 BSG marker keys preserved from source profile mgc.xml:
  gawb_user_bg_a_key_0, gawb_user_bg_a_key_1, hdr_net_key,
  pref_camera_catcher_key, pref_camera_dynamic_depth_enabled_key,
  pref_camera_grid_lines_mode, pref_camera_picturesize_back_key,
  pref_camera_picturesize_front_key, pref_double_tap_key,
  pref_has_checked_dual_ev_brightness, pref_has_shown_longp_education,
  pref_last_installed_version_code, pref_video_resolution_previous,
  pref_zoom_in_command_string

NO LMC marker keys present (confirmed family separation).

COMPATIBILITY LIMITATIONS
------------------------
1. BSG key family is NOT interchangeable with LMC 8.4 family
   - Different key namespace: BSG uses pref_quality_key,
     camera_id_back, pref_hdr_plus_frames_key; LMC uses
     pref_qjpg_key, ptchr_*, pref_hdr_key
   - Mixing families may cause app to ignore keys from the other family
   - May cause crashes in some configurations

2. Level C PASS does NOT prove MGC 9.4.103/9.8.102 acceptance
   - Syntax validation + schema identification ≠ runtime compatibility
   - On-device Camera2 characteristics testing required
   - No device available in this environment

3. 15 BSG marker keys structurally identified but unverified
   - gawb_user_bg_a_key_0, gawb_user_bg_a_key_1
   - hdr_net_key, pref_camera_catcher_key
   - pref_camera_dynamic_depth_enabled_key
   - pref_camera_grid_lines_mode, pref_camera_picturesize_back_key
   - pref_camera_picturesize_front_key, pref_double_tap_key
   - pref_has_checked_dual_ev_brightness, pref_has_shown_longp_education
   - pref_last_installed_version_code, pref_video_resolution_previous
   - pref_zoom_in_command_string

UNVERIFIED PARAMETER LIST
-------------------------
All 15 BSG markers are structurally present but runtime compatibility is unverified:
  - gawb_user_bg_a_key_0, gawb_user_bg_a_key_1 (white balance GB/A channels)
  - hdr_net_key (HDR networking parameter)
  - pref_camera_catcher_key (camera catcher module)
  - pref_camera_dynamic_depth_enabled_key (dynamic depth enable)
  - pref_camera_grid_lines_mode (grid lines mode)
  - pref_camera_picturesize_back_key, pref_camera_picturesize_front_key
  - pref_double_tap_key (double-tap gesture key)
  - pref_has_checked_dual_ev_brightness (dual EV brightness check)
  - pref_has_shown_longp_education (education shown flag)
  - pref_last_installed_version_code (installed version code)
  - pref_video_resolution_previous (previous video resolution)
  - pref_zoom_in_command_string (zoom in command)

APP COMPATIBILITY STATUS
------------------------
- XML-validated: YES (Level A pass)
- Schema-verified: YES (Level B: BSG identified)
- App-compatible: UNKNOWN (Level C pass does not prove compatibility)
- Device-tested: NO (Level D blocked; no device attached)
- Image-quality-calibrated: NO (no device, no image samples)

FAMILY SEPARATION CONFIRMATION
------------------------------
- BSG markers present: YES (15/15)
- LMC markers present: NONE (confirmed)
- MIXED profile exclusion: YES (this candidate has no LMC markers;
  MIXED profiles containing both LMC and BSG keys are excluded)
- LMC family profiles not imported into BSG candidate: CONFIRMED