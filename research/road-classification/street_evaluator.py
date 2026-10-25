#!/usr/bin/env python3
"""
street_evaluator.py  --  Navi-Gator: rate ONE street from its segment screenshots.

This is the last stage of the demo pipeline:
  Don's coordinates -> Cris's auto-clicker screenshots each segment as a PNG
  -> THIS program scores every segment 1-5 and gives the street an overall rating.

It uses the texture-based metric calibrated on real NJGIN roads (3.65 = clean = 5,
4.40 = wrecked = 1). Point it at the folder of a single street's segment PNGs, e.g.
the "CC_14H_Chews_Landing_Road_###.png" files from the auto-clicker.

USAGE:
  python street_evaluator.py <folder> [--street "Chews_Landing_Road"] [--crop 0.6] [--out results]
"""
import os, re, sys, argparse
import numpy as np
from PIL import Image
from skimage import img_as_float, img_as_ubyte, color
from skimage.filters.rank import entropy
from skimage.morphology import disk
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- calibrated metric (from the 4 real NJGIN roads) ----
TEX_GOOD, TEX_BAD = 3.65, 4.40
NAME = {5: "Excellent", 4: "Good", 3: "Fair", 2: "Poor", 1: "Do-Not-Travel"}

def load_gray(path, crop):
    img = np.array(Image.open(path).convert("L"))
    g = img_as_float(img)
    if crop < 1.0:                       # center-crop to focus on the road, drop the edges/surroundings
        h, w = g.shape
        ch, cw = int(h * crop), int(w * crop)
        top, left = (h - ch) // 2, (w - cw) // 2
        g = g[top:top + ch, left:left + cw]
    return g

def rate(g):
    texture = float(entropy(img_as_ubyte(g), disk(5)).mean())
    distress = float(np.clip((texture - TEX_GOOD) / (TEX_BAD - TEX_GOOD), 0, 1))
    level = int(np.clip(round(5 - 4 * distress), 1, 5))
    return texture, distress, level

def seg_index(fname):
    m = re.search(r"(\d+)\.\w+$", fname)   # trailing number before the extension
    return int(m.group(1)) if m else 0

def main():
    ap = argparse.ArgumentParser(description="Rate one street from its segment screenshots")
    ap.add_argument("folder", help="folder of this street's segment PNG/TIFF files")
    ap.add_argument("--street", default="", help="only files whose name contains this text")
    ap.add_argument("--crop", type=float, default=0.6, help="center-crop fraction (0.6 = keep middle 60%)")
    ap.add_argument("--out", default="street_results")
    args = ap.parse_args()

    files = [f for f in sorted(os.listdir(args.folder))
             if f.lower().endswith((".png", ".tif", ".tiff", ".jpg", ".jpeg"))
             and (args.street.lower() in f.lower())]
    if not files:
        sys.exit("No matching segment images found in that folder.")
    os.makedirs(args.out, exist_ok=True)

    rows = []
    for f in sorted(files, key=seg_index):
        try:
            g = load_gray(os.path.join(args.folder, f), args.crop)
        except Exception as e:
            print(f"  skip {f}: {e}"); continue
        texture, distress, level = rate(g)
        rows.append((f, seg_index(f), texture, level, g))

    # ---- per-segment table ----
    print(f"\nStreet evaluation — {args.street or os.path.basename(os.path.abspath(args.folder))}")
    print(f"{'segment':>8}  {'texture':>8}  {'LEVEL':>5}  condition")
    print("-" * 44)
    for f, idx, texture, level, _ in rows:
        print(f"{idx:>8}  {texture:>8.2f}  {level:>5}  {NAME[level]}")

    levels = [r[3] for r in rows]
    avg = round(sum(levels) / len(levels), 1)
    worst = min(levels)
    worst_seg = min(rows, key=lambda r: r[3])[1]
    print("-" * 44)
    print(f"SEGMENTS: {len(rows)}   STREET AVERAGE: {avg}/5   "
          f"WORST SEGMENT: #{worst_seg} = {worst} ({NAME[worst]})")
    print(f"Routing note: a street is only as drivable as its worst segment -> "
          f"use level {worst} for routing cost.\n")

    # ---- visualization: each segment tile labeled with its level ----
    n = len(rows)
    cols = min(n, 6); rowsN = (n + cols - 1) // cols
    fig, axes = plt.subplots(rowsN, cols, figsize=(2.3 * cols, 2.6 * rowsN))
    axes = np.array(axes).reshape(-1)
    colr = {5: "#166534", 4: "#4d7c0f", 3: "#ca8a04", 2: "#c2410c", 1: "#b91c1c"}
    for ax, (f, idx, texture, level, g) in zip(axes, rows):
        ax.imshow(g, cmap="gray"); ax.axis("off")
        ax.set_title(f"#{idx} -> {level} ({NAME[level]})", fontsize=9, color=colr[level])
    for ax in axes[len(rows):]:
        ax.axis("off")
    fig.suptitle(f"{args.street or 'Street'}  |  avg {avg}/5, worst {worst}", fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(args.out, "street_rating.png")
    fig.savefig(out, dpi=110); plt.close()
    print(f"visual saved -> {out}")

if __name__ == "__main__":
    main()
