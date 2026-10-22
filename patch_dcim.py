from pathlib import Path

p = Path("imx682_opencv_calibration.py")
s = p.read_text(encoding="utf-8")

old = '''    # MTF50 (simplified ESF on strongest edge)
    # Find strongest horizontal edge via gradient
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2+gy**2)
    # Top edge location
    edge_rows = np.argsort(mag.mean(axis=1))[-5:]
    mtf50 = 0.0
    if len(edge_rows) > 0:
        # ESF along middle column of top edge row
        row = int(edge_rows[-1])
        esf = gray[row, :].astype(float)
        # Derive LSF
        lsf = np.diff(esf)
        lsf = np.abs(lsf)
        if lsf.max() > 0:
            lsf /= lsf.max()
            # MTF = |FFT(LSF)|
            mtf = np.abs(np.fft.rfft(lsf))
            mtf /= mtf[0] if mtf[0]>0 else 1
            freqs = np.fft.rfftfreq(len(lsf))
            # MTF50 = freq where MTF drops to 0.5
            idx = np.where(mtf < 0.5)[0]
            mtf50 = float(freqs[idx[0]]) if len(idx)>0 else float(freqs[-1])
'''

new = '''    # MTF50 withheld: this is not a validated slanted-edge SFR method.
    mtf50 = None
    mtf50_status = (
        "NOT_MEASURED: validated slanted-edge SFR required"
    )
'''

if old not in s:
    raise SystemExit(
        "Expected MTF block not found; source unchanged."
    )

old_field = '''        "mtf50_cyc_px": mtf50,
'''
new_field = '''        "mtf50_cyc_px": mtf50,
        "mtf50_status": mtf50_status,
'''

if s.count(old_field) != 1:
    raise SystemExit(
        "Expected exactly one MTF result field; source unchanged."
    )

old_print = '''        print(f"  {r['classification']} | EV={r['ev']} | MTF50={r['mtf50_cyc_px']:.4f} | edge={r['edge_density']:.3%}")
'''
new_print = '''        mtf_value = r["mtf50_cyc_px"]
        mtf_text = (
            f"{mtf_value:.4f}"
            if mtf_value is not None
            else "NOT MEASURED"
        )
        print(
            f"  {r['classification']} | EV={r['ev']} "
            f"| MTF50={mtf_text} | edge={r['edge_density']:.3%}"
        )
'''

old_plot = '''        mtfs = [r['mtf50_cyc_px'] for r in results]
        colors = ['green' if r['has_checkerboard'] else 'gray' for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
'''

new_plot = '''        # No validated MTF50 measurements are available.
        mtfs = [0.0 for _ in results]
        colors = ['green' if r['has_checkerboard'] else 'gray' for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
        ax.text(
            0.5, 0.5,
            "MTF50 unavailable: validated slanted-edge SFR required",
            transform=ax.transAxes, ha="center", va="center",
            wrap=True
        )
'''

for old_block, new_block, label in (
    (old_field, new_field, "result field"),
    (old_print, new_print, "console output"),
    (old_plot, new_plot, "plot block"),
):
    if s.count(old_block) != 1:
        raise SystemExit(
            f"Expected exactly one {label}; source unchanged."
        )
    s = s.replace(old_block, new_block, 1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Patch applied:", p)
