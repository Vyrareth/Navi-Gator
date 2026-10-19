# Road Rating Blueprint — Walkthrough for the Professor

*First-person talking script. Read it over, say it in your own words.*

---

So last week, Professor, I came up with a rough draft of this. I was still researching
how the CNN should evaluate a road — so think of it less as the finished model and more
as a **blueprint**: the rating system the CNN will be trained to copy.

Like I mentioned last week, there are a bunch of things I ran into with image quality —
stuff like rutting depth, ride roughness, and cracks below a certain size that are too
small to see from overhead. I can't measure those from NJGIN imagery. But even with those
limits, I still managed to build an **anchor system** for rating roads.

## The 1–5 scale

If you look at Section 2, I set up a scaling system where I rank each road out of 5 —
5 being the best, 1 being the worst — and I defined what each level looks like:

- **5 — Excellent:** uniform dark asphalt, no cracks, crisp lane markings → route freely
- **4 — Good:** slightly grey, a few isolated cracks or one patch → no penalty
- **3 — Fair:** aged grey, scattered cracks or several patches → small routing penalty
- **2 — Poor:** connected/alligator cracking, potholes, ragged edges → avoid if there's an alternative
- **1 — Do-Not-Travel:** surface shattered, many potholes, crumbling edges → exclude from routing (or travel at your own risk)

## Testing with synthetic chips

To test the program first, I made three **synthetic chips** and labeled them on purpose:
the **L5** chip is a smooth, uniform surface with no blotches or potholes; the **L3** is
fair, with some minor discoloration and a few blotches; and the **L1** is the worst of the
three. These let me check the program runs and behaves before I touched real data.

## The method — the food-critic game

Here's how the program actually grades a road. Think of a **food critic** walking into a
restaurant. You order a dish — salmon, herb butter, and greens. As the critic, I start you
at **5 out of 5**, and I deduct points as I go. As long as the main components are on the
plate (the salmon, the greens, the butter), I don't deduct for them just being there. But
there are things to watch for — how well-cooked the salmon is, whether the greens are
overcooked, whether the butter is flavorful — each of those can lose you points.

Roads work the same way. Every road **starts at 5/5**. Then any defect — potholes,
blotches, scratches, anything other than smooth black asphalt — costs it points. Whatever
it ends up with out of 5 is the road's level.

## Calibrating on real NJGIN roads

Besides the synthetic chips, I went ahead and pulled **actual NJGIN road chips** to mess
around with. I picked **2 good roads and 2 bad ones**, rated them myself by eye, and then
ran them through the program to see how close it got to my own ratings.

The main problem I ran into: the program kept flagging **houses, trees, cars, and shadows**
as road defects. For now — since we're just messing around before Don's program is ready —
I bypassed it by **cropping out everything except the road itself** (Section 3 / point 10).
That matters, and I'll come back to it at the end.

### How the output matched my ratings (example: D14B15)

Take the **D14B15** chip. The program's output matched my manual rating, and here's how it
works. There are three numbers, and they're on different scales:

- **texture** = the raw roughness reading (just a sensor number, not out of 5)
- **distress** = how damaged that works out to, from 0 (perfect) to 1 (wrecked)
- **LEVEL** = the final 1–5 grade, after deducting from 5

I calibrated the program so **texture 3.65 = clean** and **texture 4.40 = wrecked**.

1. The program measures the road: **texture = 3.66**.
2. It converts that to distress:
   `distress = (3.66 − 3.65) / (4.40 − 3.65) = 0.01 / 0.75 ≈ 0.01`
   (basically no damage — it's right at the clean end).
3. It deducts from 5:
   `LEVEL = 5 − 4 × distress = 5 − 4(0.01) = 4.96 → rounds to 5`

So the program output **Level 5**, which matched my rating exactly. The same held for all
four chips I pulled — the program's scores lined up with my manual ratings.

## How my piece fits the team's pipeline

To tie this all together into the actual system — right now I'm cropping the roads out by
hand, but in the real pipeline my part sits in the **middle of three pieces**:

1. **Cris's auto-clicker** automatically pulls the road snapshots from NJGIN by coordinate —
   so instead of me manually downloading tiles, it feeds the images in at scale.
2. **Don's Stage 1–2 program** isolates just the road pixels — it strips out the houses,
   cars, trees, and shadows. That directly solves the biggest problem I ran into, where the
   program mistook those things for road defects. I was doing that cleanup by hand with
   cropping; Don's program automates it.
3. **My rating system** takes those clean, road-only chips and scores each one 1–5 using the
   food-critic method.

And finally, those 1–5 scores become the **labeled training data for the CNN**. The model
learns to reproduce my ratings automatically, and once it's trained, its score becomes the
**weight in our routing graph**: a Level-5 road is free to use, a Level-1 road gets avoided.

**So the flow is:**
Cris feeds the images → Don cleans them to road-only → I grade them → that grading trains
the CNN → the CNN's score steers the routing.

My deliverable this week is that **grading system — the blueprint — proven against real
NJGIN roads.**

---

### If he asks "what's next for your part specifically?"

> Next I want to calibrate on more roads so the thresholds are solid, hand that labeling
> rule to whoever builds the CNN so they can auto-label a training set, and look into
> street-level imagery (Mapillary) for the fine detail that overhead imagery can't show.
