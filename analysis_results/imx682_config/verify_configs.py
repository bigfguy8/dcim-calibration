import xml.etree.ElementTree as ET, hashlib, os
base_dir = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
for name in ["original_V2_Release_Day", "balanced", "detail", "lowlight", "LXX521_LMC84_Optimized"]:
    path = os.path.join(base_dir, name + ".xml")
    tree = ET.parse(path)
    root = tree.getroot()
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(name + ": keys=" + str(len(root.findall("string"))) + ", size=" + str(len(open(path, "rb").read())) + ", sha256=" + h[:16] + "...")
