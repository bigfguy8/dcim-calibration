import os, json
from PIL import Image, ExifTags
import math

base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
files = sorted(os.listdir(base))
print("Total files:", len(files))

for f in files:
    img = Image.open(os.path.join(base, f))
    exif = img._getexif()
    exif_dict = {}
    if exif:
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            exif_dict[tag] = val

    iso = exif_dict.get('ISOSpeedRatings')
    exp = exif_dict.get('ExposureTime')
    ev = None
    if iso and exp:
        try:
            if isinstance(exp, tuple):
                exp_s = exp[0] / exp[1]
            else:
                exp_s = float(exp)
            ev = round(math.log2(100.0 / int(iso) / exp_s), 3)
        except:
            pass

    sw = exif_dict.get('Software', 'N/A')
    dt = exif_dict.get('DateTime', 'N/A')
    print(f"{f} | ISO={iso} Exp={exp} EV={ev} SW={sw} DT={dt}")
