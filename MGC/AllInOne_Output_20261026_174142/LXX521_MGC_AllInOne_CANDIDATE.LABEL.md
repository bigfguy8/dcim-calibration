CANDIDATE LABEL — LXX521_MGC_AllInOne_CANDIDATE.xml
======================================================
STATUS      : UNCHANGED NATIVE-STATE RESTORE CANDIDATE (NOT a tuned profile, NOT a crash fix)
TARGET APP  : com.android.MGC_9_4_103  (versionName 9.4.103.650360311.25, versionCode 67635286)
SOURCE      : $HOME/storage/shared/Download/MGC_CONFIG/9.4.103/mgc.xml
SOURCE SHA256: 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288
THIS SHA256  : <filled by validator>
RELATIONSHIP : byte-identical copy of the verified native configuration
               (diff is empty; SHA-256 equals the native source)

WHY UNCHANGED
-------------
1. The front-camera crash (NullPointerException at
   com.a.loadConfinesExposureISO -> android.util.Range.getUpper()) is a
   code-level null-deref. The native MGC configuration contains NO
   exposure / ISO / sensitivity / confinement / AE-confinement key
   (verified: 181 entries, 0 matching exposure|iso|sensitive|confin|ae_).
   No supported config control demonstrably affects that code path.
2. 9.8.102 V0 (the only other locally available candidate) was inspected:
   its com.a.loadConfinesExposureISO() has the SAME unguarded
   Range.getUpper() call structure (3 getUpper + 1 if-nez in both),
   i.e. no null-check was added. It is therefore NOT a proven fix and is
   not recommended as the primary build.
3. Rule: "Do not use MGC configuration to bypass an internal Java
   exception unless a supported control demonstrably affects that code
   path." No such control exists here.

PRESERVATION
------------
- All 181 native entries preserved verbatim (front, rear, HDR/HDR+,
  AWB/colour gawb_user_* / c_shad_map_*, video, image sizes, routing).
- Front/rear routing kept: active_cam_id_front_key=1,
  active_cam_id_back_key=0.
- Rear-camera settings left unmodified.
- pref_camera_picturesize_front_key and _back_key remain empty exactly as
  in the native source (not invented values).

DO NOT interpret this file as:
  * a validated, newly tuned "all-in-one" profile, or
  * a fix for the front-camera crash.
It is a faithful restore of the app's current native state so the user can
re-import a known-good baseline while the crash is pursued at the
build/code level.

DEPLOYMENT (manual, user-initiated only — NOT performed by this project)
-------------------------------------------------------------------------
  To import: copy to the MGC export path and use MGC's import-config
  feature. The project did NOT import, deploy, or run any camera session.
