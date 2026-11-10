# DCIM Calibration — Final Static Audit

- Project: `/data/data/com.termux/files/home/dcim_calibration`
- Audit time (UTC): `2026-10-20T19:40:04.860334+00:00`
- Mode: **read-only static audit**
- Project scripts executed: **No**
- Source files modified: **No**

## 1. Summary

| Check | Result |
|---|---:|
| Files inventoried | 581 |
| Python scripts | 73 |
| XML files | 77 |
| JSON files | 55 |
| Markdown files | 52 |
| Candidate profile XMLs | 77 |
| Duplicate SHA-256 groups | 86 |
| Python syntax failures | 0 |
| XML parse failures | 0 |
| JSON parse failures | 0 |
| Unreadable files | 0 |

## 2. File counts by extension

| Extension | Count |
|---|---:|
| `.jpg` | 207 |
| `.xml` | 77 |
| `.py` | 73 |
| `.json` | 55 |
| `.md` | 52 |
| `.png` | 44 |
| `.txt` | 23 |
| `.csv` | 20 |
| `.log` | 12 |
| `.bak` | 7 |
| `.mp4` | 6 |
| `.pdf` | 4 |
| `.sh` | 1 |

## 3. Python syntax and entry points

| Script | Lines | Syntax | Main guard | Functions |
|---|---:|---|---|---|
| `adb_capture_helper.py` | 168 | PASS | Yes | run_adb (L21), log (L28), check_phone (L32), create_batch_dir (L41), pull_photos (L50), delete_phone_photos (L69), extract_exif_summary (L77), main (L128) |
| `analysis_results/dcim_chart_audit/analyze_dcim.py` | 263 | PASS | Yes | find_images (L20), file_hash (L28), get_exif (L31), exif_val (L45), compute_ev (L51), analyze_image (L59), main (L185) |
| `analysis_results/dcim_chart_audit/analyze_exif.py` | 110 | PASS | Yes | find_images (L12), file_hash (L20), get_exif (L23), exif_val (L37), main (L43) |
| `analysis_results/dcim_chart_audit/analyze_opencv.py` | 197 | PASS | Yes | find_images (L16), file_hash (L24), load_and_downscale (L27), analyze_image (L39), main (L127) |
| `analysis_results/dcim_chart_audit/generate_plots.py` | 109 | PASS | No/unclear | — |
| `analysis_results/final_calibration/final_report/check_new_photos.py` | 28 | PASS | No/unclear | — |
| `analysis_results/final_calibration/final_report/fix_lmc_stock.py` | 58 | PASS | No/unclear | classify_source (L12) |
| `analysis_results/final_calibration/final_report/generate_final_report.py` | 183 | PASS | No/unclear | get_keys (L19) |
| `analysis_results/final_calibration/final_report/video_focus_analysis.py` | 184 | PASS | No/unclear | analyze_video (L19) |
| `analysis_results/final_calibration/final_report/video_focus_summary.py` | 35 | PASS | No/unclear | — |
| `analysis_results/final_calibration/latest_captures/analyze_latest.py` | 22 | PASS | No/unclear | — |
| `analysis_results/final_calibration/latest_captures/analyze_portrait.py` | 22 | PASS | No/unclear | — |
| `analysis_results/final_calibration/latest_captures/check_latest.py` | 26 | PASS | No/unclear | — |
| `analysis_results/final_calibration/latest_samples/analyze_samples.py` | 45 | PASS | No/unclear | — |
| `analysis_results/final_calibration/monitor_calibration/analyze_all_monitor.py` | 362 | PASS | Yes | find_images (L24), file_hash (L32), get_exif (L35), exif_val (L49), compute_ev (L55), detect_moire (L63), analyze_image (L83), main (L218) |
| `analysis_results/final_calibration/monitor_calibration/analyze_monitor_baseline.py` | 350 | PASS | Yes | find_images (L23), file_hash (L31), get_exif (L34), exif_val (L48), compute_ev (L54), detect_moire (L62), analyze_image (L87), main (L227) |
| `analysis_results/final_calibration/monitor_calibration/generate_monitor_charts.py` | 245 | PASS | No/unclear | save_png (L17) |
| `analysis_results/final_calibration/monitor_calibration/pull_new.py` | 37 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/ab_analyze.py` | 267 | PASS | Yes | find_images (L22), get_exif (L30), exif_val (L44), compute_ev (L50), analyze_image (L58), main (L129) |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/analyze_qualified.py` | 79 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/check_exif.py` | 33 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/check_manifest.py` | 23 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/classify_scenes.py` | 135 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/make_contact_sheet.py` | 50 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/pull_baseline.py` | 50 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/reconcile_baseline.py` | 138 | PASS | No/unclear | — |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/select_baseline.py` | 276 | PASS | No/unclear | classify_scene (L27) |
| `analysis_results/final_calibration/no_cost_tests/ab_comparison/select_baseline_v2.py` | 251 | PASS | No/unclear | classify_scene (L20) |
| `analysis_results/final_calibration/no_cost_tests/analyze_no_cost.py` | 335 | PASS | No/unclear | classify_source (L32), get_keys (L182) |
| `analysis_results/final_calibration/print_targets/generate_targets.py` | 359 | PASS | No/unclear | — |
| `analysis_results/final_calibration/today_videos/analyze_videos.py` | 39 | PASS | No/unclear | — |
| `analysis_results/imx682_config/allrounder/generate_allrounder.py` | 295 | PASS | No/unclear | set_key (L17), set_keys_by_pattern (L24), get_keys (L33) |
| `analysis_results/imx682_config/apply_variants.py` | 88 | PASS | Yes | set_key (L10), save (L18), apply_variant (L21) |
| `analysis_results/imx682_config/audit_gcam.py` | 16 | PASS | No/unclear | — |
| `analysis_results/imx682_config/audit_variants.py` | 12 | PASS | No/unclear | — |
| `analysis_results/imx682_config/final/generate_final.py` | 198 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/final/generate_final_config.py` | 186 | PASS | No/unclear | set_key (L18), get_keys (L25) |
| `analysis_results/imx682_config/generate_corrected.py` | 93 | PASS | Yes | set_key (L12), main (L20) |
| `analysis_results/imx682_config/generate_optimized.py` | 97 | PASS | Yes | set_key (L11), main (L19) |
| `analysis_results/imx682_config/hdr_master/generate_hdr.py` | 221 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/hdr_video/generate_hdr_video.py` | 144 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/lava/generate_lava.py` | 131 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/list_keys.py` | 11 | PASS | No/unclear | — |
| `analysis_results/imx682_config/lowlight_v3/generate_lowlight_v3.py` | 298 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/lowlight_v4/generate_lowlight_v4.py` | 325 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/lowlight_v5/generate_lowlight_v5.py` | 281 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/special/generate_special.py` | 121 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/supercrisp/generate_supercrisp.py` | 134 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/superportrait_hdr/generate_superportrait.py` | 236 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/superportrait_v2/generate_v2.py` | 302 | PASS | No/unclear | set_key (L17), set_keys_by_pattern (L24), get_keys (L34) |
| `analysis_results/imx682_config/telegram/generate_telegram.py` | 151 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/verify_changes.py` | 35 | PASS | No/unclear | get_keys (L4) |
| `analysis_results/imx682_config/verify_configs.py` | 8 | PASS | No/unclear | — |
| `analysis_results/imx682_config/verify_corrected.py` | 49 | PASS | No/unclear | get_keys (L11) |
| `analysis_results/imx682_config/verify_optimized.py` | 8 | PASS | No/unclear | — |
| `analysis_results/imx682_config/video/generate_video.py` | 143 | PASS | No/unclear | set_key (L16), get_keys (L23) |
| `analysis_results/imx682_config/video_master/generate_video_master.py` | 292 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `analysis_results/imx682_config/video_master_v2/generate_video_master_v2.py` | 293 | PASS | No/unclear | set_key (L17), get_keys (L24) |
| `benchmark_dcim.py` | 66 | PASS | Yes | compute_sharpness (L21), main (L28) |
| `create_allrounder.py` | 103 | PASS | No/unclear | — |
| `create_v5.py` | 55 | PASS | No/unclear | — |
| `create_v6.py` | 100 | PASS | No/unclear | — |
| `create_v7.py` | 77 | PASS | No/unclear | — |
| `dcim_calibration_audit.py` | 603 | PASS | Yes | relative_path (L41), sha256_file (L48), walk_files (L56), audit_python (L91), audit_xml (L172), main (L198) |
| `imx682_opencv_calibration.py` | 299 | PASS | Yes | find_images (L19), get_exif (L27), exif_val (L40), compute_ev (L45), classify_image (L50), analyze_image (L77), main (L136) |
| `lxx521_imx682_v8_audit.py` | 265 | PASS | Yes | sha256 (L35), parse_xml (L42), markdown_escape (L72), compare (L75), main (L83) |
| `make_candidate_c.py` | 87 | PASS | No/unclear | — |
| `make_candidate_d.py` | 67 | PASS | No/unclear | — |
| `manage_noise_models.py` | 60 | PASS | Yes | banner (L15), check_noise_setup (L20), create_noise_stub (L39) |
| `patch_dcim.py` | 99 | PASS | No/unclear | — |
| `run_crisp_pipeline.py` | 92 | PASS | Yes | banner (L17), verify_environment (L22), display_online_guidelines (L34), execute_analysis (L48), deploy_sharp_profile (L56) |
| `workflow_master.py` | 65 | PASS | Yes | banner (L14), deploy_profile (L19), main (L51) |
| `workflow_master_v4.py` | 103 | PASS | Yes | banner (L15), collect_profiles (L18), validate_xml (L26), deploy (L45), main (L71) |

### Dependency map (heuristic)

- **`adb_capture_helper.py`** — local-looking imports: none detected; other imports: os, sys, shutil, json, datetime, PIL, PIL.ExifTags
- **`analysis_results/dcim_chart_audit/analyze_dcim.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, datetime, PIL, numpy, cv2, matplotlib, matplotlib.pyplot
- **`analysis_results/dcim_chart_audit/analyze_exif.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, PIL
- **`analysis_results/dcim_chart_audit/analyze_opencv.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, numpy, cv2, PIL
- **`analysis_results/dcim_chart_audit/generate_plots.py`** — local-looking imports: none detected; other imports: os, json, numpy, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/final_report/check_new_photos.py`** — local-looking imports: none detected; other imports: os, math, PIL
- **`analysis_results/final_calibration/final_report/fix_lmc_stock.py`** — local-looking imports: none detected; other imports: os, json, hashlib, numpy
- **`analysis_results/final_calibration/final_report/generate_final_report.py`** — local-looking imports: none detected; other imports: os, json, hashlib, csv, numpy, xml.etree.ElementTree
- **`analysis_results/final_calibration/final_report/video_focus_analysis.py`** — local-looking imports: none detected; other imports: os, json, cv2, numpy, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/final_report/video_focus_summary.py`** — local-looking imports: none detected; other imports: json
- **`analysis_results/final_calibration/latest_captures/analyze_latest.py`** — local-looking imports: none detected; other imports: os, cv2, numpy, PIL
- **`analysis_results/final_calibration/latest_captures/analyze_portrait.py`** — local-looking imports: none detected; other imports: os, cv2, numpy
- **`analysis_results/final_calibration/latest_captures/check_latest.py`** — local-looking imports: none detected; other imports: os, math, PIL
- **`analysis_results/final_calibration/latest_samples/analyze_samples.py`** — local-looking imports: none detected; other imports: os, math, cv2, numpy, PIL
- **`analysis_results/final_calibration/monitor_calibration/analyze_all_monitor.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, datetime, PIL, numpy, cv2, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/monitor_calibration/analyze_monitor_baseline.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, datetime, PIL, numpy, cv2, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/monitor_calibration/generate_monitor_charts.py`** — local-looking imports: none detected; other imports: numpy, PIL, os, json, hashlib, datetime, matplotlib.patches, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/monitor_calibration/pull_new.py`** — local-looking imports: none detected; other imports: subprocess, os
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/ab_analyze.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, datetime, PIL, numpy, cv2, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/analyze_qualified.py`** — local-looking imports: ab_analyze; other imports: os, sys, json, csv, hashlib, datetime, PIL, numpy, cv2, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/check_exif.py`** — local-looking imports: none detected; other imports: os, json, PIL, math
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/check_manifest.py`** — local-looking imports: none detected; other imports: json
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/classify_scenes.py`** — local-looking imports: none detected; other imports: os, json, csv, hashlib, numpy, cv2, PIL, json
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/make_contact_sheet.py`** — local-looking imports: none detected; other imports: os, json, PIL, matplotlib, matplotlib.pyplot
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/pull_baseline.py`** — local-looking imports: none detected; other imports: subprocess, os
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/reconcile_baseline.py`** — local-looking imports: none detected; other imports: os, json, hashlib, math, PIL, collections
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/select_baseline.py`** — local-looking imports: none detected; other imports: os, json, csv, math, numpy, cv2, PIL, collections
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/select_baseline_v2.py`** — local-looking imports: none detected; other imports: os, json, math, numpy, cv2, PIL, collections
- **`analysis_results/final_calibration/no_cost_tests/analyze_no_cost.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, hashlib, numpy, cv2, matplotlib, matplotlib.pyplot, collections, xml.etree.ElementTree
- **`analysis_results/final_calibration/print_targets/generate_targets.py`** — local-looking imports: none detected; other imports: matplotlib, matplotlib.pyplot, matplotlib.patches, numpy, os, hashlib, json, datetime
- **`analysis_results/final_calibration/today_videos/analyze_videos.py`** — local-looking imports: none detected; other imports: os, cv2, numpy
- **`analysis_results/imx682_config/allrounder/generate_allrounder.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/apply_variants.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/audit_gcam.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, os
- **`analysis_results/imx682_config/audit_variants.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree
- **`analysis_results/imx682_config/final/generate_final.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/final/generate_final_config.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/generate_corrected.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/generate_optimized.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/hdr_master/generate_hdr.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/hdr_video/generate_hdr_video.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime
- **`analysis_results/imx682_config/lava/generate_lava.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime
- **`analysis_results/imx682_config/list_keys.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree
- **`analysis_results/imx682_config/lowlight_v3/generate_lowlight_v3.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/lowlight_v4/generate_lowlight_v4.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/lowlight_v5/generate_lowlight_v5.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/special/generate_special.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime
- **`analysis_results/imx682_config/supercrisp/generate_supercrisp.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime
- **`analysis_results/imx682_config/superportrait_hdr/generate_superportrait.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/superportrait_v2/generate_v2.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/telegram/generate_telegram.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime, subprocess
- **`analysis_results/imx682_config/verify_changes.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree
- **`analysis_results/imx682_config/verify_configs.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/verify_corrected.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/verify_optimized.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os
- **`analysis_results/imx682_config/video/generate_video.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, shutil, datetime
- **`analysis_results/imx682_config/video_master/generate_video_master.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`analysis_results/imx682_config/video_master_v2/generate_video_master_v2.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, hashlib, os, json, shutil, datetime
- **`benchmark_dcim.py`** — local-looking imports: none detected; other imports: os, sys, pathlib
- **`create_allrounder.py`** — local-looking imports: none detected; other imports: pathlib, xml.etree.ElementTree, hashlib, shutil
- **`create_v5.py`** — local-looking imports: none detected; other imports: pathlib, xml.etree.ElementTree, shutil
- **`create_v6.py`** — local-looking imports: none detected; other imports: pathlib, re, shutil, time, xml.etree.ElementTree
- **`create_v7.py`** — local-looking imports: none detected; other imports: shutil, xml.etree.ElementTree, datetime, pathlib
- **`dcim_calibration_audit.py`** — local-looking imports: none detected; other imports: argparse, ast, hashlib, json, os, sys, xml.etree.ElementTree, collections, datetime, pathlib
- **`imx682_opencv_calibration.py`** — local-looking imports: none detected; other imports: os, sys, json, csv, argparse, hashlib, glob, datetime, numpy, cv2, matplotlib, matplotlib.pyplot, PIL
- **`lxx521_imx682_v8_audit.py`** — local-looking imports: none detected; other imports: argparse, hashlib, json, os, re, shutil, sys, tempfile, datetime, pathlib, xml.etree.ElementTree
- **`make_candidate_c.py`** — local-looking imports: none detected; other imports: xml.etree.ElementTree, pathlib, hashlib, shutil
- **`make_candidate_d.py`** — local-looking imports: none detected; other imports: pathlib, xml.etree.ElementTree, hashlib, sys
- **`manage_noise_models.py`** — local-looking imports: none detected; other imports: os, shutil, pathlib
- **`patch_dcim.py`** — local-looking imports: none detected; other imports: pathlib
- **`run_crisp_pipeline.py`** — local-looking imports: none detected; other imports: os, sys, subprocess, shutil, pathlib
- **`workflow_master.py`** — local-looking imports: none detected; other imports: shutil, pathlib
- **`workflow_master_v4.py`** — local-looking imports: none detected; other imports: __future__, shutil, sys, xml.etree.ElementTree, datetime, pathlib

### Camera/image processing calls

- **`analysis_results/dcim_chart_audit/analyze_dcim.py`**
  - Line 22: `os.walk`
  - Line 60: `cv2.imread`
  - Line 63: `cv2.cvtColor`
  - Line 82: `cv2.cvtColor`
  - Line 105: `cv2.findChessboardCorners`
  - Line 108: `cv2.cornerSubPix`
  - Line 142: `cv2.imwrite`
- **`analysis_results/dcim_chart_audit/analyze_exif.py`**
  - Line 14: `os.walk`
- **`analysis_results/dcim_chart_audit/analyze_opencv.py`**
  - Line 18: `os.walk`
  - Line 28: `cv2.imread`
  - Line 43: `cv2.cvtColor`
  - Line 46: `cv2.cvtColor`
  - Line 67: `cv2.findChessboardCorners`
  - Line 70: `cv2.cornerSubPix`
  - Line 102: `cv2.imwrite`
- **`analysis_results/dcim_chart_audit/generate_plots.py`**
  - Line 34: `plt.savefig`
  - Line 49: `plt.savefig`
  - Line 64: `plt.savefig`
  - Line 80: `plt.savefig`
  - Line 95: `plt.savefig`
- **`analysis_results/final_calibration/final_report/generate_final_report.py`**
  - Line 143: `os.walk`
- **`analysis_results/final_calibration/final_report/video_focus_analysis.py`**
  - Line 20: `cv2.VideoCapture`
  - Line 44: `cv2.cvtColor`
  - Line 141: `plt.savefig`
- **`analysis_results/final_calibration/latest_captures/analyze_latest.py`**
  - Line 8: `cv2.imread`
  - Line 12: `cv2.cvtColor`
  - Line 14: `cv2.cvtColor`
- **`analysis_results/final_calibration/latest_captures/analyze_portrait.py`**
  - Line 5: `cv2.imread`
  - Line 6: `cv2.cvtColor`
  - Line 8: `cv2.cvtColor`
- **`analysis_results/final_calibration/latest_samples/analyze_samples.py`**
  - Line 8: `cv2.imread`
  - Line 12: `cv2.cvtColor`
  - Line 14: `cv2.cvtColor`
- **`analysis_results/final_calibration/monitor_calibration/analyze_all_monitor.py`**
  - Line 26: `os.walk`
  - Line 84: `cv2.imread`
  - Line 87: `cv2.cvtColor`
  - Line 109: `cv2.cvtColor`
  - Line 116: `cv2.cvtColor`
  - Line 140: `cv2.findChessboardCorners`
  - Line 143: `cv2.cornerSubPix`
  - Line 173: `cv2.imwrite`
  - Line 299: `plt.savefig`
  - Line 316: `plt.savefig`
  - Line 337: `plt.savefig`
  - Line 353: `plt.savefig`
- **`analysis_results/final_calibration/monitor_calibration/analyze_monitor_baseline.py`**
  - Line 25: `os.walk`
  - Line 88: `cv2.imread`
  - Line 91: `cv2.cvtColor`
  - Line 114: `cv2.cvtColor`
  - Line 121: `cv2.cvtColor`
  - Line 146: `cv2.findChessboardCorners`
  - Line 149: `cv2.cornerSubPix`
  - Line 182: `cv2.imwrite`
  - Line 303: `plt.savefig`
  - Line 320: `plt.savefig`
  - Line 341: `plt.savefig`
- **`analysis_results/final_calibration/monitor_calibration/generate_monitor_charts.py`**
  - Line 112: `fig.savefig`
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/ab_analyze.py`**
  - Line 24: `os.walk`
  - Line 59: `cv2.imread`
  - Line 62: `cv2.cvtColor`
  - Line 84: `cv2.cvtColor`
  - Line 89: `cv2.cvtColor`
  - Line 236: `plt.savefig`
  - Line 255: `plt.savefig`
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/analyze_qualified.py`**
  - Line 73: `plt.savefig`
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/classify_scenes.py`**
  - Line 16: `cv2.imread`
  - Line 19: `cv2.cvtColor`
  - Line 26: `cv2.cvtColor`
- **`analysis_results/final_calibration/no_cost_tests/ab_comparison/make_contact_sheet.py`**
  - Line 35: `plt.savefig`
  - Line 47: `plt.savefig`
- **`analysis_results/final_calibration/no_cost_tests/analyze_no_cost.py`**
  - Line 221: `plt.savefig`
  - Line 238: `plt.savefig`
  - Line 252: `plt.savefig`
  - Line 269: `plt.savefig`
  - Line 285: `plt.savefig`
- **`analysis_results/final_calibration/print_targets/generate_targets.py`**
  - Line 78: `fig.savefig`
  - Line 134: `fig.savefig`
  - Line 186: `fig.savefig`
  - Line 236: `fig.savefig`
- **`analysis_results/final_calibration/today_videos/analyze_videos.py`**
  - Line 8: `cv2.VideoCapture`
  - Line 27: `cv2.cvtColor`
- **`analysis_results/imx682_config/audit_gcam.py`**
  - Line 5: `os.walk`
- **`benchmark_dcim.py`**
  - Line 23: `cv2.imread`
- **`dcim_calibration_audit.py`**
  - Line 60: `os.walk`
  - Line 144: `ast.walk`
- **`imx682_opencv_calibration.py`**
  - Line 21: `os.walk`
  - Line 53: `cv2.findChessboardCorners`
  - Line 56: `cv2.findChessboardCorners`
  - Line 59: `cv2.findChessboardCorners`
  - Line 62: `cv2.findChessboardCorners`
  - Line 78: `cv2.imread`
  - Line 81: `cv2.cvtColor`
  - Line 94: `cv2.cvtColor`
  - Line 180: `cv2.imread`
  - Line 181: `cv2.findChessboardCorners`
  - Line 184: `cv2.cornerSubPix`
  - Line 189: `cv2.imread`
  - Line 192: `cv2.imwrite`
  - Line 215: `cv2.imread`
  - Line 216: `cv2.calibrateCamera`
  - Line 228: `cv2.projectPoints`
  - Line 274: `plt.savefig`
  - Line 290: `plt.savefig`
- **`lxx521_imx682_v8_audit.py`**
  - Line 101: `root.rglob`
  - Line 156: `root.rglob`
- **`manage_noise_models.py`**
  - Line 24: `CONFIG_DIR.glob`
  - Line 24: `BASE_DIR.glob`
  - Line 32: `SDCARD_LMC_DIR.glob`
- **`run_crisp_pipeline.py`**
  - Line 62: `CONFIG_DIR.glob`
- **`workflow_master.py`**
  - Line 26: `CONFIG_DIR.glob`
- **`workflow_master_v4.py`**
  - Line 22: `folder.glob`

## 4. XML/profile inventory

| XML path | Status | Root tag | Elements | Attributes |
|---|---|---|---:|---:|
| `analysis_results/imx682_config/allrounder/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/allrounder/LXX521_IMX682_AllRounder_Master_V1.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/balanced.xml` | PASS | `map` | 2638 | 2634 |
| `analysis_results/imx682_config/detail.xml` | PASS | `map` | 2638 | 2634 |
| `analysis_results/imx682_config/final/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/final/LXX521_IMX682_SuperCrisp.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/final/LXX521_LMC84_Optimized_Final.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/hdr_master/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/hdr_video/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lava/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lava/Lava_Crisp_Clear.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight.xml` | PASS | `map` | 2638 | 2634 |
| `analysis_results/imx682_config/lowlight_v3/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight_v4/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight_v5/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/lowlight_v5/LXX521_IMX682_LowLight_Shot_V5.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/LXX521_CleanZoomAndCrisp.xml` | PASS | `map` | 2653 | 2663 |
| `analysis_results/imx682_config/LXX521_LMC84_Optimized_Corrected.xml` | PASS | `map` | 2638 | 2634 |
| `analysis_results/imx682_config/LXX521_UltimateSpeedCrisp.xml` | PASS | `map` | 2652 | 2648 |
| `analysis_results/imx682_config/original_V2_Release_Day.xml` | PASS | `map` | 2638 | 2634 |
| `analysis_results/imx682_config/special/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/special/LXX521_LMC84_Special.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/supercrisp/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/supercrisp/LXX521_IMX682_SuperCrisp.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/superportrait_hdr/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/superportrait_v2/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/superportrait_v2/LXX521_IMX682_SuperPortrait_HDR_V2.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/telegram/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/telegram/LXX521_IMX682_Telegram.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video/Lava_Videography.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video_master/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video_master_v2/default_working_backup.xml` | PASS | `map` | 2645 | 2641 |
| `analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml` | PASS | `map` | 2645 | 2641 |
| `LXX521_BSG_Master.xml` | PASS | `map` | 13 | 12 |
| `LXX521_BSG_Pro.xml` | PASS | `map` | 13 | 12 |
| `LXX521_FrontCam_Only_Sanitized.xml` | PASS | `map` | 20 | 19 |
| `LXX521_FrontCam_Sanitized_V2.xml` | PASS | `map` | 12 | 11 |
| `LXX521_FrontCam_Sanitized_V3.xml` | PASS | `map` | 18 | 17 |
| `LXX521_IMX682_ActionCam.xml` | PASS | `map` | 28 | 27 |
| `LXX521_IMX682_AllInOne_Master.xml` | PASS | `map` | 27 | 26 |
| `LXX521_IMX682_AllInOne_V2.xml` | PASS | `map` | 27 | 26 |
| `LXX521_IMX682_AllInOne_V3.xml` | PASS | `map` | 27 | 26 |
| `LXX521_IMX682_FastShutter.xml` | PASS | `map` | 25 | 24 |
| `LXX521_IMX682_HDR_Video_Test.xml` | PASS | `map` | 11 | 10 |
| `LXX521_IMX682_ISO_Boost.xml` | PASS | `map` | 23 | 22 |
| `LXX521_IMX682_Master_PhotoVideo.xml` | PASS | `map` | 25 | 24 |
| `LXX521_IMX682_MaxQuality.xml` | PASS | `map` | 30 | 29 |
| `LXX521_IMX682_NightPro.xml` | PASS | `map` | 27 | 26 |
| `LXX521_IMX682_PerfectNight.xml` | PASS | `map` | 20 | 19 |
| `LXX521_IMX682_Super_AllInOne_V4.xml` | PASS | `map` | 27 | 26 |
| `LXX521_IMX682_TunedPro.xml` | PASS | `map` | 25 | 24 |
| `LXX521_IMX682_UltimateMaster.xml` | PASS | `map` | 26 | 25 |
| `LXX521_MasterPortrait.xml` | PASS | `map` | 22 | 21 |
| `LXX521_MasterPortrait_Pro.xml` | PASS | `map` | 15 | 14 |
| `LXX521_UltraSharp_Detail.xml` | PASS | `map` | 22 | 21 |
| `profiles/LXX521_BSG_Master.xml` | PASS | `map` | 13 | 12 |
| `profiles/LXX521_BSG_Pro.xml` | PASS | `map` | 13 | 12 |
| `profiles/LXX521_IMX682_AllInOne_V2.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_AllInOne_V3.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_AllRounder_NaturalBalanced.xml` | PASS | `map` | 2645 | 2641 |
| `profiles/LXX521_IMX682_HDR_Video_Test.xml` | PASS | `map` | 11 | 10 |
| `profiles/LXX521_IMX682_LMC84_AllRounder.xml` | PASS | `map` | 2645 | 2641 |
| `profiles/LXX521_IMX682_NightPro.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_Super_AllInOne_V6_NightIndoor.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml` | PASS | `map` | 27 | 26 |
| `profiles/LXX521_IMX682_UltimateMaster.xml` | PASS | `map` | 26 | 25 |
| `profiles/LXX521_MasterPortrait_Pro.xml` | PASS | `map` | 15 | 14 |

### Candidate profile XMLs

This is a filename/path heuristic, not proof of active LMC use.

- `analysis_results/imx682_config/allrounder/default_working_backup.xml`
- `analysis_results/imx682_config/allrounder/LXX521_IMX682_AllRounder_Master_V1.xml`
- `analysis_results/imx682_config/balanced.xml`
- `analysis_results/imx682_config/detail.xml`
- `analysis_results/imx682_config/final/default_working_backup.xml`
- `analysis_results/imx682_config/final/LXX521_IMX682_SuperCrisp.xml`
- `analysis_results/imx682_config/final/LXX521_LMC84_Optimized_Final.xml`
- `analysis_results/imx682_config/hdr_master/default_working_backup.xml`
- `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml`
- `analysis_results/imx682_config/hdr_video/default_working_backup.xml`
- `analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml`
- `analysis_results/imx682_config/lava/default_working_backup.xml`
- `analysis_results/imx682_config/lava/Lava_Crisp_Clear.xml`
- `analysis_results/imx682_config/lowlight.xml`
- `analysis_results/imx682_config/lowlight_v3/default_working_backup.xml`
- `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml`
- `analysis_results/imx682_config/lowlight_v4/default_working_backup.xml`
- `analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml`
- `analysis_results/imx682_config/lowlight_v5/default_working_backup.xml`
- `analysis_results/imx682_config/lowlight_v5/LXX521_IMX682_LowLight_Shot_V5.xml`
- `analysis_results/imx682_config/LXX521_CleanZoomAndCrisp.xml`
- `analysis_results/imx682_config/LXX521_LMC84_Optimized_Corrected.xml`
- `analysis_results/imx682_config/LXX521_UltimateSpeedCrisp.xml`
- `analysis_results/imx682_config/original_V2_Release_Day.xml`
- `analysis_results/imx682_config/special/default_working_backup.xml`
- `analysis_results/imx682_config/special/LXX521_LMC84_Special.xml`
- `analysis_results/imx682_config/supercrisp/default_working_backup.xml`
- `analysis_results/imx682_config/supercrisp/LXX521_IMX682_SuperCrisp.xml`
- `analysis_results/imx682_config/superportrait_hdr/default_working_backup.xml`
- `analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml`
- `analysis_results/imx682_config/superportrait_v2/default_working_backup.xml`
- `analysis_results/imx682_config/superportrait_v2/LXX521_IMX682_SuperPortrait_HDR_V2.xml`
- `analysis_results/imx682_config/telegram/default_working_backup.xml`
- `analysis_results/imx682_config/telegram/LXX521_IMX682_Telegram.xml`
- `analysis_results/imx682_config/video/default_working_backup.xml`
- `analysis_results/imx682_config/video/Lava_Videography.xml`
- `analysis_results/imx682_config/video_master/default_working_backup.xml`
- `analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml`
- `analysis_results/imx682_config/video_master_v2/default_working_backup.xml`
- `analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml`
- `LXX521_BSG_Master.xml`
- `LXX521_BSG_Pro.xml`
- `LXX521_FrontCam_Only_Sanitized.xml`
- `LXX521_FrontCam_Sanitized_V2.xml`
- `LXX521_FrontCam_Sanitized_V3.xml`
- `LXX521_IMX682_ActionCam.xml`
- `LXX521_IMX682_AllInOne_Master.xml`
- `LXX521_IMX682_AllInOne_V2.xml`
- `LXX521_IMX682_AllInOne_V3.xml`
- `LXX521_IMX682_FastShutter.xml`
- `LXX521_IMX682_HDR_Video_Test.xml`
- `LXX521_IMX682_ISO_Boost.xml`
- `LXX521_IMX682_Master_PhotoVideo.xml`
- `LXX521_IMX682_MaxQuality.xml`
- `LXX521_IMX682_NightPro.xml`
- `LXX521_IMX682_PerfectNight.xml`
- `LXX521_IMX682_Super_AllInOne_V4.xml`
- `LXX521_IMX682_TunedPro.xml`
- `LXX521_IMX682_UltimateMaster.xml`
- `LXX521_MasterPortrait.xml`
- `LXX521_MasterPortrait_Pro.xml`
- `LXX521_UltraSharp_Detail.xml`
- `profiles/LXX521_BSG_Master.xml`
- `profiles/LXX521_BSG_Pro.xml`
- `profiles/LXX521_IMX682_AllInOne_V2.xml`
- `profiles/LXX521_IMX682_AllInOne_V3.xml`
- `profiles/LXX521_IMX682_AllRounder_NaturalBalanced.xml`
- `profiles/LXX521_IMX682_HDR_Video_Test.xml`
- `profiles/LXX521_IMX682_LMC84_AllRounder.xml`
- `profiles/LXX521_IMX682_NightPro.xml`
- `profiles/LXX521_IMX682_Super_AllInOne_V4.xml`
- `profiles/LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml`
- `profiles/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml`
- `profiles/LXX521_IMX682_Super_AllInOne_V6_NightIndoor.xml`
- `profiles/LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml`
- `profiles/LXX521_IMX682_UltimateMaster.xml`
- `profiles/LXX521_MasterPortrait_Pro.xml`

## 5. Byte-identical duplicates (SHA-256)

- **17 files** — SHA-256 `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49`
  - `analysis_results/imx682_config/allrounder/default_working_backup.xml`
  - `analysis_results/imx682_config/final/default_working_backup.xml`
  - `analysis_results/imx682_config/hdr_master/default_working_backup.xml`
  - `analysis_results/imx682_config/hdr_video/default_working_backup.xml`
  - `analysis_results/imx682_config/lava/default_working_backup.xml`
  - `analysis_results/imx682_config/lowlight_v3/default_working_backup.xml`
  - `analysis_results/imx682_config/lowlight_v4/default_working_backup.xml`
  - `analysis_results/imx682_config/lowlight_v5/default_working_backup.xml`
  - `analysis_results/imx682_config/special/default_working_backup.xml`
  - `analysis_results/imx682_config/supercrisp/default_working_backup.xml`
  - `analysis_results/imx682_config/superportrait_hdr/default_working_backup.xml`
  - `analysis_results/imx682_config/superportrait_v2/default_working_backup.xml`
  - `analysis_results/imx682_config/telegram/default_working_backup.xml`
  - `analysis_results/imx682_config/video/default_working_backup.xml`
  - `analysis_results/imx682_config/video_master/default_working_backup.xml`
  - `analysis_results/imx682_config/video_master_v2/default_working_backup.xml`
  - `profiles/LXX521_IMX682_LMC84_AllRounder.xml`
- **4 files** — SHA-256 `afb5f9506a5ef76eb4e0146073b71f0f569b81aed0684ff74745378634567dcc`
  - `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml`
  - `analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml`
  - `analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml`
  - `analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml`
- **4 files** — SHA-256 `050614008f0c002c71daf0feb4908a3c07f42a3c79bc91de45667f18e1e67993`
  - `analysis_results/v8_audit_20261020_211620/V8_AB_TEST_PLAN.md`
  - `analysis_results/v8_audit_20261020_215540/V8_AB_TEST_PLAN.md`
  - `analysis_results/v8_audit_20261020_220428/V8_AB_TEST_PLAN.md`
  - `analysis_results/v8_audit_20261021_001923/V8_AB_TEST_PLAN.md`
- **4 files** — SHA-256 `e02afad332222c3f8e811a34680ee8014a1de8a2e886406858b9a3d3733f3319`
  - `backups/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml.1792509832.destination.bak`
  - `backups/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml.1792509832.local.bak`
  - `backups/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml.1792509861.destination.bak`
  - `backups/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml.1792509861.local.bak`
- **4 files** — SHA-256 `0d8385f495ed74552611cf25ee72bf8bcfd68610337bcecc40e318f25fcf8f97`
  - `LXX521_BSG_Master.xml`
  - `LXX521_BSG_Pro.xml`
  - `profiles/LXX521_BSG_Master.xml`
  - `profiles/LXX521_BSG_Pro.xml`
- **3 files** — SHA-256 `674fc49bf5371eceb9fc6b019bdad7a1833dfdf6a6671e954860890c60178c0b`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133814_LavaPlayUltra_IMX682_Pro.jpg`
  - `monitor_test_1338/020261019_133814_LavaPlayUltra_IMX682_Pro.jpg`
  - `recapture_v12/Camera/020261019_133814_LavaPlayUltra_IMX682_Pro.jpg`
- **3 files** — SHA-256 `2df2d19b6abfb4661fab58bd3cd7d0da3eedc21e74173004884cd5d77cc42a87`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133816_LavaPlayUltra_IMX682_Pro.jpg`
  - `monitor_test_1338/020261019_133816_LavaPlayUltra_IMX682_Pro.jpg`
  - `recapture_v12/Camera/020261019_133816_LavaPlayUltra_IMX682_Pro.jpg`
- **3 files** — SHA-256 `874db740051bcf7eaac7917caff219b5f691eedc25be36d1708096db1419ca18`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133819_LavaPlayUltra_IMX682_Pro.jpg`
  - `monitor_test_1338/020261019_133819_LavaPlayUltra_IMX682_Pro.jpg`
  - `recapture_v12/Camera/020261019_133819_LavaPlayUltra_IMX682_Pro.jpg`
- **3 files** — SHA-256 `b63125d51eff2c46bafb80191be615df6c2c723aa22a6606fb2c3ef90bd77007`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133821_LavaPlayUltra_IMX682_Pro.jpg`
  - `monitor_test_1338/020261019_133821_LavaPlayUltra_IMX682_Pro.jpg`
  - `recapture_v12/Camera/020261019_133821_LavaPlayUltra_IMX682_Pro.jpg`
- **3 files** — SHA-256 `6b7d72cbcc03a20c611a4096e2735018fcb4d25a1911330aea878564672a6ab3`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133843_lmc_8.4.jpg`
  - `monitor_test_1338/020261019_133843_lmc_8.4.jpg`
  - `recapture_v12/Camera/020261019_133843_lmc_8.4.jpg`
- **3 files** — SHA-256 `3f0cb17118f5ea462a76c574a356334292efd427426f5b0ae5f78222668aa36c`
  - `analysis_results/dcim_chart_audit/device_pulls/020261019_133846_lmc_8.4.jpg`
  - `monitor_test_1338/020261019_133846_lmc_8.4.jpg`
  - `recapture_v12/Camera/020261019_133846_lmc_8.4.jpg`
- **3 files** — SHA-256 `623e275c10edf55f7e7c73e34737082bb52dd80565ba670dcd8011c8c23872fb`
  - `analysis_results/dcim_chart_audit/device_pulls/_  20261019_132920_lmc_8.4.jpg`
  - `recapture_1329/_  20261019_132920_lmc_8.4.jpg`
  - `recapture_v12/Camera/_  20261019_132920_lmc_8.4.jpg`
- **3 files** — SHA-256 `bcf696e75ca8feeed40ae8d9a36fd09d00293b04119712596792dcb0fcbcfe9c`
  - `analysis_results/dcim_chart_audit/device_pulls/_  20261019_132923_lmc_8.4.jpg`
  - `recapture_1329/_  20261019_132923_lmc_8.4.jpg`
  - `recapture_v12/Camera/_  20261019_132923_lmc_8.4.jpg`
- **3 files** — SHA-256 `454b62c6522a9ce42109d29e36b926084a2420825ca1e8ba1824a551b241b567`
  - `analysis_results/dcim_chart_audit/device_pulls/_  20261019_132924_lmc_8.4.jpg`
  - `recapture_1329/_  20261019_132924_lmc_8.4.jpg`
  - `recapture_v12/Camera/_  20261019_132924_lmc_8.4.jpg`
- **3 files** — SHA-256 `5833366bd9e815ac0a61d2ecba47907a707ecab5228d3e298b1221cee4e1685b`
  - `analysis_results/dcim_chart_audit/device_pulls/_  20261019_133147_lmc_8.4.jpg`
  - `recapture_1331/_  20261019_133147_lmc_8.4.jpg`
  - `recapture_v12/Camera/_  20261019_133147_lmc_8.4.jpg`
- **3 files** — SHA-256 `b061b5389526b57da7d54467e443831bc7ed876e97863c673a1aa3165dc58e7b`
  - `analysis_results/dcim_chart_audit/device_pulls/_  20261019_133152_lmc_8.4.jpg`
  - `recapture_1331/_  20261019_133152_lmc_8.4.jpg`
  - `recapture_v12/Camera/_  20261019_133152_lmc_8.4.jpg`
- **3 files** — SHA-256 `457c5987a80493606a6e24c8013e7b0e4dd5a8b876b39c48421e2ef5045421a6`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_133141_1_HDR.jpg`
  - `recapture_1331/IMG_20261019_133141_1_HDR.jpg`
  - `recapture_v12/Camera/IMG_20261019_133141_1_HDR.jpg`
- **3 files** — SHA-256 `b41b228568e908d40cf643f2d0422de4e7d784e2405a7370cfd1177b6ab179cd`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134401_1.jpg`
  - `bracket_test_1344/IMG_20261019_134401_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134401_1.jpg`
- **3 files** — SHA-256 `380b4aa45a8c167b37cc29c97c9de2c3baed8eea6c9994e355396aca6e04810d`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134408_1.jpg`
  - `bracket_test_1344/IMG_20261019_134408_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134408_1.jpg`
- **3 files** — SHA-256 `25c8fbeb6ba4f6b3ab66511113d24683311e192cbf2609f3245dfe804b50e566`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134414_1.jpg`
  - `bracket_test_1344/IMG_20261019_134414_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134414_1.jpg`
- **3 files** — SHA-256 `15763839e8b7e33bcf02c526b2a2030876398489c2dc14a85c26356c25fade96`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134420_1.jpg`
  - `bracket_test_1344/IMG_20261019_134420_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134420_1.jpg`
- **3 files** — SHA-256 `ae37c1ba4fa76c54e01980dea4ca8b6bea772cd63e0b2665bb11edb929d6c99b`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134758_1.jpg`
  - `bracket_test_1347/IMG_20261019_134758_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134758_1.jpg`
- **3 files** — SHA-256 `3491422a861767ae4b3ecaebb2f8d7044f752c4465cad70fe842e28f29d5789b`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134804_1.jpg`
  - `bracket_test_1347/IMG_20261019_134804_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134804_1.jpg`
- **3 files** — SHA-256 `89bcfe2d82533465705a9a1c23810fae50036d1b8c3ae013aef60c1fe2b40006`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134814_1.jpg`
  - `bracket_test_1347/IMG_20261019_134814_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134814_1.jpg`
- **3 files** — SHA-256 `da0433fc33d116c17fda39bd705aba7f17e8f0ce7743b18c8ae0c70edd493ce8`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_134816_1.jpg`
  - `bracket_test_1347/IMG_20261019_134816_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134816_1.jpg`
- **2 files** — SHA-256 `2c96c853743332af5c40bc76d1aab2eab64683d5e5c259557b636a3dbca8c1e3`
  - `analysis_results/dcim_chart_audit/device_pulls/20261019_140214_lmc_8.4.jpg`
  - `recapture_v12/Camera/20261019_140214_lmc_8.4.jpg`
- **2 files** — SHA-256 `1161addeecf0568f4ee16c78d78e08379e793c12dc1bca13b894c362b44c1199`
  - `analysis_results/dcim_chart_audit/device_pulls/20261019_141010_lmc_8.4.jpg`
  - `recapture_v12/Camera/20261019_141010_lmc_8.4.jpg`
- **2 files** — SHA-256 `b4ef1ba7743040f8fa847e85e78871996c783f9e6548e950a5f2e536fe236f2c`
  - `analysis_results/dcim_chart_audit/device_pulls/20261019_141014_lmc_8.4.jpg`
  - `recapture_v12/Camera/20261019_141014_lmc_8.4.jpg`
- **2 files** — SHA-256 `00115d441c276c0f35e8f7f9691799facfea536228be4f0ed039198650c518d5`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142620_HDR.jpg`
  - `recapture_v12/Camera/IMG_20261019_142620_HDR.jpg`
- **2 files** — SHA-256 `13848a8ac0e7b1b0724e9ed593d8df38f80af6be4ac204434b212b2f6c2bd482`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142622.jpg`
  - `recapture_v12/Camera/IMG_20261019_142622.jpg`
- **2 files** — SHA-256 `740057831eb438af9a54e12d1fd72a5452c48352ee35df637ad48da3b6490b00`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142629_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142629_1.jpg`
- **2 files** — SHA-256 `b6a6817d73bd76cc913d25178540b2293b2457156ee01e7a9a4e00ddf6ffc7a5`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142631_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142631_1.jpg`
- **2 files** — SHA-256 `c7b4c42e6113ecc29addcd1c227e5e82f0d7aebb848eb6ad68879b95e9c81086`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142632_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142632_1.jpg`
- **2 files** — SHA-256 `6f3d621ecc494dd314966694b77005f745b93a3cd8c147f8b7656cf78ddf8cb5`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142635_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142635_1.jpg`
- **2 files** — SHA-256 `187d7fda319a71f0041e2d4257718a34721091051eb3308b847c58da41f66874`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142639_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142639_1.jpg`
- **2 files** — SHA-256 `a7f8c86faaac53c08a3f556f021a23cc9a2e5afbb2feb01c3397d8c35c6c2086`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142642_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142642_1.jpg`
- **2 files** — SHA-256 `d917407b298540e0066f34c977b5574e90232e0016eff4de6e6da7053fc56c1d`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142644_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142644_1.jpg`
- **2 files** — SHA-256 `8a06c8399e1f8af9c815c624a58d951fd1730c50034f8f9f43885aac9939a2ef`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142647_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142647_1.jpg`
- **2 files** — SHA-256 `4474fefb49dc4a59674254795877db42d118d6b56c3eb24084f523c86aea475a`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142649_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142649_1.jpg`
- **2 files** — SHA-256 `558c70bea81ea5fd1dbe48fc87974dbde45e015fb962042b50f201e837fd7f21`
  - `analysis_results/dcim_chart_audit/device_pulls/IMG_20261019_142650_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_142650_1.jpg`
- **2 files** — SHA-256 `273435357064a3f1a2e221ccd7aad80a5b83bf11759c6a443de4787422f87bb5`
  - `analysis_results/dcim_chart_audit/plots/edge_density_all.png`
  - `analysis_results/final_calibration/final_report/plots/edge_density_all.png`
- **2 files** — SHA-256 `88eefcd18e11f394a36741cc307722b84c3828ef9f699653398bea5577559666`
  - `analysis_results/dcim_chart_audit/plots/iso_vs_ev.png`
  - `analysis_results/final_calibration/final_report/plots/iso_vs_ev.png`
- **2 files** — SHA-256 `3ae80ce1819a98a63da6b20f08c516874df7527a3b9df535db1b7e37a077e917`
  - `analysis_results/dcim_chart_audit/plots/mtf50_all.png`
  - `analysis_results/final_calibration/final_report/plots/mtf50_all.png`
- **2 files** — SHA-256 `e3beda01d93456872ace45799a44fafba62da8fd9a15b725ff32ea0c1ddaccd5`
  - `analysis_results/dcim_chart_audit/plots/rb_vs_ev.png`
  - `analysis_results/final_calibration/final_report/plots/rb_vs_ev.png`
- **2 files** — SHA-256 `d17bcca8c1f1b77d12b39c1414d605bed67db5abf4407fe34eaab77aa0a41b47`
  - `analysis_results/final_calibration/final_report/plots/black_clip_vs_ev.png`
  - `analysis_results/final_calibration/no_cost_tests/plots/black_clip_vs_ev.png`
- **2 files** — SHA-256 `373b5280efb55d0bebacda5fcbf6a837799a1c9c897009ed652e248a680b5bc6`
  - `analysis_results/final_calibration/final_report/plots/edge_density_distribution.png`
  - `analysis_results/final_calibration/no_cost_tests/plots/edge_density_distribution.png`
- **2 files** — SHA-256 `ba0d734498f03c0b2ef25b676fc18b18e516a3526f149726b09c8564f29e4c52`
  - `analysis_results/final_calibration/final_report/plots/iso_vs_blackclip.png`
  - `analysis_results/final_calibration/no_cost_tests/plots/iso_vs_blackclip.png`
- **2 files** — SHA-256 `c4e3fd4dbe0906471b95da45d97d944d7c24691ef29ca09fa4e75c58cb5e7343`
  - `analysis_results/final_calibration/final_report/plots/moire_distribution.png`
  - `analysis_results/final_calibration/no_cost_tests/plots/moire_distribution.png`
- **2 files** — SHA-256 `30d34a4e00384e93d31c1cf485b664d45e1a283512a83d7cec267896406d7e7d`
  - `analysis_results/final_calibration/final_report/plots/monitor_all_clipping.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_all_clipping.png`
- **2 files** — SHA-256 `7b5df64cc3b9fca8bf4f088e00990f8f2396329a7e8d2ef12cc6cbe50da3e48b`
  - `analysis_results/final_calibration/final_report/plots/monitor_all_moire.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_all_moire.png`
- **2 files** — SHA-256 `54e5d58870c477ad046773126dde2f1507cd9f33e79d72f1dee458fda8928fda`
  - `analysis_results/final_calibration/final_report/plots/monitor_all_mtf50.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_all_mtf50.png`
- **2 files** — SHA-256 `a71c0707218026e3002797bc8a7d007ab2eaf7daf2918d9d325b9e72bd75e542`
  - `analysis_results/final_calibration/final_report/plots/monitor_all_wb.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_all_wb.png`
- **2 files** — SHA-256 `aee534d5e3fed85960b77cd536027a04d314c985bb48e97931fdb328c30dea5e`
  - `analysis_results/final_calibration/final_report/plots/monitor_clipping.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_clipping.png`
- **2 files** — SHA-256 `cf3a6ea8685905cc85b425ceee9a37564bbf247788a6e36ede7e44937ac7d50c`
  - `analysis_results/final_calibration/final_report/plots/monitor_mtf50.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_mtf50.png`
- **2 files** — SHA-256 `c80fc4e6bc64cf931a3046dc10bf7874d8b8a1907cb7992ca66e9a92fed826f6`
  - `analysis_results/final_calibration/final_report/plots/monitor_wb.png`
  - `analysis_results/final_calibration/monitor_calibration/plots/monitor_wb.png`
- **2 files** — SHA-256 `eb9753f8b4bc7cd190b1a8536389c6e32d8e4b14630019b48de862319bfa4cf3`
  - `analysis_results/final_calibration/final_report/plots/warm_cast_distribution.png`
  - `analysis_results/final_calibration/no_cost_tests/plots/warm_cast_distribution.png`
- **2 files** — SHA-256 `bb90c262d33452524e79e40df30678d05412d4e04293e54f5283482dfcbaf59a`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172024_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172024_lmc_8.4.jpg`
- **2 files** — SHA-256 `b722a8a5c39555b98ec821d3905f218ff305833891ac1ed03abc7e3b28b51198`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172034_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172034_lmc_8.4.jpg`
- **2 files** — SHA-256 `aa64f91812244e33ad500bf6417119b49cf7bb83af7cf0ce88a367a98a2a3fea`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172038_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172038_lmc_8.4.jpg`
- **2 files** — SHA-256 `0764ce73d02147b37bc03a09b34dd75c40779a3d1ada09c96413660c1e0a0144`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172044_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172044_lmc_8.4.jpg`
- **2 files** — SHA-256 `b3b51bdef3995ec838378809e2967b4636ee8e71a223b6e51099b9d2902b08a8`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172103_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172103_lmc_8.4.jpg`
- **2 files** — SHA-256 `48f477381e99c2dec4c873fb99d15927c1de17ce6037206c0a99aae5d6e13496`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172106_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172106_lmc_8.4.jpg`
- **2 files** — SHA-256 `a0472a023ff4fea911727abc026652d18a5fda6e86cf3bf307840601130794c7`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172116_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172116_lmc_8.4.jpg`
- **2 files** — SHA-256 `295c930f1f09581dd69c86e8e94217e037b03ffc63f0a79f147ae9a5f261b724`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172124_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172124_lmc_8.4.jpg`
- **2 files** — SHA-256 `92eaaf0a20b3c5768f36eef054a526b63e8b3b6819ce157cd1c3fca6cf5c5ef3`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172126_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172126_lmc_8.4.jpg`
- **2 files** — SHA-256 `91aede2775daea1439aa9d15d64637a197fd46ce5715ad861e06c45b8982724b`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172134_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172134_lmc_8.4.jpg`
- **2 files** — SHA-256 `6e3a7b31e8cb6f39aa9c8e2f0891f5f5817dfd71b3210b057d9744a0d25ff587`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172202_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172202_lmc_8.4.jpg`
- **2 files** — SHA-256 `0dbdefad4024be5971f63c1c8bba20193faa80dd824ca9950db068616af4f838`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172207_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172207_lmc_8.4.jpg`
- **2 files** — SHA-256 `b1b465b871e38f07b503f2ff60646eadb16f8b4e6845b91003cdbc49058b2acd`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172231_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172231_lmc_8.4.jpg`
- **2 files** — SHA-256 `6ed3d08966a6d0113674915d7ce770ec523b5ef3d932c6e01ed6a75e220a40c3`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172451_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172451_lmc_8.4.jpg`
- **2 files** — SHA-256 `e4191d637566b96a456a012e64a695ec54bb636844e990309a44cd22c4af81ae`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172452_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172452_lmc_8.4.jpg`
- **2 files** — SHA-256 `76bb4ee2af8736c7bb6a51beae3b7c27ec95fbcac9d431aeb8d620dd2b966be2`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172454_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172454_lmc_8.4.jpg`
- **2 files** — SHA-256 `9fcb179b4d9cc760e4c63ad48591087b283eb32b6bf248d6eb98db16140492f8`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172512_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172512_lmc_8.4.jpg`
- **2 files** — SHA-256 `9d15f541f305ade6b77d182792d77751b91dac2c43cd0ad0df8f9e7326f60133`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline/20261019_172513_lmc_8.4.jpg`
  - `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified/20261019_172513_lmc_8.4.jpg`
- **2 files** — SHA-256 `2118c905a247a5534dadfb82530638659e7d39c54ea3cf8dd622baf145bebc9a`
  - `analysis_results/imx682_config/balanced.xml`
  - `analysis_results/imx682_config/original_V2_Release_Day.xml`
- **2 files** — SHA-256 `9e7bbfb1ab70cdffe5e0f20d379b539afbee80f219be97d2960f73bcf0187ad8`
  - `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml`
  - `analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml`
- **2 files** — SHA-256 `fbf87e08e796e7a566b78fcefac78ebc08655992291c6b898d471ce57a71b3c9`
  - `analysis_results/imx682_config/video/Lava_Videography.xml`
  - `analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml`
- **2 files** — SHA-256 `8bdfa4cfb2d45206e4da3660b01ca33973ee86e6d5bc006649bf88b79aee523b`
  - `backups/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail_20261020_205827.xml.bak`
  - `profiles/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml`
- **2 files** — SHA-256 `40f6f07c42b2ad37f6c87a48a2c4229ef38a03e2f24e69111814c82fdbd89c16`
  - `bracket_test_1344/IMG_20261019_134433_1.jpg`
  - `recapture_v12/Camera/IMG_20261019_134433_1.jpg`
- **2 files** — SHA-256 `642fd418d7c8ecd3ce4e5c4a1355d7401d7b19de6a6ad805bc945107cccddbf7`
  - `LXX521_IMX682_AllInOne_V2.xml`
  - `profiles/LXX521_IMX682_AllInOne_V2.xml`
- **2 files** — SHA-256 `8be6d35dcd137074d3c2343db7534f4f2d1099c39ed11734f70eb9d63a33c7f8`
  - `LXX521_IMX682_AllInOne_V3.xml`
  - `profiles/LXX521_IMX682_AllInOne_V3.xml`
- **2 files** — SHA-256 `085323aff48fe602293532b82d8ac0c32bdbca39cd4af6e50912435a9290161b`
  - `LXX521_IMX682_HDR_Video_Test.xml`
  - `profiles/LXX521_IMX682_HDR_Video_Test.xml`
- **2 files** — SHA-256 `b59f8744122b776b548136675d4943e49cc5ce36e62f51970c60a0abb02a38a5`
  - `LXX521_IMX682_NightPro.xml`
  - `profiles/LXX521_IMX682_NightPro.xml`
- **2 files** — SHA-256 `15eec8037b7cd173997020da293ffec14ba3a3648d9fa6289083c682cc4085bd`
  - `LXX521_IMX682_Super_AllInOne_V4.xml`
  - `profiles/LXX521_IMX682_Super_AllInOne_V4.xml`
- **2 files** — SHA-256 `07141128e51bb4a08b0f477cb15db127ad4edf458e2516f43b7e902d548815d9`
  - `LXX521_IMX682_UltimateMaster.xml`
  - `profiles/LXX521_IMX682_UltimateMaster.xml`
- **2 files** — SHA-256 `f4ffd9e0af157feb7ebf764692e63ce7285acc56c74bb446ae3b46e013936f25`
  - `LXX521_MasterPortrait_Pro.xml`
  - `profiles/LXX521_MasterPortrait_Pro.xml`

## 6. JSON validation

- `analysis/analysis_results.json`: PASS
- `analysis_results/calibration_verification.json`: PASS
- `analysis_results/color_results.json`: PASS
- `analysis_results/dcim_chart_audit/dcim_exif_inventory.json`: PASS
- `analysis_results/dcim_chart_audit/dcim_full_analysis.json`: PASS
- `analysis_results/distortion_results.json`: PASS
- `analysis_results/final_calibration/final_report/file_manifest.json`: PASS
- `analysis_results/final_calibration/final_report/verification_results.json`: PASS
- `analysis_results/final_calibration/final_report/video_analysis/video_analysis.json`: PASS
- `analysis_results/final_calibration/monitor_calibration/charts/monitor_chart_manifest.json`: PASS
- `analysis_results/final_calibration/monitor_calibration/monitor_all_captures_analysis.json`: PASS
- `analysis_results/final_calibration/monitor_calibration/monitor_baseline_analysis.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_inventory.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_qualified_results.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_results.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/baseline_selection_manifest.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/optimized_results.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/scene_assignments.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/ab_comparison/scene_features.json`: PASS
- `analysis_results/final_calibration/no_cost_tests/no_cost_summary.json`: PASS
- `analysis_results/final_calibration/print_targets/target_manifest.json`: PASS
- `analysis_results/image_metrics_full.json`: PASS
- `analysis_results/imx682_config/allrounder/change_log.json`: PASS
- `analysis_results/imx682_config/allrounder/validation_report.json`: PASS
- `analysis_results/imx682_config/final/change_log.json`: PASS
- `analysis_results/imx682_config/final/validation_report.json`: PASS
- `analysis_results/imx682_config/hdr_master/change_log.json`: PASS
- `analysis_results/imx682_config/hdr_master/validation_report.json`: PASS
- `analysis_results/imx682_config/lowlight_v3/change_log.json`: PASS
- `analysis_results/imx682_config/lowlight_v3/validation_report.json`: PASS
- `analysis_results/imx682_config/lowlight_v4/change_log.json`: PASS
- `analysis_results/imx682_config/lowlight_v4/validation_report.json`: PASS
- `analysis_results/imx682_config/lowlight_v5/change_log.json`: PASS
- `analysis_results/imx682_config/lowlight_v5/validation_report.json`: PASS
- `analysis_results/imx682_config/superportrait_hdr/change_log.json`: PASS
- `analysis_results/imx682_config/superportrait_hdr/validation_report.json`: PASS
- `analysis_results/imx682_config/superportrait_v2/change_log.json`: PASS
- `analysis_results/imx682_config/superportrait_v2/validation_report.json`: PASS
- `analysis_results/imx682_config/video_master/change_log.json`: PASS
- `analysis_results/imx682_config/video_master/validation_report.json`: PASS
- `analysis_results/imx682_config/video_master_v2/change_log.json`: PASS
- `analysis_results/imx682_config/video_master_v2/validation_report.json`: PASS
- `analysis_results/target_1210/analysis/analysis_results.json`: PASS
- `analysis_results/v8_audit_20261020_211620/V8_VALIDATION.json`: PASS
- `analysis_results/v8_audit_20261020_215540/V8_VALIDATION.json`: PASS
- `analysis_results/v8_audit_20261020_220428/V8_VALIDATION.json`: PASS
- `analysis_results/v8_audit_20261021_001923/V8_VALIDATION.json`: PASS
- `bracket_test_1344/analysis/analysis_results.json`: PASS
- `bracket_test_1347/analysis/analysis_results.json`: PASS
- `monitor_test_1338/analysis/analysis_results.json`: PASS
- `new_captures/analysis/analysis_results.json`: PASS
- `new_captures_1325/analysis/analysis_results.json`: PASS
- `recapture_1329/analysis/analysis_results.json`: PASS
- `recapture_1331/analysis/analysis_results.json`: PASS
- `recapture_v12/Camera/analysis/analysis_results.json`: PASS

## 7. Top-level directory counts

| Path | Files |
|---|---:|
| `analysis_results` | 415 |
| `(root)` | 47 |
| `recapture_v12` | 42 |
| `profiles` | 15 |
| `monitor_test_1338` | 10 |
| `bracket_test_1344` | 9 |
| `bracket_test_1347` | 8 |
| `recapture_1329` | 7 |
| `recapture_1331` | 7 |
| `new_captures` | 6 |
| `new_captures_1325` | 6 |
| `backups` | 5 |
| `analysis` | 4 |

## 8. Limitations and cautions

- Static audit only; project scripts are not executed or imported.
- Python syntax PASS does not prove runtime correctness or calibration accuracy.
- XML parsing checks well-formedness, not LMC schema or device compatibility.
- Identical hashes do not identify the authoritative profile.
- Dependency and profile identification are heuristic; dynamic imports may be missed.
- No calibration measurements or image-quality results are generated.

## 9. Recommended validation plan

1. Back up the project before any future changes.
2. Confirm the active LMC 8.4 import directory and profile selection on-device.
3. Review syntax/XML/JSON failures and duplicate groups manually; do not delete duplicates solely by hash.
4. Document every generator's inputs, outputs, overwrite behavior, and dependencies.
5. Test generators on a copied fixture before importing profiles.
6. Use documented captures with known chart geometry and controlled conditions.
7. Validate checkerboard geometry, reprojection RMS, and image-quality metrics independently.
8. Compare one candidate profile at a time against a preserved baseline.

## 10. Reports

- `audit_report.md` — readable report
- `audit_report.json` — detailed inventory and findings
