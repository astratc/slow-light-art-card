"""Slow Light - a Generative Art Card (600x800 looping GIF).
Every moving term is periodic in the loop length, so the last frame
flows straight into the first. Python + numpy + Pillow only.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, ART = 600, 800, 560          # canvas, square art window size
FPS, SECONDS = 15, 4      # 60 frames; GIF delay 60 ms (centisecond units) = 3.6 s loop
N = FPS * SECONDS                  # 80 frames
TAU = 2 * np.pi
rng = np.random.default_rng(7)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
for p in ["/usr/share/fonts/truetype/sand-box/google/IBM Plex Serif/IBMPlexSerif-Light.ttf",
          "/usr/share/fonts/truetype/sand-box/google/IBM Plex Serif/IBMPlexSerif-Regular.ttf"]:
    try: ImageFont.truetype(p, 10); SERIF = p; break
    except OSError: pass
SERIF_IT = SERIF.replace("Light", "LightItalic").replace("Regular.ttf", "Italic.ttf")

# palette stops: night -> burgundy -> violet -> rose -> warm glow
STOPS = np.array([[0.00, 10, 4, 16], [0.30, 62, 10, 38], [0.52, 104, 32, 92],
                  [0.70, 128, 70, 160], [0.86, 214, 120, 150], [1.00, 255, 214, 190]], float)

def palette(v):
    v = np.clip(v, 0, 1)
    out = np.empty(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, STOPS[:, 0], STOPS[:, c + 1])
    return out

y, x = np.mgrid[0:ART, 0:ART] / ART
cx, cy = x - 0.5, y - 0.5
r = np.sqrt(cx**2 + cy**2)

# random wave field: spatial frequency, direction, phase, integer time harmonic
K = 14
waves = [(rng.uniform(2, 9), rng.uniform(0, TAU), rng.uniform(0, TAU),
          rng.choice([1, 1, 2, -1, -2]), rng.uniform(0.4, 1.0)) for _ in range(K)]

stars_n = 140
sx, sy = rng.integers(0, ART, stars_n), rng.integers(0, ART, stars_n)
sph, sk = rng.uniform(0, TAU, stars_n), rng.choice([1, 2, 3], stars_n)
sb = rng.uniform(0.25, 1.0, stars_n) ** 2

def field(t):
    ph = TAU * t
    # slow domain warp (periodic)
    wx = cx + 0.06 * np.sin(TAU * 2.2 * cy + ph)
    wy = cy + 0.06 * np.cos(TAU * 1.7 * cx - ph)
    f = np.zeros_like(x)
    for k, a, p, h, amp in waves:
        f += amp * np.sin(TAU * k * (wx * np.cos(a) + wy * np.sin(a)) + p + h * ph) / k**0.6
    f = (f - f.min()) / (np.ptp(f) + 1e-9)
    breath = 0.5 + 0.5 * np.sin(ph - np.pi / 2)          # one slow breath per loop
    core = np.exp(-(r / (0.30 + 0.05 * breath)) ** 2)
    v = 0.15 + 0.55 * f**1.6 * (0.45 + 0.75 * core) + 0.28 * core * (0.75 + 0.25 * breath)
    v *= 1 - 0.55 * np.clip(r / 0.72, 0, 1) ** 2         # vignette
    return v

def stars(t):
    s = np.zeros((ART, ART))
    tw = sb * (0.55 + 0.45 * np.sin(TAU * sk * t + sph)) ** 3
    s[sy, sx] = tw
    img = Image.fromarray((np.clip(s, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
    return np.asarray(img, float) / 255 * 3.2 + s * 0.8

# static card: dark plate, thin rule, title + artist
base = Image.new("RGB", (W, H), (12, 6, 14))
d = ImageDraw.Draw(base)
m = (W - ART) // 2
d.rectangle([m - 2, m - 2, m + ART + 1, m + ART + 1], outline=(70, 32, 58))
title_f, art_f, small_f = ImageFont.truetype(SERIF, 38), ImageFont.truetype(SERIF_IT if SERIF_IT != SERIF else SERIF, 20), ImageFont.truetype(SERIF, 13)
plate_top = m + ART + 2
def ctext(yc, s, f, fill):
    w = d.textlength(s, font=f); d.text(((W - w) / 2, yc), s, font=f, fill=fill)
ctext(plate_top + 40, "Slow Light", title_f, (240, 214, 200))
d.line([(W / 2 - 40, plate_top + 98), (W / 2 + 40, plate_top + 98)], fill=(150, 70, 110), width=1)
ctext(plate_top + 112, "Astra Trading Co.", art_f, (196, 150, 176))
ctext(plate_top + 150, "generative loop  \u00b7  2026", small_f, (120, 86, 110))

frames = []
for i in range(N):
    t = i / N
    rgb = palette(field(t)) + stars(t)[..., None] * np.array([255, 236, 240])
    art = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    card = base.copy(); card.paste(art, (m, m)); frames.append(card)

# one shared palette for every frame -> no colour flicker, small file
strip = Image.new("RGB", (W, H * 4))
for j, k in enumerate(range(0, N, N // 4)): strip.paste(frames[k], (0, H * j))
pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save("slow_light.gif", save_all=True, append_images=q[1:], duration=60, loop=0, optimize=False, disposal=1)
print("frames", N)
