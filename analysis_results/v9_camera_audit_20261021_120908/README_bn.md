# LXX521 / IMX682 — V9 Camera Audit

- তৈরি: 2026-10-21T12:09:22
- Input folder: `/storage/emulated/0/DCIM/Camera`
- Profile label: **V8_ProBalanced** (ব্যবহারকারীর দেওয়া label; EXIF থেকে যাচাইকৃত নয়)
- নির্বাচিত ছবি: 5
- সফলভাবে decode: 5
- decode ব্যর্থ: 0
- exact duplicate SHA-256 group: 0

## এই রান-এর ফাইল
- `image_metrics.csv` — প্রতি ছবির metadata ও pixel statistics
- `capture_manifest.csv` — capture/EXIF manifest
- `input_sha256_manifest.txt` — input hash তালিকা
- `audit_summary.json` — machine-readable summary
- `execution_log.txt` — execution log
- `output_sha256_manifest.txt` — generated outputs-এর hash (manifest নিজেকে বাদ দিয়ে)

## পরিমাপের ব্যাখ্যা
Mean/median/std encoded-luma proxy এবং near-black/near-white শতাংশ JPEG-এ দৃশ্যমান pixel distribution বর্ণনা করে। এগুলো সরাসরি sensor dynamic range বা shadow recovery প্রমাণ করে না। Saturation proxy-ও color accuracy নয়।

## যাচাইয়ের সীমাবদ্ধতা
EXIF থেকে XML profile LMC-তে প্রয়োগ হয়েছে কি না নিশ্চিত করা যায় না। Profile label command line থেকে দেওয়া হয়। আলো, framing, exposure, HDR state ও capture order না মিললে profile-এর causal effect দাবি করা যাবে না। এই স্ক্রিপ্ট sensor noise, true dynamic range, color accuracy বা MTF50 পরিমাপের দাবি করে না।

## পরবর্তী পদক্ষেপ
1. `capture_manifest.csv`-এ timestamp, exposure time, ISO ও resolution পরীক্ষা করুন।
2. একই scene-এর ProBalanced এবং FullAllRounder/V9 ছবিগুলো আলাদা batch label দিয়ে চালান।
3. ChatGPT-তে `image_metrics.csv`, `capture_manifest.csv`, `audit_summary.json` ও `README_bn.md` একসঙ্গে দিন; scene pairing এবং limitations-সহ interpretation চাইুন।
