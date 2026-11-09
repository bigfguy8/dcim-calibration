#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request

app = Flask(__name__)

DEFAULT_MASTER = "LXX521_IMX682_AllInOne_Master.xml"
DEFAULT_TARGET = "LXX521_IMX682_MaxQuality.xml"
DEFAULT_STORAGE_DIR = "/sdcard/LMC8.4/"

def parse_xml_params(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found -> {filepath}")
        return {}
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
    print(f"\n[INFO] Comparing target: {target_path}")
    print(f"[INFO] Against master: {master_path}\n")
    
    master = parse_xml_params(master_path)
    target = parse_xml_params(target_path)
    
    if not master or not target:
        print("[ERROR] Profile comparison failed due to missing files.")
        return
    
    all_keys = sorted(set(master.keys()).union(set(target.keys())))
    diff_count = 0
    
    for k in all_keys:
        m_val = master.get(k, "NOT_PRESENT")
        t_val = target.get(k, "NOT_PRESENT")
        if m_val != t_val:
            print(f"Parameter: {k}")
            print(f"  Master: {m_val}")
            print(f"  Target: {t_val}\n")
            diff_count += 1
            
    print(f"[INFO] Total differences found: {diff_count}")

def deploy_profile(profile_filename, destination_dir=DEFAULT_STORAGE_DIR):
    if not os.path.exists(profile_filename):
        print(f"[ERROR] Profile {profile_filename} does not exist locally.")
        return False
    
    os.makedirs(destination_dir, exist_ok=True)
    dest_path = os.path.join(destination_dir, profile_filename)
    
    try:
        with open(profile_filename, 'r', encoding='utf-8') as src, open(dest_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        print(f"[SUCCESS] Deployed {profile_filename} to {dest_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        return False

@app.route('/')
def dashboard_home():
    return jsonify({
        "status": "online",
        "service": "DCIM Calibration Pipeline Dashboard",
        "endpoints": {
            "/profiles": "List available local XML profiles",
            "/deploy?profile=<filename>": "Deploy profile to storage"
        }
    })

@app.route('/profiles')
def list_profiles():
    files = [f for f in os.listdir('.') if f.endswith('.xml')]
    return jsonify({"available_xml_profiles": files})

@app.route('/deploy', methods=['GET'])
def api_deploy():
    profile = request.args.get('profile', DEFAULT_MASTER)
    success = deploy_profile(profile)
    if success:
        return jsonify({"status": "success", "deployed": profile}), 200
    return jsonify({"status": "error", "message": "Deployment failed"}), 500

def print_menu():
    print("==================================================")
    print("      DCIM Calibration & Deployment Pipeline      ")
    print("==================================================")
    print(" [1] Compare Master and MaxQuality Profiles")
    print(" [2] Deploy XML Profile to Phone Storage")
    print(" [3] Start Flask Control Dashboard")
    print(" [q] Quit")
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "compare":
            compare_profiles(DEFAULT_MASTER, DEFAULT_TARGET)
        elif sys.argv[1] == "server":
            app.run(host='0.0.0.0', port=5000, debug=False)
        else:
            print("Unknown argument. Use 'compare' or 'server'.")
    else:
        while True:
            print_menu()
            choice = input("Enter choice: ").strip()
            if choice == '1':
                compare_profiles(DEFAULT_MASTER, DEFAULT_TARGET)
            elif choice == '2':
                filename = input("Enter XML filename to deploy (e.g., LXX521_IMX682_MaxQuality.xml): ").strip()
                deploy_profile(filename)
            elif choice == '3':
                print("[INFO] Starting Flask dashboard on port 5000...")
                app.run(host='0.0.0.0', port=5000, debug=False)
            elif choice.lower() == 'q':
                print("Exiting. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
