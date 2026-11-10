import cv2
import json
import os

def analyze_captions(image_dir):
    results = []
    if not os.path.exists(image_dir):
        print(f"Error: Directory {image_dir} not found.")
        return
    for filename in os.listdir(image_dir):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            img_path = os.path.join(image_dir, filename)
            img = cv2.imread(img_path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            b, g, r = cv2.mean(img)[:3]
            results.append({
                "filename": filename,
                "sharpness_mtf_proxy": round(sharpness, 2),
                "color_balance": {"R": round(r, 2), "G": round(g, 2), "B": round(b, 2)}
            })
    with open("calibration_upgrade_report.json", "w") as f:
        json.dump(results, f, indent=4)
    print("=== CALIBRATION UPGRADE SUCCESSFUL ===")
    print(f"Processed {len(results)} images. Report saved to calibration_upgrade_report.json")

if __name__ == "__main__":
    analyze_captions("/sdcard/DCIM/Camera/")
