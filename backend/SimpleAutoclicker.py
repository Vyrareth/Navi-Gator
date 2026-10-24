# =====================================================================================
# SimpleAutoclicker.py   (Windows)   V1.2
# Part of Navi-Gator - screenshots road boxes from any sector image for the CNN dataset.
# =====================================================================================
# WHAT IT DOES
#   Takes a box on a sector image (upper-left corner + lower-right corner, in pixels)
#   and for each box:
#     1. opens the image full-screen, centered on the box, starting 3 zoom notches out
#     2. clicks once to give the window focus, then the autoclicker scrolls the mouse
#        wheel to zoom in until one more notch would cut off part of the box
#        (if a scroll doesn't register, it zooms anyway so it never gets stuck)
#     3. zooms the last bit so the box touches the screen edges, moves the cursor
#        out of the way and screenshots exactly the box
#     4. saves it as a lossless .png in a folder named after the sector file:
#        <Sector>/<Sector>_001.png, _002.png, ...  (never overwrites earlier shots)
#   The sector name comes from the file name:  CC_9C.tif -> CC_9C
#   .tif files are read with rasterio and contrast-stretched to normal 8-bit colors.
#
# SETUP BEFORE RUNNING
#   1. Set Windows display scaling to 100%
#        Settings -> System -> Display -> Scale -> 100%
#        (otherwise the screenshot grabs the wrong area)
#   2. Put this file, connect_sector_direct.py and sectorCoordinateProcessor.py
#      in the same folder. The sector .tif can be anywhere.
#   3. Close or minimize anything that could pop up on top of the screen.
#   4. Once it starts, don't touch the mouse - it clicks and scrolls by itself.
#HOW TO RUN
#   Whole sector (normal way):  python connect_sector_direct.py <Sector>.tif
#        finds every road box in the sector and screenshots each one; pictures are
#        renamed to <Sector>/<Sector>_<Road_Name>_000.png
#        (see connect_sector_direct.py for more options)
#   One box (test):             python SimpleAutoclicker.py
#        uses the capture((ULx, ULy), (LRx, LRy), "<Sector>.tif") line at the bottom -
#        change the coordinates and file name there
#
#   Press Esc to stop. In a connect_sector_direct.py run this stops the whole run.
import csv
import ctypes
import math
import os
import sys
import time
import tkinter as tk

import numpy as np
import pyautogui
from PIL import Image, ImageFilter, ImageTk

STEP = 2.0 # zoom per scroll notch
SMOOTH = 0.8  # blur (in image pixels) before zooming, to soften blocky pixels; 0 = off, ~1.5 = very soft
stopped = {"esc": False}  # set when Esc is pressed so a CSV run stops too


def load_image(sector_img_file):
    # .tif sector files can be 16-bit or 4-band, which PIL can't show properly, so read them with rasterio
    if sector_img_file.lower().endswith((".tif", ".tiff")):
        import rasterio
        with rasterio.open(sector_img_file) as dataset:
            bands = [1, 2, 3] if dataset.count >= 3 else [1, 1, 1]  # grayscale -> RGB
            arr = np.moveaxis(dataset.read(bands), 0, -1)
        if arr.dtype != np.uint8:  # stretch to 0-255, clipping the darkest/brightest 2%
            arr = arr.astype(np.float32)
            p2, p98 = np.percentile(arr, (2, 98))
            arr = np.clip((arr - p2) / max(p98 - p2, 1e-6), 0, 1) * 255
            arr = arr.astype(np.uint8)
        return Image.fromarray(arr)
    return Image.open(sector_img_file).convert("RGB")


def next_path(sector):
    # first unused number, so earlier screenshots are never overwritten
    os.makedirs(sector, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(sector, f"{sector}_{n:03d}.png")):
        n += 1
    return os.path.join(sector, f"{sector}_{n:03d}.png")


def capture(ul, lr, sector_img_file, img=None):
    (x1, y1), (x2, y2) = ul, lr
    sector = os.path.splitext(os.path.basename(sector_img_file))[0]  # CC_17F.tif -> CC_17F
    if img is None:
        img = load_image(sector_img_file)
    if not (0 <= x1 < x2 <= img.width and 0 <= y1 < y2 <= img.height):
        raise ValueError(f"Box must fit inside the image, which is {img.width} x {img.height}")

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    W, H = root.winfo_screenwidth(), root.winfo_screenheight()
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2           # box center stays at screen center
    fit = min(W / (x2 - x1), H / (y2 - y1))            # zoom where the box fills the screen
    view = {"scale": fit / STEP**3, "saved": None}      # start 3 notches out from that

    def to_screen(ix, iy):
        s = view["scale"]
        return round(W / 2 + (ix - cx) * s), round(H / 2 + (iy - cy) * s)

    def draw():
        s = view["scale"]
        # only the part of the image that's on screen (+2 px so the blur has neighbors)
        left, top = cx - W / (2 * s), cy - H / (2 * s)
        part_box = (math.floor(left) - 2, math.floor(top) - 2,
                    math.ceil(left + W / s) + 2, math.ceil(top + H / s) + 2)
        part = img.crop(part_box)
        if SMOOTH > 0:
            part = part.filter(ImageFilter.GaussianBlur(SMOOTH))
        frame = part.transform((W, H), Image.Transform.AFFINE,
                               (1 / s, 0, left - part_box[0], 0, 1 / s, top - part_box[1]),
                               Image.Resampling.BICUBIC)  # smooth instead of blocky pixels
        view["photo"] = ImageTk.PhotoImage(frame)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=view["photo"])

    def on_scroll(event):  # the viewer zooms in/out when the wheel moves
        view["scale"] *= STEP if event.delta > 0 else 1 / STEP
        draw()

        # Step 1: autoclicker scrolls one notch at a time while the box still fits
    def zoom_step():
        s = view["scale"] * STEP
        if (x2 - x1) * s <= W and (y2 - y1) * s <= H:
            before = view["scale"]
            pyautogui.scroll(120, x=W // 2, y=H // 2)  # 120 = one wheel notch on Windows
            root.update()
            if view["scale"] == before:                 # scroll didn't reach the window
                view["scale"] *= STEP
                draw()
            root.after(100, zoom_step)
        else:
            # zoom the rest of the way so the box touches the screen edges
            view["scale"] = min(W / (x2 - x1), H / (y2 - y1))
            draw()
            root.after(150, shoot)

    # Steps 2 + 3: screenshot the box and save it in the sector folder as a lossless .png
    def shoot():
        left, top = to_screen(x1, y1)
        right, bottom = to_screen(x2, y2)
        pyautogui.moveTo(W - 1, H // 2)  # cursor out of the shot
        root.update()
        time.sleep(0.1)
        shot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))

        path = next_path(sector)
        shot.save(path)
        print("Saved", path)
        view["saved"] = path
        root.destroy()

    def on_escape(event):
        stopped["esc"] = True
        root.destroy()

    def start():
        root.lift()
        root.focus_force()
        canvas.focus_set()
        pyautogui.click(W // 2, H // 2)   # the click you were doing by hand
        zoom_step()

    canvas.bind("<MouseWheel>", on_scroll)
    root.bind("<Escape>", on_escape)
    draw()
    root.after(300, start)
    root.mainloop()
    return view["saved"]


def capture_from_csv(sector_img_file, coords_csv):
    # one screenshot per row of the CSV from sectorCoordinateProcessor.py
    img = load_image(sector_img_file)  # load the big image once, not once per box
    sector = os.path.splitext(os.path.basename(sector_img_file))[0]
    with open(coords_csv, newline="") as f:
        rows = list(csv.DictReader(f))

    os.makedirs(sector, exist_ok=True)
    index_path = os.path.join(sector, f"{sector}_index.csv")
    new_index = not os.path.exists(index_path)
    with open(index_path, "a", newline="") as index_file:
        writer = csv.writer(index_file)
        if new_index:
            writer.writerow(["file", "SectorName", "RoadName", "intervalNum", "ULx", "ULy", "LRx", "LRy"])
        for i, row in enumerate(rows, 1):
            ul = (int(row["ULx"]), int(row["ULy"]))
            lr = (int(row["LRx"]), int(row["LRy"]))
            print(f"[{i}/{len(rows)}] {row['RoadName']} #{row['intervalNum']}")
            path = capture(ul, lr, sector_img_file, img)
            if stopped["esc"]:
                print("Stopped with Esc")
                break
            writer.writerow([os.path.basename(path), row["SectorName"], row["RoadName"],
                             row["intervalNum"], *ul, *lr])
            index_file.flush()
