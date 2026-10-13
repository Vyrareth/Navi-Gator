# Navi-Gator — Road Condition Classification (1–5) from NJGIN Overhead Imagery

**Author:** Vyrareth · **Status:** research / scheme definition · **Sprint:** 2

This is the answer to "how do we classify a road's condition in the first place."
It defines the rating scale, what we can actually see from overhead, the visual
signals that separate a good road from a bad one, how to label a training set,
and how the label plugs into routing.

---

## 1. The key constraint: NJGIN is *top-down* imagery

NJGIN orthoimagery (statewide ortho, ~6 in–1 ft ground sample distance, finer in
some urban areas) is shot straight down. That decides what the classifier can and
can't learn. Build the rubric around what is **visible from above**, not around a
ground-level inspector's checklist.

| Reliably visible from overhead ✅ | NOT reliably visible ❌ |
|---|---|
| Cracking patterns (alligator/block/longitudinal) — as texture/edges | Rutting depth |
| Patching & repairs (albedo mismatch) | Ride roughness / IRI |
| Potholes & large dark depressions (dark blobs) | Hairline cracks below ~1 px |
| Surface oxidation/aging (fresh = dark, old = grey) | Subsurface / base failure |
| Raveling / surface break-up (texture) | Friction / skid resistance |
| Faded or missing lane markings | |
| Edge crumbling, vegetation in cracks, standing water | |

**Design consequence:** we grade *coarse surface distress*, and we are honest that
we are **not** measuring ride quality. That's a defensible scope for a class project
and it's what the imagery supports.

---

## 2. Grounding: this is a real discipline (don't invent a scale)

Pavement condition rating is standardized. We anchor to these so our scale isn't
arbitrary:

- **PASER** (Pavement Surface Evaluation and Rating) — a **visual surface** 1–10 scale
  used by DOTs. Closest match to what we're doing; we compress 10→5.
- **PCI** (Pavement Condition Index) — 0–100, distress-based.
- **FHWA HPMS** — uses IRI + % cracking (we already cite HPMS as a data source).

Our 1–5 scale = PASER compressed, restricted to overhead-visible distress.

| Navi-Gator | PASER (approx) | PCI (approx) |
|:--:|:--:|:--:|
| 5 | 9–10 | 85–100 |
| 4 | 7–8  | 70–85 |
| 3 | 5–6  | 55–70 |
| 2 | 3–4  | 40–55 |
| 1 | 1–2  | 0–40 |

---

## 3. The rubric — what each level *looks like from above*

For each level: the visual description a human labeler uses, and the direction of
the measured features (from `road_condition_features.py`).

### Level 5 — Excellent  ·  *route freely (no penalty)*
- **Looks like:** uniform dark/near-black asphalt, smooth, no visible cracks,
  crisp lane markings, clean edges.
- **Features:** low edge density, low texture entropy, no dark spots, low
  blotchiness, low mean brightness (dark = fresh).

### Level 4 — Good  ·  *minor wear (no penalty)*
- **Looks like:** mostly uniform, slightly greyer (early oxidation), a few short
  isolated cracks or one small patch, markings intact.
- **Features:** low–moderate edges, low texture, 0–1 small dark spots.

### Level 3 — Fair  ·  *passable (small routing penalty)*
- **Looks like:** clearly grey/aged, scattered longitudinal/transverse cracks or
  several patches (blotchy surface), markings fading.
- **Features:** moderate edges, moderate texture & blotchiness, maybe 1–2 dark spots.

### Level 2 — Poor  ·  *avoid if an alternative exists (heavy penalty)*
- **Looks like:** connected/alligator cracking over a noticeable area, multiple
  patches, one or more potholes, ragged edges, maybe vegetation in cracks.
- **Features:** high edges, high texture entropy, several dark spots, high blotchiness.

### Level 1 — Do-Not-Travel / Failed  ·  *exclude from routing*
- **Looks like:** extensive alligator cracking across most of the surface, many
  potholes, crumbling/washed-out edges, standing water, surface barely intact.
- **Features:** very high edges + texture + dark-spot area; surface looks shattered.

---

## 4. The measurable signals (what the tool computes, what the CNN learns)

These are the handles that separate the levels. The script quantifies each so you
can *see* the separation; later the CNN learns them implicitly.

| Feature | Distress it captures | Good → Bad direction |
|---|---|---|
| **edge_density** (Canny) | cracking | low → high  *(strongest single signal)* |
| **texture_entropy** (local entropy) | raveling / break-up | low → high |
| **dark_spot_frac / count** | potholes & dark patches | none → many |
| **blotchiness** (brightness std) | patching / uneven aging | low → high |
| **mean_brightness** | oxidation/age *(reported, not scored — concrete confounds it)* | dark → grey |

Weights in the heuristic score: edges 0.40, texture 0.25, dark-spots 0.20,
blotch 0.15 → distress 0..1 → `level = round(5 − 4·distress)`. All constants live
at the top of `road_condition_features.py` and are meant to be **calibrated on real
NJGIN chips** (the worst→best *ranking* is robust even before you calibrate).

---

## 5. How to get the pictures (what the professor asked you to do first)

You need a handful of road chips at a few condition levels. Three ways:

1. **Use our own auto-screenshot tool (Cris).** It already zooms to a coordinate
   on NJGIN and saves a snapshot — that's literally a chip generator. Point it at
   a few roads you know (a freshly paved street vs. a beat-up one).
2. **NJGIN Open Data / ArcGIS image service.** The NJ statewide orthoimagery is an
   ArcGIS image service; its `exportImage` REST endpoint returns a PNG/TIFF for a
   lat/long bounding box at full resolution. Grab 400–800 px chips centered on road
   segments. (njgin.nj.gov / NJ OGIS open-data portal.)
3. **NJ imagery viewer / aerial basemap** — pan to a road, screenshot, crop tight
   to the pavement.

**Crop tight to the road surface** before analysis — grass/roofs/cars add edges and
texture that aren't pavement distress. (Don's road-mask preprocessing will automate
this crop later; for "playing around" now, crop by hand.)

---

## 6. Play-around workflow (run it today)

```bash
# one-time
pip install numpy scikit-image matplotlib scipy

# drop a few cropped chips in a folder, then:
python road_condition_features.py my_chips/ --out analysis

# prints a feature table + a worst->best ranking, and writes a 4-panel PNG per chip
# (original / cracking-edges / texture / detected potholes).
```

Pick 2 roads you *know* are good and bad, run it, and check the ranking matches your
eye. Then tune the constants at the top until the Level cutoffs feel right on NJ
imagery. That table + the panels **is** your "here's how I'd classify it" evidence.

---

## 7. From rubric → CNN training set

The rubric isn't just documentation — it's the **labeling guide** for the dataset the
CNN needs:

1. Collect chips (step 5), one road segment per chip, consistent size (e.g. 256×256).
2. A human labels each chip 1–5 using Section 3. Use the tool's output to stay
   consistent and to break ties (if two labelers disagree, the feature numbers arbitrate).
3. Record every label in `road_labels_template.csv` (chip filename, lat/long,
   assigned level, who labeled it, notes).
4. Aim for a roughly balanced set across the 5 levels (bad roads are rarer — oversample them).
5. Train the CNN on (chip → level). The heuristic score is the **bootstrap**: it
   pre-sorts a big pile of chips so humans only confirm/correct, which is far faster
   than labeling from scratch.

---

## 8. From level → routing (closing the loop)

Each Level becomes an **edge weight multiplier** in the routing graph (Dijkstra/A*),
so the shortest *good* route beats the shortest *bad* one:

| Level | Routing effect | Example cost multiplier |
|:--:|---|:--:|
| 5 | free | ×1.0 |
| 4 | free | ×1.1 |
| 3 | small penalty | ×1.5 |
| 2 | heavy penalty | ×3.0 |
| 1 | exclude / last resort | ×∞ (or ×10) |

That's the whole product thesis in one table: *classify the surface from imagery,
turn the class into a cost, route around the bad roads.*

---

## 9. Honest limitations (say these out loud)

- Overhead ≠ ride quality. We grade visible surface distress, not IRI/rutting.
- Resolution caps us at coarse distress; hairline cracking won't register.
- Shadows, tree cover, cars, and wet pavement can mislead features — the CNN will
  need enough varied examples to be robust, and chips must be cropped to pavement.
- Concrete vs. asphalt differ in albedo — that's why brightness is reported, not scored.
