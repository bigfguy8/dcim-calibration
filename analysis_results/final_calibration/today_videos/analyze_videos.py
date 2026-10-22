import os, cv2, numpy as np

base = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\today_videos"
videos = sorted(os.listdir(base))
for v in videos:
    if v.endswith('.mp4'):
        path = os.path.join(base, v)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(v + " | COULD NOT OPEN")
            continue
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        dur = total / fps if fps > 0 else 0

        # Sample sharpness
        interval = max(1, total // 20)
        sharpness = []
        brightness = []
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            if idx % interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                lap = cv2.Laplacian(gray, cv2.CV_64F)
                sharpness.append(float(np.var(lap)))
                brightness.append(float(np.mean(gray)))
            idx += 1
        cap.release()

        sharp_arr = np.array(sharpness)
        bright_arr = np.array(brightness)
        print(v + " | " + str(w) + "x" + str(h) + " | " + str(round(fps,2)) + "fps | " + str(total) + " frames | " + str(round(dur,1)) + "s")
        print("  Sharpness: mean=" + str(round(np.mean(sharp_arr),1)) + " min=" + str(round(np.min(sharp_arr),1)) + " max=" + str(round(np.max(sharp_arr),1)) + " CV=" + str(round(np.std(sharp_arr)/np.mean(sharp_arr),3)))
        print("  Brightness: mean=" + str(round(np.mean(bright_arr),1)) + " std=" + str(round(np.std(bright_arr),1)))
        print()
