"""
Rebuilds everything in assets/ from the original Canva exports in
"Pages for Portfolio/". Run it only if you re-export a design from Canva:

    python tools/build_assets.py

What it does
------------
1. Cuts every button out of the flattened exports as a transparent PNG, in both
   its normal and hover state, using an exact alpha mask (no background fringe).
2. Erases the name that Canva baked into the landing background, filling the
   night sky back in, so the separate hi-res ascii title can sit on top.
3. Fades the photo's left/right edges into the page background colour.
4. Builds the two title overlays from the hi-res ascii artwork.

It prints the CSS percentages for every piece. If a number here changes, copy
the printed value into the matching rule in css/style.css.
"""
from PIL import Image
import numpy as np
import os
import shutil

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Pages for Portfolio")
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

CANVAS_W, CANVAS_H = 1920.0, 1080.0
PAGE_BG = np.array([22, 12, 15], dtype=np.float64)  # #160c0f
rng = np.random.default_rng(11)


def load(name):
    return np.asarray(Image.open(os.path.join(SRC, name)).convert("RGB"), dtype=np.float64)


def dilate(m, n=1):
    for _ in range(n):
        o = m.copy()
        o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        m = o
    return m


def erode(m):
    return ~dilate(~m)


def fill_holes(m):
    """Mark enclosed background (e.g. inside a letter O) as part of the shape."""
    inv = ~m
    outside = np.zeros_like(m)
    outside[0, :] = inv[0, :]; outside[-1, :] = inv[-1, :]
    outside[:, 0] |= inv[:, 0]; outside[:, -1] |= inv[:, -1]
    while True:
        grown = dilate(outside) & inv
        if (grown == outside).all():
            break
        outside = grown
    return m | (inv & ~outside)


def blur3(a):
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    return (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 4.0 * p[1:-1, 1:-1]) / 8.0


def pct(x, y, w, h):
    return (f"left: {x / CANVAS_W * 100:.4f}%; top: {y / CANVAS_H * 100:.4f}%; "
            f"width: {w / CANVAS_W * 100:.4f}%; height: {h / CANVAS_H * 100:.4f}%;")


# ---------------------------------------------------------------- 1. buttons
bg = load("bg.png")
btns = load("bg with buttons.png")
hover = load("each button on hover.png")
clicked = load("what I can do (when clicked).png")
clicked_hover = load("what I can do (when clicked) each button hover.png")


def mask_vs(img, ref, win, thresh=30):
    """Alpha mask of whatever `img` adds on top of `ref`, inside `win`."""
    x0, y0, x1, y1 = win
    m = np.zeros(img.shape[:2], dtype=bool)
    d = np.abs(img[y0:y1, x0:x1] - ref[y0:y1, x0:x1]).sum(axis=2)
    m[y0:y1, x0:x1] = dilate(fill_holes(d > thresh))
    return m


def save_rgba(img, alpha, rect, name):
    x0, y0, x1, y1 = rect
    a = alpha[y0:y1, x0:x1]
    a8 = (a * 255).astype(np.uint8) if a.dtype != bool else (a * 255).astype(np.uint8)
    rgba = np.dstack([img[y0:y1, x0:x1].astype(np.uint8), a8])
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, name))


print("--- main page buttons (stage %) ---")
# search windows, comfortably larger than each button
WINDOWS = {
    "email":    (350, 170, 740, 280),
    "linkedin": (1210, 170, 1340, 290),
    "about":    (460, 415, 690, 495),
    "resume":   (1240, 415, 1450, 495),
    "wicd":     (590, 565, 1290, 670),
}
for name, win in WINDOWS.items():
    mn, mh = mask_vs(btns, bg, win), mask_vs(hover, bg, win)
    ys, xs = np.nonzero(mn | mh)
    rect = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    save_rgba(btns, mn.astype(np.float64), rect, f"btn-{name}.png")
    save_rgba(hover, mh.astype(np.float64), rect, f"btn-{name}-hover.png")
    print(f"#btn-{name} {{ {pct(rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1])} }}")

mw = mask_vs(clicked, bg, (690, 570, 1230, 1080))
ys, xs = np.nonzero(mw)
WIN_RECT = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
save_rgba(clicked, mw.astype(np.float64), WIN_RECT, "wicd-window.png")
print(f"#wicd-window {{ {pct(WIN_RECT[0], WIN_RECT[1], WIN_RECT[2]-WIN_RECT[0], WIN_RECT[3]-WIN_RECT[1])} }}")
# the X in the window's title bar, reused as the About Me close button
Image.open(os.path.join(OUT, "wicd-window.png")).crop((451, 13, 479, 42))     .save(os.path.join(OUT, "btn-close.png"))

# --- menu buttons: soft-edged, measured against the window's flat grey body ---
print("\n--- WICD menu buttons (window %) ---")
grey = clicked[900, 750].copy()
flat = np.empty_like(clicked); flat[:, :] = grey
MENU_WINDOWS = {
    "social":    (770, 640, 1150, 780),
    "marketing": (770, 785, 1150, 925),
    "data":      (770, 930, 1150, 1055),  # stops above the window's bottom bevel
}


def soft_button(img, win):
    """Opaque core + anti-aliased ring, with the ring's colour de-contaminated."""
    x0, y0, x1, y1 = win
    sub = img[y0:y1, x0:x1]
    d = np.abs(sub - grey).sum(axis=2)
    core = erode(fill_holes(d > 40))
    ring = dilate(core, 2) & ~core & (d > 10)
    ys, xs = np.nonzero(core)
    top_band = core & (np.arange(sub.shape[0])[:, None] < ys.min() + 8)
    fill = sub[top_band].mean(axis=0)          # flat colour along the button's top
    f = fill - grey
    ratio = np.clip(((sub - grey) @ f) / (f @ f), 0.0, 1.0)
    alpha = core.astype(np.float64)
    alpha[ring] = ratio[ring]
    rgb = sub.copy()
    rgb[(alpha > 0.03) & ~core] = fill
    return alpha, rgb


wx0, wy0 = WIN_RECT[0], WIN_RECT[1]
ww, wh = WIN_RECT[2] - wx0, WIN_RECT[3] - wy0
for name, win in MENU_WINDOWS.items():
    a_n, rgb_n = soft_button(clicked, win)
    a_h, rgb_h = soft_button(clicked_hover, win)
    vis = (a_n > 0.03) | (a_h > 0.03)
    ys, xs = np.nonzero(vis)
    rx0, ry0, rx1, ry1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    for tag, a, rgb in (("", a_n, rgb_n), ("-hover", a_h, rgb_h)):
        out = np.dstack([rgb[ry0:ry1, rx0:rx1],
                         np.round(np.where(a > 0.03, a, 0)[ry0:ry1, rx0:rx1] * 255)]).astype(np.uint8)
        Image.fromarray(out, "RGBA").save(os.path.join(OUT, f"btn-menu-{name}{tag}.png"))
    ax, ay = win[0] + rx0, win[1] + ry0
    print(f"#menu-{name} {{ left: {(ax-wx0)/ww*100:.4f}%; top: {(ay-wy0)/wh*100:.4f}%; "
          f"width: {(rx1-rx0)/ww*100:.4f}%; height: {(ry1-ry0)/wh*100:.4f}%; }}")

# ------------------------------------------------- 2/3. landing background
# Canva baked the name into bg.png. These are the measured glyph bands; the
# threshold sits above both the page background (max 22) and the night sky
# (max ~19) so only letters are selected, and the bands stop short of the
# car's top edge at row 243.
img = load("bg.png")
h, w = img.shape[:2]
GLYPH_BANDS = [(18, 120, 655, 1270), (148, 242, 655, 1270)]
for by0, by1, bx0, bx1 in GLYPH_BANDS:
    zone = img[by0:by1, bx0:bx1].copy()
    mask = dilate(zone.max(axis=2) > 40, 7)
    known = ~mask
    grain = (zone - blur3(zone))[known].std(axis=0)
    cur = zone.copy()
    cur[mask] = np.median(zone[known], axis=0)
    m3 = mask[:, :, None]
    for _ in range(2500):          # diffusion inpaint -> smooth, seamless fill
        cur = np.where(m3, blur3(cur), zone)
    cur = cur + rng.normal(0.0, grain, size=cur.shape)   # match the photo's grain
    img[by0:by1, bx0:bx1] = np.where(m3, np.clip(cur, 0, 255), zone)

# fade the photo's vertical edges into the page background
PHOTO_LEFT, PHOTO_RIGHT, PHOTO_TOP, FEATHER = 574, 1347, 25, 80.0
xx = np.arange(w)[None, :].astype(np.float64)
yy = np.arange(h)[:, None].astype(np.float64)
t = np.clip(np.minimum((xx - PHOTO_LEFT) / FEATHER, (PHOTO_RIGHT - 1 - xx) / FEATHER), 0.0, 1.0)
t = t * t * (3 - 2 * t)                                   # smoothstep
t = np.where((xx >= PHOTO_LEFT) & (xx < PHOTO_RIGHT) & (yy >= PHOTO_TOP), t, 1.0)
img = PAGE_BG + (img - PAGE_BG) * t[:, :, None]

# --- lift the stars and the planet out into their own layers -------------
# Clicking "Social Media" fades the whole landing artwork away while the
# stars stay put and the planet slides off-screen, so neither can stay baked
# into bg-home.png. Both sit on flat page colour (everything left of the
# photo is untouched #160c0f), which makes the cut-out and the erase exact.
# The stars double as the social page's background and sit at identical
# coordinates there -- that is what makes the hand-off seamless.
# The top-left cluster sits where the Social Media page puts its title, so it
# gets its own layer and fades out during the transition; the other two stay
# put and are what the social page draws as its background.
STAR_TITLE_BOX = (246, 66, 322, 142)
STAR_BOXES = [(1485, 154, 1561, 231), (108, 507, 184, 584)]
PLANET_BOX = (0, 110, 268, 348)


def cut_out(source, boxes):
    """Alpha cut-out of artwork sitting on flat page colour.

    Alpha ramps with distance from the background and the colour is un-mixed
    (BG + diff/alpha), so compositing back onto #160c0f is pixel-identical.
    """
    a = np.zeros(source.shape[:2], dtype=np.float64)
    for x0, y0, x1, y1 in boxes:
        d = np.abs(source[y0:y1, x0:x1] - PAGE_BG).max(axis=2)
        a[y0:y1, x0:x1] = np.clip(d / 30.0, 0.0, 1.0)
    safe = np.maximum(a, 1e-6)[:, :, None]
    rgb = np.clip(PAGE_BG + (source - PAGE_BG) / safe, 0, 255)
    return np.dstack([rgb, a * 255.0]).astype(np.uint8), a


stars_rgba, stars_a = cut_out(img, STAR_BOXES)
Image.fromarray(stars_rgba, "RGBA").save(os.path.join(OUT, "layer-stars.png"))
tstar_rgba, tstar_a = cut_out(img, [STAR_TITLE_BOX])
_sx0, _sy0, _sx1, _sy1 = STAR_TITLE_BOX
Image.fromarray(tstar_rgba[_sy0:_sy1, _sx0:_sx1]).save(os.path.join(OUT, "layer-star-title.png"))
planet_rgba, planet_a = cut_out(img, [PLANET_BOX])
_px0, _py0, _px1, _py1 = PLANET_BOX
Image.fromarray(planet_rgba[_py0:_py1, _px0:_px1], "RGBA").save(os.path.join(OUT, "layer-planet.png"))

img[(stars_a > 0) | (tstar_a > 0) | (planet_a > 0)] = PAGE_BG   # flat fill = exact

Image.fromarray(np.round(img).astype(np.uint8), "RGB").save(os.path.join(OUT, "bg-home.png"))
shutil.copy(os.path.join(SRC, "Social Media & Content Creation.png"), os.path.join(OUT, "bg-page.png"))
print("bg-home.png (stars + planet lifted out) + bg-page.png written")
print(f"#layer-planet {{ {pct(_px0, _py0, _px1 - _px0, _py1 - _py0)} }}")
print(f".layer-star-title {{ {pct(_sx0, _sy0, _sx1 - _sx0, _sy1 - _sy0)} }}")

# ------------------------------------------- 3b. social page artwork
# "stats (1).png" is the mockup's 1920x3080 canvas carrying only the
# non-text art on transparency, so these boxes are straight lifts.
_sheet_path = os.path.join(SRC, "stats (1).png")
if os.path.exists(_sheet_path):
    _sheet = Image.open(_sheet_path).convert("RGBA")
    SOCIAL_ART = {
        "social-tiktok.png":      (842, 1322, 983, 1463),
        "social-youtube.png":     (1707, 1355, 1831, 1443),
        "social-phone.png":       (1342, 1978, 1709, 2703),
        "social-highlighter.png": (588, 2188, 1195, 2244),
    }
    print()
    print("--- social page artwork (canvas 1920x3080) ---")
    for _n, _b in SOCIAL_ART.items():
        _sheet.crop(_b).save(os.path.join(OUT, _n))
        print(f"{_n}: x{_b[0]} y{_b[1]}  {_b[2]-_b[0]}x{_b[3]-_b[1]}")

# ------------------------------------------------------- 4. title overlays
art = Image.open(os.path.join(SRC, "nirvaan_nair_ascii_8800px_transparent_tight.png")).convert("RGBA")
A = np.asarray(art).copy()
A[:, 6795:, 3] = 0        # the generator left a dashed guide line at the right edge
art = Image.fromarray(A, "RGBA")
alpha = A[:, :, 3]

LINE_SPLIT = 1520         # blank rows between the two lines in the artwork
ALPHA_GAMMA = 0.45        # <1 lifts the faint digits so the dissolve reads small
WHITE_LIFT = 0.70         # pushes mid-greys toward white
# name, artwork row range, and where the SOLID letters sit on the 1920x1080
# canvas (left, cap-top, cap-height) - measured from bg.png
LINES = [("title-line1.png", 0, LINE_SPLIT, 685, 24, 88),
         ("title-line2.png", LINE_SPLIT, alpha.shape[0], 799, 154, 83)]

placed = []
for name, ya, yb, ox, oy, cap in LINES:
    sub = alpha[ya:yb]
    solid = sub > 128
    rowmass, colmass = solid.sum(axis=1), solid.sum(axis=0)
    rows = np.nonzero(rowmass > rowmass.max() * 0.10)[0]
    cols = np.nonzero(colmass > colmass.max() * 0.10)[0]
    core_top, core_left, core_h = rows[0], cols[0], rows[-1] - rows[0] + 1
    ys, xs = np.nonzero(sub > 8)                     # includes the digit trail
    fx0, fy0 = int(xs.min()), int(ys.min())
    fx1, fy1 = int(xs.max()) + 1, int(ys.max()) + 1
    s = cap / core_h                                 # scale by cap height, so the
    placed.append([name, (fx0, ya + fy0, fx1, ya + fy1),   # solid letters land exactly
                   ox - (core_left - fx0) * s,             # on the original footprint
                   oy - (core_top - fy0) * s,
                   (fx1 - fx0) * s, (fy1 - fy0) * s])

# nudge the block down so the trail never pokes above the canvas and gets clipped
nudge = max(0.0, -min(p[3] for p in placed)) + 1.0
for p in placed:
    p[3] += nudge

print("\n--- title overlays (stage %) ---")
for name, box, x, y, bw, bh in placed:
    im2 = art.crop(box).resize((max(1, round(bw * 2)), max(1, round(bh * 2))), Image.LANCZOS)
    q = np.asarray(im2).astype(np.float64)
    a = (q[:, :, 3] / 255.0) ** ALPHA_GAMMA
    rgb = 255.0 - (255.0 - q[:, :, :3]) * WHITE_LIFT
    Image.fromarray(np.dstack([np.round(rgb), np.round(a * 255)]).astype(np.uint8), "RGBA") \
        .save(os.path.join(OUT, name))
    print(f"{name}: {pct(x, y, bw, bh)}")

print("\nDone. Assets written to assets/.")
