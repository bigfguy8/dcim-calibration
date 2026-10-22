import xml.etree.ElementTree as ET
base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"

def get_keys(path):
    tree = ET.parse(path)
    root = tree.getroot()
    keys = {}
    for el in root.findall("string"):
        keys[el.get("name")] = el.text
    return keys

baseline = get_keys(base + "\\original_V2_Release_Day.xml")
optimized = get_keys(base + "\\LXX521_LMC84_Optimized.xml")

changes = ["cw_rg_key", "lib_sharpnessb_key", "lib_sharpgain_key", "lib_sharpmini_key"]
print("Key comparison (Baseline vs Optimized):")
for k in changes:
    print("  " + k + ": " + baseline[k] + " -> " + optimized[k])

# Verify no other differences
diff_keys = []
for name in baseline:
    if baseline[name] != optimized.get(name):
        diff_keys.append(name)
for name in optimized:
    if name not in baseline:
        diff_keys.append(name)

print("\nTotal differing keys: " + str(len(diff_keys)))
if len(diff_keys) > 4:
    print("WARNING: More than 4 keys differ:")
    for k in diff_keys:
        print("  " + k + ": baseline=" + baseline.get(k, "N/A") + " optimized=" + optimized.get(k, "N/A"))
else:
    print("OK: Exactly 4 keys differ as intended.")
