import os, math
from PIL import Image, ExifTags

base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\latest_captures"
for f in sorted(os.listdir(base)):
    if f.endswith('.jpg') or f.endswith('.jpeg'):
        img = Image.open(os.path.join(base, f))
        exif = img._getexif()
        d = {}
        if exif:
            for tid, val in exif.items():
                tag = ExifTags.TAGS.get(tid, str(tid))
                d[tag] = val
        iso = d.get('ISOSpeedRatings')
        exp = d.get('ExposureTime')
        ev = None
        if iso and exp:
            try:
                if isinstance(exp, tuple): exp_s = exp[0]/exp[1]
                else: exp_s = float(exp)
                ev = round(math.log2(100.0/int(iso)/exp_s), 3)
            except: pass
        sw = d.get('Software', 'N/A')
        dt = d.get('DateTime', 'N/A')
        fl = d.get('FocalLength', 'N/A')
        print(f + " | " + str(img.size[0]) + "x" + str(img.size[1]) + " | ISO=" + str(iso) + " Exp=" + str(exp) + " EV=" + str(ev) + " FL=" + str(fl) + " SW=" + str(sw) + " DT=" + str(dt))
