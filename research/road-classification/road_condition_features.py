#!/usr/bin/env python3
"""
road_condition_features.py  --  Navi-Gator road-condition exploration tool

GOAL (what the professor asked for):
  Take a few road chips cropped from NJGIN overhead imagery and figure out, in a
  measurable way, what separates a Level-5 road (great) from a Level-1 road
  (do-not-travel). This script turns the *visible* signals into numbers, scores
  each chip 1-5 with a transparent rule, and shows you WHY.

  It is NOT the CNN. It is the step before the CNN: it (a) proves the signal is
  real, (b) defines the features the CNN should learn, and (c) gives you a
  heuristic rater to bootstrap your first labeled training set.

WHAT IS VISIBLE FROM OVERHEAD (and so what we measure):
  edge_density   -> cracking (alligator/block/longitudinal). Smooth road = few
                    edges; cracked road = many. Usually the strongest signal.
  texture_entropy-> raveling / surface break-up. Smooth = low, gritty = high.
  dark_spot_frac -> potholes & dark patches (large dark blobs inside the road).
  blotchiness    -> patching/repairs & uneven aging (albedo varies across the slab).
  mean_brightness-> oxidation proxy (fresh asphalt is dark; aged is grey).
                    REPORTED ONLY, not scored: concrete roads are light and would
                    confound it.

NOT reliably visible from NJGIN ortho (don't pretend to classify these):
  rutting depth, ride roughness/IRI, hairline cracks below ~1 px, subsurface.

USAGE:
  python road_condition_features.py <image_or_folder> [--out OUTDIR] [--max-size 1200]

  Feed it road-cropped chips (crop tight to the pavement for best results).
  Outputs: a per-chip PNG panel (original / edges / texture / dark-spots),
           a printed feature table, and a worst->best ranking.
"""

import os, sys, argparse, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from skimage import io, color, img_as_float, img_as_ubyte, exposure
from skimage.feature import canny
from skimage.filters.rank import entropy
from skimage.morphology import disk, remove_small_objects
from skimage.measure import label

# ----------------------------------------------------------------------------
# CALIBRATION CONSTANTS  --  tune these on YOUR NJGIN chips. These defaults are
# starting points for ~6in/1ft orthoimagery. The ranking at the end is robust
# even if absolute thresholds are off, so use it to sanity-check your eye first.
# ----------------------------------------------------------------------------
EDGE_SIGMA       = 1.5     # Canny smoothing. Higher = only coarse cracks.
ENTROPY_DISK     = 5       # neighborhood radius for texture entropy.
DARK_PCTILE      = 8       # pixels darker than this percentile are "dark-spot" candidates.
DARK_MIN_FRAC    = 0.0008  # min blob size (fraction of chip) to count as a pothole/patch.

# Where each feature saturates to "fully bad" (badness = feature / SCALE, clipped 0..1)
EDGE_SCALE       = 0.14    # edge-pixel fraction at which cracking is maxed out
ENTROPY_SCALE    = 4.2     # mean local entropy (bits) at which texture is maxed out
DARK_SCALE       = 0.06    # dark-spot area fraction at which potholes are maxed out
BLOTCH_SCALE     = 0.22    # brightness std (0..1) at which patching is maxed out

# How much each distress contributes to the overall score (must sum to 1.0)
WEIGHTS = {"edges": 0.40, "entropy": 0.25, "darkspots": 0.20, "blotch": 0.15}

LEVEL_NAME = {5: "Excellent", 4: "Good", 3: "Fair", 2: "Poor", 1: "Do-Not-Travel"}
LEVEL_ROUTING = {
    5: "route freely (no penalty)",
    4: "minor wear (no penalty)",
    3: "passable (small routing penalty)",
    2: "avoid if alternative exists (heavy penalty)",
    1: "exclude from routing / last resort",
}


def load_gray(path, max_size):
    img = io.imread(path)
    if img.ndim == 3:
        if img.shape[2] == 4:
            img = img[:, :, :3]
        img = color.rgb2gray(img)
    # Convert to float [0,1] using the NATIVE tone values. We deliberately do
    # NOT per-image contrast-stretch: chips come from the same ortho capture, so
    # absolute brightness is a real oxidation signal, and stretching a smooth
    # road's sensor noise to full range would fabricate "cracks".
    g = img_as_float(img)
    h, w = g.shape
    if max(h, w) > max_size:
        step = int(np.ceil(max(h, w) / max_size))
        g = g[::step, ::step]
    return g


def extract_features(g):
    """Return (features dict, visualization layers dict)."""
    # --- cracking: edge density ---
    edges = canny(g, sigma=EDGE_SIGMA)
    edge_density = float(edges.mean())

    # --- texture: local entropy (raveling / break-up) ---
    gi = img_as_ubyte(g)
    ent = entropy(gi, disk(ENTROPY_DISK))
    texture_entropy = float(ent.mean())

    # --- potholes / dark patches: large dark blobs ---
    thr = np.percentile(g, DARK_PCTILE)
    dark = g < thr
    min_size = max(16, int(DARK_MIN_FRAC * g.size))
    dark = remove_small_objects(dark, min_size=min_size)
    dark_spot_frac = float(dark.mean())
    n_spots = int(label(dark).max())

    # --- patching / uneven aging: brightness spread ---
    blotchiness = float(g.std())

    # --- oxidation proxy (reported only) ---
    mean_brightness = float(g.mean())

    feats = dict(edge_density=edge_density, texture_entropy=texture_entropy,
                 dark_spot_frac=dark_spot_frac, n_dark_spots=n_spots,
                 blotchiness=blotchiness, mean_brightness=mean_brightness)
    viz = dict(edges=edges, entropy=ent, dark=dark)
    return feats, viz


def score(feats):
    """Transparent distress score -> 1..5 level. Each term is a 0..1 'badness'."""
    b_edges = min(feats["edge_density"] / EDGE_SCALE, 1.0)
    b_ent   = min(feats["texture_entropy"] / ENTROPY_SCALE, 1.0)
    b_dark  = min(feats["dark_spot_frac"] / DARK_SCALE, 1.0)
    b_blot  = min(feats["blotchiness"] / BLOTCH_SCALE, 1.0)
    distress = (WEIGHTS["edges"] * b_edges + WEIGHTS["entropy"] * b_ent +
                WEIGHTS["darkspots"] * b_dark + WEIGHTS["blotch"] * b_blot)
    level = int(np.clip(round(5 - 4 * distress), 1, 5))
    return distress, level, dict(edges=b_edges, entropy=b_ent, darkspots=b_dark, blotch=b_blot)


def panel(path, g, viz, feats, distress, level, outdir):
    fig, ax = plt.subplots(2, 2, figsize=(9, 9))
    ax[0, 0].imshow(g, cmap="gray"); ax[0, 0].set_title("Road chip (grayscale)")
    ax[0, 1].imshow(viz["edges"], cmap="magma"); ax[0, 1].set_title(f"Cracking / edges  ({feats['edge_density']*100:.2f}%)")
    ax[1, 0].imshow(viz["entropy"], cmap="viridis"); ax[1, 0].set_title(f"Texture entropy  ({feats['texture_entropy']:.2f})")
    ov = np.dstack([g, g, g]); ov[viz["dark"]] = [1, 0, 0]
    ax[1, 1].imshow(ov); ax[1, 1].set_title(f"Dark spots / potholes  ({feats['n_dark_spots']} blobs)")
    for a in ax.ravel(): a.axis("off")
    fig.suptitle(f"{os.path.basename(path)}   ->   LEVEL {level} ({LEVEL_NAME[level]})   "
                 f"| distress {distress:.2f}", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + "_analysis.png")
    fig.savefig(out, dpi=110); plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser(description="Navi-Gator road-condition feature explorer")
    ap.add_argument("target", help="image file or folder of road chips")
    ap.add_argument("--out", default="road_analysis_out")
    ap.add_argument("--max-size", type=int, default=1200)
    args = ap.parse_args()

    if os.path.isdir(args.target):
        paths = []
        for ext in ("*.tif", "*.tiff", "*.png", "*.jpg", "*.jpeg"):
            paths += glob.glob(os.path.join(args.target, ext))
            paths += glob.glob(os.path.join(args.target, ext.upper()))
        paths = sorted(set(paths))
    else:
        paths = [args.target]
    if not paths:
        sys.exit("No images found. Give an image file or a folder of road chips.")

    os.makedirs(args.out, exist_ok=True)
    rows = []
    print(f"\nAnalyzing {len(paths)} chip(s). Panels -> {args.out}/\n")
    hdr = f"{'file':<28}{'edges%':>8}{'texture':>9}{'darkspt':>9}{'blotch':>8}{'bright':>8}{'distress':>10}{'LEVEL':>7}"
    print(hdr); print("-" * len(hdr))
    for p in paths:
        try:
            g = load_gray(p, args.max_size)
        except Exception as e:
            print(f"{os.path.basename(p):<28}  !! could not read ({e})"); continue
        feats, viz = extract_features(g)
        distress, level, _ = score(feats)
        panel(p, g, viz, feats, distress, level, args.out)
        rows.append((os.path.basename(p), feats, distress, level))
        print(f"{os.path.basename(p):<28}{feats['edge_density']*100:>8.2f}{feats['texture_entropy']:>9.2f}"
              f"{feats['dark_spot_frac']*100:>8.2f}%{feats['blotchiness']:>8.3f}{feats['mean_brightness']:>8.3f}"
              f"{distress:>10.2f}{level:>7}")

    if len(rows) > 1:
        print("\nWorst -> best (does this match your eye? if yes, the features work):")
        for name, feats, distress, level in sorted(rows, key=lambda r: -r[2]):
            print(f"  LEVEL {level} ({LEVEL_NAME[level]:<13}) {name:<28} {LEVEL_ROUTING[level]}")
    print()


if __name__ == "__main__":
    main()
