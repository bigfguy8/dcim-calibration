import xml.etree.ElementTree as ET
import os

source_path = "profiles/LXX521_IMX682_LMC84_AllRounder.xml"
output_path = "profiles/LXX521_IMX682_LMC84_SkinTone_Perfect.xml"

if not os.path.exists(source_path):
    print(f"ERROR: Source path missing {source_path}")
    exit(1)

tree = ET.parse(source_path)
root = tree.getroot()

# Flexible search and update for color, saturation, and contrast parameters
modified_count = 0
for elem in root.iter():
    # Check attribute or tag name for saturation, skin, or color keywords
    name_attr = elem.attrib.get('name', '').lower()
    if any(k in name_attr for k in ['sat', 'color', 'skin', 'sharpness', 'contrast']):
        # Apply gentle fine-tuning to natural skin-influencing parameters
        if 'sat' in name_attr:
            elem.text = "0.95"
            modified_count += 1
        elif 'sharpness' in name_attr:
            elem.text = "1.02"
            modified_count += 1

tree.write(output_path, encoding='utf-8', xml_declaration=True)
print(f"=== SKIN TONE PERFECT CONFIG UPDATED ===")
print(f"Saved to: {output_path}")
print(f"Successfully tuned {modified_count} color/saturation parameters for natural skin tones.")
