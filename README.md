# Nirvaan Nair — Portfolio Site



## Files


| `index.Rmd` | Landing page
| `social-media.Rmd` | "Social Media & Content Creation" page
| `marketing.Rmd` | "Marketing Campaign Development" page
| `css/style.css` | All styling + button positions
| `js/wicd.js` | WHAT I CAN DO window, About Me slide-over, Social Media exit animation |
| `js/social.js` | Swaps a video poster for the real player when clicked |
| `css/social-layout.css` | Social page positions
| `css/social.css` | Social page components: poster grid, play button, lightbox |
| `assets/` | Web-ready images: backgrounds, the name overlays, and every button in normal and `-hover` state |
| `tools/build_assets.py` | Script that r0egenerates everything in `assets/`
| `tools/build_social_css.py` | Lays out the Social page rows and writes `css/social-layout.css` |
| `tools/build_marketing_assets.py` | Cuts the Marketing artwork out of the Canva exports
| `tools/build_marketing_css.py` | Marketing page positions + entrance timing → `css/marketing-layout.css` |
| `notes/ANIMATIONS.md` | AI Notes on making more animations |
| `Pages for Portfolio/` | Original Canva exports 
| `_site.yml` | Site config (output folder, shared page options) |





AI-Gen Notes:



- **Videos.** The four brand clips are local files (`assets/1.mp4` … `4.mp4`,
  in filename order). The three personal ones are TikTok/YouTube embeds.
- **The grid is posters, not players.** Platform embeds letterbox and add their
  own chrome, which is what threw the thumbnails and play buttons off-centre.
  Each frame is now a poster image with `object-fit: cover`, so it fills its
  white border exactly. Posters for the brand clips are pulled straight out of
  the videos by `ffmpeg`, so they always match.
- **Playback is split.** The four local brand clips play **in place**, inside
  their own white border. The three TikTok/YouTube embeds open in a **lightbox**
  at ~86% of the window height, because four videos across a 1920 canvas caps
  each frame at ~250px and a TikTok card clips below ~325px. Which behaviour a
  frame gets is the `data-kind` on its button: `inline` or `embed`.
- **The top-left star cluster fades out during the transition.** It sits exactly
  where the Social Media title goes, so `tools/build_assets.py` splits it into
  its own layer (`layer-star-title.png`) that fades with everything else on the
  way out. The other two stars stay put and are what the social page draws as
  its background — which is why the hand-off still lines up.
- **Layout knobs.** Everything about the rows — the content band, the gaps, the
  vertical rhythm — lives at the top of `tools/build_social_css.py`. Change a
  number, re-run it, rebuild. The box scale is derived, not hard-coded: the
  personal row is the crowded one, so it decides how large every box can be.
  `--soc-scale` in the generated CSS then shrinks the whole page (stars
  excluded) — raise it for bigger videos, lower it to fit more on screen.

**Marketing page.** Built on the 1920x1080 canvas from `mkt-assets-hq2.png`,
with the eight polaroids cut from `plsbehq.png` (they are ~2.6x the size they
display at, so they stay sharp). The two cream boxes are drawn in CSS and sized
by their content, so both hug their text with matching padding. The photo grid
is laid out by the generator rather than hard-coded: it mirrors the copy's
margin (text starts 107px from the left, photos finish 107px from the right)
and the scale is pushed as high as the vertical band allows.

Two things the Canva exports need cleaning up, both handled in
`tools/build_marketing_assets.py`:

- every polaroid carries a 1-2px white bevel on its top and right edge, which
  reads as a stray light line against pale photos - the shape is eroded before
  the cut-out
- the map pin is **drawn as SVG** (`assets/mkt-pin.svg`) rather than cut from
  the export: the bitmap version had ragged edges, and the original red pin was
  also baked into photo 4, so it flashed red before the recoloured one appeared.
  It is now slate `#677b82`, anchored by its tip to the Machapuchare summit as a
  fraction of photo 4, so it follows the photo wherever the grid puts it.

Its entrance runs on load with no JavaScript - three beats, all timed in
`tools/build_marketing_css.py`:

| Beat | What | When |
|---|---|---|
| 1 | mountains + title fade up alone | 0 -> 1.2s |
| 2 | boxes, photos and flag fade in together | 1.0 -> 1.9s |
| 3 | the pin springs up from its own tip | 2.05 -> 2.75s |

The pin uses `animation-fill-mode: backwards` (not `both`) so that once it
settles the element returns to its normal styles and the hover effect works.

**The name.** It is *not* part of the background image. The version Canva baked
into the export was erased (the night sky was filled back in), and the hi-res
ascii artwork is layered on top as `title-line1.png` / `title-line2.png`, scaled
so the solid letters land exactly on the original footprint while the digit
trail spills out naturally. They ship at 2x resolution so they stay crisp.


## Video sizes

The brand clips are already compressed: 720p portrait / 720p landscape, H.264
CRF 26, AAC 96k, with `+faststart` so they begin playing before fully
downloading. That took them from **145 MB to 24 MB** with no visible difference
at the size they display.

Re-compressing a replaced clip is the same command; the poster is re-cut from
the new file so the grid always matches what plays.

**Originals are at `../video-originals/`** (next to this repo,
deliberately outside it so they never get committed). If you re-export from
Canva, re-compress with:

```bash
ffmpeg -i input.mp4 -vf scale=720:-2 -c:v libx264 -crf 26 -preset medium   -c:a aac -b:a 96k -movflags +faststart assets/1.mp4
```

Use `scale=1280:-2` for landscape clips. Whole repo is now ~54 MB including
the `docs/` copy.

## Still to fill in

- **About Me portrait** — commented `<img>` slot ready in `index.Rmd`
- **`assets/social-poster-p1.jpg`** — TikTok only serves a 133x210 cover for
  that video, so it looks soft. Drop a full-size screenshot in over it (any
  9:16 image) and it will sharpen up; nothing else needs changing.
- **Agrandir font** — buttons using it are images, so nothing needed now; for
  future HTML text in that style, add font files to `assets/fonts/` and
  uncomment the `@font-face` block in `css/style.css`
- **Name brightness** — if the ascii digits should glow more or less, change
  `ALPHA_GAMMA` / `WHITE_LIFT` near the bottom of `tools/build_assets.py`
  (lower gamma = brighter faint digits) and re-run it
- The inner pages don't have a back/home button in the design yet — add one in
  Canva (or ask for an HTML one) when ready
