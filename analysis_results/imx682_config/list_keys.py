import xml.etree.ElementTree as ET
tree = ET.parse(r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config\original_V2_Release_Day.xml")
root = tree.getroot()
keys = {}
for el in root.findall('string'):
    keys[el.get('name')] = el.text
print("Total keys:", len(keys))
print("\n--- Base keys (non-suffixed) ---")
for k in sorted(keys):
    if not any(k.endswith(suf) for suf in ['_2','_3','_4','_5','_front','_pro']):
        print(f"  {k}={keys[k]}")
