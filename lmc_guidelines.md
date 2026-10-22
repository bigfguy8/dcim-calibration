# LMC 8.4 Operational Guidelines: Lava Play Ultra (LXX521 / IMX682)

This guide outlines the recommended in-app settings to get the absolute best performance, zero shutter lag, and maximum crispness from your Sony IMX682 sensor using LMC 8.4.

---

## 1. Essential In-App Settings (LMC Settings Menu)
Tap the dropdown arrow at the top of LMC 8.4, go to **LMC Settings**, and configure the following:

* **Libpatcher**: **Enabled** (Required for custom sharpness, denoise, and tone curves to take effect).
* **AWB (Auto White Balance)**: Set to **Pixel 7 Pro** or **IMX682 Custom** for accurate, natural skin tones and balanced whites.
* **HDR+ Quality / Frames**: Set to **Default (7–9 frames)**. This strikes the optimal balance between high dynamic range and lightning-fast shutter response.
* **Sabre Merging**: **Enabled** (Enhances detail and reduces high-ISO noise in low light).

---

## 2. Shooting Modes & Performance Tips

* **For Fast Action / Street Photography**:
  - Ensure HDR+ Enhanced is toggled off if you need instant point-and-shoot snaps with zero processing delay.
* **For Landscapes / Maximum Detail**:
  - Use HDR+ Enhanced, hold the phone steady for 1 second after pressing the shutter to allow multi-frame stacking to lock in maximum texture.
* **Low Light / Night Shots**:
  - Rely on the built-in Astro/Night mode settings embedded in the profile. Keep your hands steady for 2–3 seconds.

---

## 3. Profile Activation Steps
1. Run `python workflow_master.py` in Termux and choose deploy.
2. Select **`LXX521_UltimateSpeedCrisp.xml`**.
3. Open LMC 8.4, **double-tap** the black space beside the shutter button.
4. Select `LXX521_UltimateSpeedCrisp.xml` from the list and tap **Import**.
