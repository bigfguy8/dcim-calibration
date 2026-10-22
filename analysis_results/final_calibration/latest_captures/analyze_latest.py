import os, cv2, numpy as np
from PIL import Image

base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\latest_captures"
for f in sorted(os.listdir(base)):
    if f.endswith('.jpg') or f.endswith('.jpeg'):
        path = os.path.join(base, f)
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            print(f + " | COULD NOT READ")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        lum = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:,:,0].astype(float)
        b, g, r = cv2.split(img)
        edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
        edge_density = float(np.sum(edges > 0) / edges.size)
        black_clip = float(np.sum(gray.astype(np.uint8) <= 5) / gray.size * 100)
        white_clip = float(np.sum(gray.astype(np.uint8) >= 250) / gray.size * 100)
        rb_ratio = float(np.mean(r) / np.mean(b)) if np.mean(b) > 0 else 0
        rg_diff = float(np.mean(r) - np.mean(g))
        print(f + " | " + str(w) + "x" + str(h) + " | lum_mean=" + str(round(np.mean(lum),1)) + " lum_std=" + str(round(np.std(lum),1)) + " edge=" + str(round(edge_density,3)) + " black=" + str(round(black_clip,2)) + "% white=" + str(round(white_clip,2)) + "% R/B=" + str(round(rb_ratio,3)) + " R-G=" + str(round(rg_diff,1)))
