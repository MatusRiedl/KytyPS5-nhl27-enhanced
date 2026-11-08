"""Draw the Faceoff icon into packaging/faceoff.ico and faceoff.png.

The mark is the rink's center ice, minimal: a black tile, a red center line and a red faceoff circle with its dot.
Drawn at 4x and scaled down so the edges stay smooth; small sizes get thicker lines so they still read at 16 px.
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = [16, 24, 32, 48, 64, 128, 256]
RED = (230, 30, 52, 255)
SS = 4                                   # supersampling


def draw(size):
    S = size * SS
    small = size <= 32
    pad = 0 if small else S * 0.04
    radius = S * 0.22
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([pad, pad, S - pad, S - pad], radius=radius, fill=255)

    # black tile with a soft top-down sheen
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        v = int(26 * (1 - t) + 6 * t)
        d.line([(0, y), (S, y)], fill=(v, v, v + 2, 255))

    c = S / 2
    line = S * (0.07 if small else 0.04)
    ring = S * (0.075 if small else 0.045)
    r = S * (0.30 if small else 0.28)

    # center line, edge to edge through the circle like on the ice
    d.rectangle([c - line / 2, 0, c + line / 2, S], fill=RED)
    # faceoff circle and the center dot
    d.ellipse([c - r, c - r, c + r, c + r], outline=RED, width=int(ring))
    dot = S * (0.075 if small else 0.055)
    d.ellipse([c - dot, c - dot, c + dot, c + dot], fill=RED)

    # thin steel rim so the black tile holds on dark taskbars
    if not small:
        d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=radius, outline=(70, 74, 82, 255), width=int(S * 0.012))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    frames = [draw(s) for s in SIZES]
    big = frames[-1]
    big.save(os.path.join(HERE, "faceoff.ico"), sizes=[(s, s) for s in SIZES], append_images=frames[:-1])
    big.save(os.path.join(HERE, "faceoff.png"))
    print("faceoff.ico written")
