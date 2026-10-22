import xml.etree.ElementTree as ET
base_dir = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
for name in ['original_V2_Release_Day', 'balanced', 'detail', 'lowlight']:
    tree = ET.parse(base_dir + "\\" + name + ".xml")
    root = tree.getroot()
    keys = {}
    for el in root.findall('string'):
        keys[el.get('name')] = el.text
    print("=== " + name + " ===")
    for k in ['cw_rg_key','lib_sharpnessb_key','lib_sharpnessb_key_2','lib_sharpnessb_key_3','lib_sharpnessb_key_4','lib_sharpnessb_key_5','lib_sharpnessb_key_front','lib_sharpgain_key','lib_sharpmini_key','lib_denoise_key','lib_lumadenoise_key','lib_lumanoise_key','lib_denoisesmoothing_key','pref_iso_noise_key','pref_camera_hdr_plus_key']:
        print("  " + k + "=" + keys.get(k, "NOT FOUND"))
    print()
