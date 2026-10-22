import json
m = json.load(open(r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline_selection_manifest.json"))
print("Selected:", m['selected_count'])
print("Extras:", m['extras_count'])
print("Excluded:", m['excluded_count'])
print()
for scene, info in m['scenes'].items():
    print(scene + ": " + str(info["count"]) + "/3 (shortfall: " + str(info["shortfall"]) + ")")
    for img in info['images']:
        print("  " + img)
print()
if 'shortfalls' in m:
    print("SHORTFALLS:")
    for s in m['shortfalls']:
        print("  " + s)
print()
print("Extras:")
for e in m['extras']:
    print("  " + e)
print()
print("Excluded:")
for e in m['excluded']:
    print("  " + e)
