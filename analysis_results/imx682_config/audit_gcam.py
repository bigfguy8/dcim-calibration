import xml.etree.ElementTree as ET
import os

gcam_dir = r"C:\Users\l\AppData\Local\Temp\opencode\lxx521_configs"
for root, dirs, files in os.walk(gcam_dir):
    for f in files:
        if f.endswith('.xml'):
            path = os.path.join(root, f)
            try:
                tree = ET.parse(path)
                r = tree.getroot()
                keys = [el.get('name') for el in r.findall('string')]
                lmc_style = sum(1 for k in keys if k and ('lib_' in k or 'cw_rg' in k or 'pref_camera_hdr_plus' in k))
                print(f"{f}: root={r.tag}, keys={len(keys)}, lmc_style={lmc_style}")
            except Exception as e:
                print(f"{f}: ERROR {str(e)[:50]}")
