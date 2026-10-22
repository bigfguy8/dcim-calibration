import os, json, hashlib, math
from PIL import Image, ExifTags

base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
files = sorted(os.listdir(base))

results = []
for f in files:
    path = os.path.join(base, f)
    img = Image.open(path)
    exif = img._getexif()
    exif_dict = {}
    raw_exif = {}
    if exif:
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            exif_dict[tag] = val
            raw_exif[tid] = val

    iso = exif_dict.get('ISOSpeedRatings')
    exp = exif_dict.get('ExposureTime')
    fnum = exif_dict.get('FNumber')
    fl = exif_dict.get('FocalLength')
    wb = exif_dict.get('WhiteBalance')
    flash = exif_dict.get('Flash')
    exp_prog = exif_dict.get('ExposureProgram')
    scene = exif_dict.get('SceneCaptureType')
    sw = exif_dict.get('Software')
    dt = exif_dict.get('DateTime')
    make = exif_dict.get('Make')
    model = exif_dict.get('Model')

    # Check raw ISO tag
    iso_raw = raw_exif.get(34855)  # ISOSpeedRatings tag ID

    # Check for additional ISO-related tags
    additional_iso = {}
    for tid, val in raw_exif.items():
        tag = ExifTags.TAGS.get(tid, str(tid))
        if 'iso' in tag.lower() or 'sensitivity' in tag.lower() or 'gain' in tag.lower():
            additional_iso[tag] = val

    ev = None
    exp_s = None
    if exp:
        try:
            if isinstance(exp, tuple):
                exp_s = exp[0] / exp[1]
            else:
                exp_s = float(exp)
        except:
            pass
    if iso and exp_s:
        try:
            ev = round(math.log2(100.0 / int(iso) / exp_s), 3)
        except:
            pass

    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()

    results.append({
        "filename": f,
        "width": img.size[0],
        "height": img.size[1],
        "sha256": h,
        "iso": iso,
        "iso_raw_tag": iso_raw,
        "additional_iso_tags": additional_iso,
        "exposure_time": str(exp),
        "exposure_seconds": exp_s,
        "ev": ev,
        "f_number": str(fnum),
        "focal_length": str(fl),
        "white_balance": wb,
        "flash": flash,
        "exposure_program": exp_prog,
        "scene_capture_type": scene,
        "software": sw,
        "datetime": dt,
        "make": make,
        "model": model,
        "all_exif_keys": list(exif_dict.keys()),
    })

# Save full inventory
with open(r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline_inventory.json", 'w') as f:
    json.dump(results, f, indent=2, default=str)

# Print summary
print("Total files:", len(results))
print("\nSoftware tags:")
from collections import Counter
sw_counts = Counter(r['software'] for r in results)
for sw, n in sw_counts.items():
    print(f"  {sw}: {n}")

print("\nISO range:", min(r['iso'] for r in results if r['iso']), "to", max(r['iso'] for r in results if r['iso']))
print("EV range:", min(r['ev'] for r in results if r['ev']), "to", max(r['ev'] for r in results if r['ev']))

# Check for additional ISO tags
print("\nAdditional ISO-related tags found:")
all_addl = set()
for r in results:
    all_addl.update(r['additional_iso_tags'].keys())
for tag in all_addl:
    print(f"  {tag}")
    vals = set(str(r['additional_iso_tags'].get(tag)) for r in results if tag in r['additional_iso_tags'])
    print(f"    Values: {vals}")

# Check for raw EXIF tag differences
print("\nFiles with 'ndy' suffix:")
for r in results:
    if 'ndy' in str(r['software']):
        print(f"  {r['filename']}: ISO={r['iso']} EV={r['ev']} Exp={r['exposure_seconds']}")
print("\nFiles with ISO > 10000:")
for r in results:
    if r['iso'] and int(r['iso']) > 10000:
        print(f"  {r['filename']}: ISO={r['iso']} EV={r['ev']} SW={r['software']}")
print("\nFiles with negative EV:")
for r in results:
    if r['ev'] is not None and r['ev'] < 0:
        print(f"  {r['filename']}: EV={r['ev']} ISO={r['iso']} SW={r['software']}")

# Check datetime range
dts = sorted(r['datetime'] for r in results if r['datetime'])
print("\nDatetime range:", dts[0], "to", dts[-1])

# Check exposure programs
ep_counts = Counter(r['exposure_program'] for r in results)
print("Exposure programs:", dict(ep_counts))

# Check scene capture types
sc_counts = Counter(r['scene_capture_type'] for r in results)
print("Scene capture types:", dict(sc_counts))

# Check white balance
wb_counts = Counter(r['white_balance'] for r in results)
print("White balance modes:", dict(wb_counts))
