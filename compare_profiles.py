import xml.etree.ElementTree as ET

def parse_xml_params(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        params = {}
        for elem in root.iter():
            if 'name' in elem.attrib and ('value' in elem.attrib or elem.text):
                key = elem.attrib['name']
                val = elem.attrib.get('value', elem.text)
                params[key] = val
        return params
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {}

def compare_profiles(master_path, target_path):
    master = parse_xml_params(master_path)
    target = parse_xml_params(target_path)
    
    print(f"Comparing {target_path} against Master: {master_path}\n")
    
    all_keys = sorted(set(master.keys()).union(set(target.keys())))
    diff_count = 0
    
    for k in all_keys:
        m_val = master.get(k, "NOT_PRESENT")
        t_val = target.get(k, "NOT_PRESENT")
        if m_val != t_val:
            print(f"Param: {k}")
            print(f"  Master: {m_val}")
            print(f"  Target: {t_val}\n")
            diff_count += 1
            
    print(f"Total differences found: {diff_count}")

if __name__ == "__main__":
    master_file = "LXX521_IMX682_AllInOne_Master.xml"
    target_file = "LXX521_IMX682_MaxQuality.xml"
    compare_profiles(master_file, target_file)
