"""
road_classifier.py - load the trained Navi-Gator road-condition CNN and rate roads.

You do NOT need any of the training code to use this. You DO need the trained model file
**road_cnn.keras** sitting in the SAME folder as this file. It ships with this file in the
repo (backend/cnn/road_cnn.keras), so a normal `git clone` / `git pull` gets both together.
If you copied only this .py, download road_cnn.keras into the same folder before running.

Usage:
    from road_classifier import load_model, classify_folder

    model = load_model()                        # loads road_cnn.keras from this folder
    ratings = classify_folder("some_folder", model)
    print(ratings)

Each result looks like:
    {"D13D10_Westfield_Avenue": {"average": 3.4, "worst": 2, "best": 5, "segments": 117}}

Scale: 5 = Excellent (route freely) ... 1 = Do-Not-Travel (avoid).
The images are prepped exactly the way the model was trained, so results stay consistent.

Requirements:  pip install tensorflow numpy pillow
"""
import os
import numpy as np
from PIL import Image
import tensorflow as tf

IMG_SIZE = 128
MODEL_PATH = os.path.join(os.path.dirname(__file__), "road_cnn.keras")


def load_model(path=MODEL_PATH):
    """Load the trained CNN from disk (road_cnn.keras)."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            "\n\nroad_cnn.keras was not found next to road_classifier.py.\n"
            "It lives in the repo at backend/cnn/road_cnn.keras and ships with this file -\n"
            "a normal 'git clone' / 'git pull' gets it. If you only copied the .py, download\n"
            "road_cnn.keras into the same folder as this script and run again.\n"
        )
    return tf.keras.models.load_model(path)


def parse_segment(filename):
    """'CC_1H_Burlington_Pike_000.png' -> ('CC_1H_Burlington_Pike', 0)."""
    name = filename.rsplit(".", 1)[0]       # drop the .png
    road_key, seg = name.rsplit("_", 1)     # split off the trailing number
    return road_key, int(seg)


def prep_image(path):
    """Load one segment and prep it the SAME way the model was trained on."""
    image = Image.open(path).convert("L")
    width, height = image.size
    left = int(width * 0.1)
    top = int(height * 0.1)
    image = image.crop((left, top, width - left, height - top))
    image = image.resize((IMG_SIZE, IMG_SIZE))
    return np.array(image) / 255.0


def classify_folder(folder, model):
    """Rate every road in a folder of segment screenshots.

    Returns {road_key: {"average", "worst", "best", "segments"}} on the 1-5 scale.
    """
    # group the prepped images by road
    roads = {}
    for filename in sorted(os.listdir(folder)):
        if not filename.lower().endswith((".png", ".jpg", ".tif")):
            continue
        road_key, seg = parse_segment(filename)
        if road_key not in roads:
            roads[road_key] = []
        roads[road_key].append(prep_image(os.path.join(folder, filename)))

    # run the model per road and average the segment levels
    results = {}
    for road_key in roads:
        images = np.array(roads[road_key]).reshape(len(roads[road_key]), IMG_SIZE, IMG_SIZE, 1)
        levels = np.argmax(model.predict(images, verbose=0), axis=1) + 1
        results[road_key] = {
            "segments": len(levels),
            "average": round(float(levels.mean()), 1),
            "worst": int(levels.min()),
            "best": int(levels.max()),
        }
    return results


# quick test:  python road_classifier.py <folder>
if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "r2_segments"
    model = load_model()
    for road_key, r in classify_folder(folder, model).items():
        print(f"{road_key}: avg {r['average']}/5  "
              f"(worst {r['worst']}, best {r['best']}, {r['segments']} segments)")
