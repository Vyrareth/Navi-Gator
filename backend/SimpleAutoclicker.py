#Simple autoclicker  (Windows)
#pip install pyautogui pillow

#capture((ULx, ULy), (LRx, LRy), "CC_17F.png")
#  1. opens the image full-screen and the autoclicker scrolls to zoom in
#     until one more notch would cut off part of the box
#   BEFORE RUNNING: set Windows display scaling to 100%
#       Settings -> System -> Display -> Scale -> 100%
#       (otherwise the screenshot can grab the wrong area)
#  2. screenshots the box (UL corner -> LR corner)
#  3. saves it in a folder named after the image: CC_17F/CC_17F_001.png
#Press Esc to quit early.

import ctypes
import os
import time
import tkinter as tk

import pyautogui
from PIL import Image, ImageTk

STEP = 2.0 # zoom per scroll notch

def capture(ul, lr, sector_img_file):
    (x1, y1), (x2, y2) = ul, lr
    sector = os.path.splitext(os.path.basename(sector_img_file))[0]  # CC_17F.png -> CC_17F
    img = Image.open(sector_img_file).convert("RGB")
    if not (0 <= x1 < x2 <= img.width and 0 <= y1 < y2 <= img.height):
        raise ValueError(f"Box must fit inside the image, which is {img.width} x {img.height}")

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    W, H = root.winfo_screenwidth(), root.winfo_screenheight()
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2           # box center stays at screen center
    view = {"scale": min(W / img.width, H / img.height)}  # start: whole image fits

    def to_screen(ix, iy):
        s = view["scale"]
        return round(W / 2 + (ix - cx) * s), round(H / 2 + (iy - cy) * s)

    def draw():
        s = view["scale"]
        frame = img.transform((W, H), Image.Transform.AFFINE,
                              (1 / s, 0, cx - W / (2 * s), 0, 1 / s, cy - H / (2 * s)),
                              Image.Resampling.NEAREST)
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
            pyautogui.scroll(120, x=W // 2, y=H // 2)  # 120 = one wheel notch on Windows
            root.after(400, zoom_step)
        else:
            # zoom the rest of the way so the box touches the screen edges
            view["scale"] = min(W / (x2 - x1), H / (y2 - y1))
            draw()
            root.after(400, shoot)

    # Steps 2 + 3: screenshot the box and save it in the sector folder
    def shoot():
        left, top = to_screen(x1, y1)
        right, bottom = to_screen(x2, y2)
        pyautogui.moveTo(W - 1, H // 2)  # cursor out of the shot
        root.update()
        time.sleep(0.2)
        shot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))

        os.makedirs(sector, exist_ok=True)
        n = len([f for f in os.listdir(sector) if f.endswith(".jpg")]) + 1
        path = os.path.join(sector, f"{sector}_{n:03d}.jpeg")
        shot.save(path)
        print("Saved", path)
        root.destroy()

    canvas.bind("<MouseWheel>", on_scroll)
    root.bind("<Escape>", lambda e: root.destroy())
    draw()
    root.after(1000, zoom_step)
    root.mainloop()


if __name__ == "__main__":
    capture((450, 310), (480, 330), "CC_17F.jpeg")



# tiny box capture((450, 310), (480, 330), "CC_17F.jpeg"). 
# A 30 × 20 pixel spot on the nose. It zooms in a lot and comes out very blocky

#Right ear	capture((590, 10), (790, 210), "CC_17F.jpeg")

#Out of bounds: capture((800, 600), (1000, 900), "CC_17F.jpeg"). 
# This should stop with the "Box must fit inside the image" error.

#Right eye	capture((560, 190), (705, 270), "CC_17F.jpeg")
#Nose	capture((385, 285), (560, 370), "CC_17F.jpeg")