# Sony IMX682 Custom Noise Model Guide for LMC 8.4

To achieve optimal noise reduction without losing detail on your Lava Play Ultra (IMX682):

1. **Obtain an IMX682 Noise Profile**:
   - Compatible `.noise.png` files for Sony 64MP sensors can be sourced from community repositories (like Celso Azevedo's noise profile collection or Telegram GCam groups).
2. **Placement**:
   - Place the `.noise.png` file directly into your phone's `/sdcard/LMC8.4/` directory alongside your XML profiles (`LXX521_UltimateSpeedCrisp.xml`).
3. **Linking in LMC 8.4**:
   - Open LMC Settings → Libpatcher → Noise Model / Custom Noise, and select the IMX682 profile.
