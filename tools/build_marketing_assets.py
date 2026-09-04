"""
Cuts the Marketing page's artwork out of the two Canva exports.

    python tools/build_marketing_assets.py

Sources (both in "Pages for Portfolio/"):
  mkt-assets-hq2.png  1920x1080, transparent - mountains, Nepal flag, map pin,
                      and the layout positions used by build_marketing_css.py
  plsbehq.png         1920x3080 - the eight polaroids at ~2.6x the size they
                      appear at, so they stay sharp on high-density screens

Two details worth knowing:
  * Canva bakes a 1-2px white bevel onto the top and right edge of every
    polaroid. It reads as a stray light line against pale photos, so the
    shape is eroded a couple of pixels before the cut-out.
  * The pin is recoloured from its original red to the mountains' slate. Each
    pixel is a blend of the pin's red and its white dot, so the blend factor
    is recovered and rebuilt with slate, which keeps the dot and the
    anti-aliased edge clean.
"""
from PIL import Image
from collections import deque
import numpy as np
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Pages for Portfolio")
OUT = os.path.join(ROOT, "assets")
PAGE_BG = np.array([22, 12, 15], dtype=float)
CREAM = np.array([245, 235, 206], dtype=float)
SLATE = np.array([0x67, 0x7b, 0x82], dtype=float)   # #677b82, the mountain colour
EDGE_TRIM = 2                                       # px of Canva's bevel to drop


def dilate(m, n=1):
    for _ in range(n):
        o = m.copy()
        o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        m = o
    return m


def erode(m, n=1):
    return ~dilate(~m, n)


def fill_holes(m):
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


def blob(mask, x0, y0, x1, y1):
    """The one shape connected to the centre of the box."""
    sub = mask[y0:y1, x0:x1]
    h, w = sub.shape
    seen = np.zeros_like(sub)
    q = deque([(h // 2, w // 2)])
    seen[h // 2, w // 2] = True
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and sub[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return fill_holes(seen)


# ------------------------------------------------- 1. the eight polaroids
hq = np.asarray(Image.open(os.path.join(SRC, "plsbehq.png")).convert("RGB")).astype(float)
dist = np.abs(hq - PAGE_BG).sum(axis=2)
solid = dist > 40
# boxes in the source, ordered to match photo-1..8 on the page
POLAROIDS = [(275, 244, 770, 820), (1415, 278, 1911, 854), (867, 469, 1362, 1045),
             (9, 948, 770, 1603), (1415, 976, 1911, 1552), (867, 1275, 1362, 1851),
             (318, 1731, 814, 2307), (1415, 1731, 1911, 2307)]
print("--- polaroids (from plsbehq.png) ---")
for i, (x0, y0, x1, y1) in enumerate(POLAROIDS, 1):
    m = erode(blob(solid, x0, y0, x1, y1), EDGE_TRIM)   # drop Canva's white bevel
    core = erode(m)
    ring = m & ~core
    alpha = core.astype(float)
    alpha[ring] = np.clip(dist[y0:y1, x0:x1][ring] / 30.0, 0, 1)
    rgb = np.clip(PAGE_BG + (hq[y0:y1, x0:x1] - PAGE_BG) / np.maximum(alpha, 1e-6)[:, :, None], 0, 255)
    Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA") \
        .save(os.path.join(OUT, f"mkt-photo-{i}.png"))
    print(f"  mkt-photo-{i}.png  {x1 - x0}x{y1 - y0}")

# --------------------------------- 2. mountains, flag and pin (from hq2)
art = np.asarray(Image.open(os.path.join(SRC, "mkt-assets-hq2.png")).convert("RGBA"))
al, rgb = art[:, :, 3], art[:, :, :3].astype(int)
opaque = al > 40
r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

# the polaroids sit over the mountains in this export, so mask them out first
LAYOUT_POLAS = [(940, 227, 1131, 449), (1384, 240, 1575, 462), (1171, 314, 1361, 537),
                (837, 501, 1131, 753), (1384, 512, 1575, 734), (1170, 627, 1361, 850),
                (957, 806, 1148, 1028), (1384, 806, 1575, 1028)]
covered = np.zeros_like(opaque)
for x0, y0, x1, y1 in LAYOUT_POLAS:
    covered[y0:y1, x0:x1] |= blob(opaque, x0, y0, x1, y1)

slate_ink = opaque & (np.abs(r - 103) < 48) & (np.abs(g - 123) < 48) & (np.abs(b - 130) < 48)
band = np.zeros_like(slate_ink)
band[0:335] = True
mountains = slate_ink & band & ~covered
print("\n--- mountains + flag (from mkt-assets-hq2.png) ---")
def drop_hanging_strokes(mask, max_width=4, drop=110, look=6):
    """Remove the thin vertical strokes Canva leaves dangling below the ridge.

    One hangs off the right-hand range and, now that the photo grid sits lower,
    it shows as a stray line in the gap above a polaroid. A stroke qualifies if
    it is only a few pixels wide and reaches far below where the silhouette
    otherwise ends -- 110px past the median, which clears the real ridge
    detail that dips 40-90px below. Only the part hanging under the ridge is
    cut, so the line it grows out of stays intact.
    """
    m = mask.copy()
    H, W = m.shape
    inked = m.any(axis=0)
    if not inked.any():
        return m
    lowest = H - 1 - np.argmax(m[::-1], axis=0)
    cutoff = int(np.median(lowest[inked])) + drop
    cols = [x for x in range(W) if inked[x] and lowest[x] > cutoff]
    runs, i = [], 0
    while i < len(cols):
        j = i
        while j + 1 < len(cols) and cols[j + 1] == cols[j] + 1:
            j += 1
        runs.append((cols[i], cols[j]))
        i = j + 1
    for x0, x1 in runs:
        if x1 - x0 + 1 > max_width:
            continue                       # wide enough to be real ridge detail
        near = np.zeros(H, dtype=bool)     # ink either side of the stroke?
        for x in range(max(0, x0 - look), min(W, x1 + look + 1)):
            if x0 <= x <= x1:
                continue
            near |= m[:, x]
        cut = H
        for y in range(H - 1, -1, -1):     # walk up until it rejoins the ridge
            if near[y]:
                cut = y + 1
                break
        m[cut:, x0:x1 + 1] = False
    return m


for name, (bx0, bx1) in {"mkt-mountain-left": (0, 700), "mkt-mountain-right": (1200, 1920)}.items():
    m = np.zeros_like(mountains)
    m[:, bx0:bx1] = mountains[:, bx0:bx1]
    before = int(m.sum())
    m = drop_hanging_strokes(m)
    if m.sum() != before:
        print(f"    (trimmed {before - int(m.sum())} px of dangling stroke)")
    ys, xs = np.nonzero(m)
    cx0, cy0, cx1, cy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out = art[cy0:cy1, cx0:cx1].copy()
    out[:, :, 3] = np.where(m[cy0:cy1, cx0:cx1], al[cy0:cy1, cx0:cx1], 0)
    Image.fromarray(out, "RGBA").save(os.path.join(OUT, f"{name}.png"))
    print(f"  {name}.png  x{cx0} y{cy0}  {cx1 - cx0}x{cy1 - cy0}")

FLAG = (1321, 67, 1382, 148)
Image.fromarray(art[FLAG[1]:FLAG[3], FLAG[0]:FLAG[2]], "RGBA").save(os.path.join(OUT, "mkt-flag.png"))
print(f"  mkt-flag.png  x{FLAG[0]} y{FLAG[1]}  {FLAG[2]-FLAG[0]}x{FLAG[3]-FLAG[1]}")

# The pin is drawn rather than cut out of the export: the bitmap version came
# out with ragged edges, and an SVG stays perfectly round at any size.
pin_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 32" width="24" height="32">
  <path d="M12 0.6C5.9 0.6 1 5.5 1 11.6c0 7.4 9.2 18 10.3 19.2a1 1 0 0 0 1.4 0
           C13.8 29.6 23 19 23 11.6 23 5.5 18.1 0.6 12 0.6Z" fill="#677b82"/>
  <circle cx="12" cy="11.6" r="4.3" fill="#ffffff"/>
</svg>
"""
with open(os.path.join(OUT, "mkt-pin.svg"), "w", encoding="utf-8") as fh:
    fh.write(pin_svg)
old_png = os.path.join(OUT, "mkt-pin.png")
if os.path.exists(old_png):
    os.remove(old_png)          # superseded by the vector
print("  mkt-pin.svg   drawn (slate #677b82); the old bitmap pin was removed")
print()
print("Now run: python tools/build_marketing_css.py")
