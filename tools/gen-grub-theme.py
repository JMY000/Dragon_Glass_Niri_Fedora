#!/usr/bin/env python3
"""Build the Dragon GRUB theme into grub/theme/dragon/.
Original artwork, generated procedurally. Needs: pillow numpy, plus `grub-mkfont` and
the Inter font (OFL) to produce the .pf2 fonts. The generated files are shipped in the bundle,
so you only need to run this to change the design.

GRUB cannot blur live, so the frosted panel is baked into the background image. The theme uses
desktop-image-scale-method "stretch" so the panel always lines up with the percent-positioned menu."""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "grub", "theme", "dragon")
WALL = os.path.join(ROOT, "wallpapers", "dragon-dark.jpg")
INTER = os.environ.get("INTER_FONT", "/usr/share/fonts/opentype/inter/Inter-Regular.otf")
INTER_BOLD = INTER.replace("Regular", "SemiBold")

W, H = 1920, 1080
# Panel rectangle as percentages of the screen (keep in sync with theme.txt)
PX, PY, PW, PH = 0.27, 0.24, 0.46, 0.52
SS = 4  # supersampling for smooth corners


def rounded_mask(w, h, r):
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def background():
    bg = Image.open(WALL).convert("RGB").resize((W, H), Image.LANCZOS)
    x, y, w, h = int(PX * W), int(PY * H), int(PW * W), int(PH * H)
    r = 28
    region = bg.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(26))
    tint = Image.new("RGB", (w, h), (28, 20, 62))
    region = Image.blend(region, tint, 0.52)
    # soft top highlight so the panel reads as glass
    grad = np.linspace(0.10, 0.0, h)[:, None, None] * np.ones((h, w, 1))
    arr = np.asarray(region, dtype=np.float32)
    arr = arr + (255 - arr) * grad
    region = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    mask = rounded_mask(w, h, r)
    # 1.5px light border
    ring = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(ring)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, outline=255, width=int(1.5 * SS))
    ring = ring.resize((w, h), Image.LANCZOS).point(lambda v: int(v * 0.30))
    # drop shadow
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x, y + 14, x + w, y + h + 14], r, fill=120)
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    bg = Image.composite(Image.new("RGB", (W, H), (4, 2, 14)), bg, shadow)
    bg.paste(region, (x, y), mask)
    bg.paste(Image.new("RGB", (w, h), (255, 255, 255)), (x, y), ring)
    return bg


def pill(w, h, r, fill, border, bw):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=border)
    d.rounded_rectangle([bw * SS, bw * SS, w * SS - 1 - bw * SS, h * SS - 1 - bw * SS],
                        (r - bw) * SS, fill=(0, 0, 0, 0))
    # transparent inner needs compositing: draw fill into a separate layer
    inner = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(inner).rounded_rectangle(
        [bw * SS, bw * SS, w * SS - 1 - bw * SS, h * SS - 1 - bw * SS], (r - bw) * SS, fill=fill)
    out = Image.alpha_composite(inner, img)
    return out.resize((w, h), Image.LANCZOS)


def selection_slices():
    # GRUB draws the border slices OUTSIDE the item area, so keep them small (12px).
    r = 12
    size = 2 * r + 8
    p = pill(size, size, r, fill=(182, 156, 255, 64), border=(255, 107, 129, 235), bw=2)
    b = [0, r, size - r, size]
    names = {
        ("nw"): (b[0], b[0], b[1], b[1]), ("n"): (b[1], b[0], b[2], b[1]), ("ne"): (b[2], b[0], b[3], b[1]),
        ("w"): (b[0], b[1], b[1], b[2]), ("c"): (b[1], b[1], b[2], b[2]), ("e"): (b[2], b[1], b[3], b[2]),
        ("sw"): (b[0], b[2], b[1], b[3]), ("s"): (b[1], b[2], b[2], b[3]), ("se"): (b[2], b[2], b[3], b[3]),
    }
    blank = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for n, box in names.items():
        p.crop(box).save(os.path.join(OUT, f"select_{n}.png"))
        # Unselected items need an invisible box of the same border size, otherwise GRUB
        # offsets only the selected item's content and the rows look unevenly spaced.
        blank.crop(box).save(os.path.join(OUT, f"item_{n}.png"))


def icon(letter, c1, c2, name, glyph=None):
    s = 128
    img = Image.new("RGBA", (s * SS // 2, s * SS // 2), (0, 0, 0, 0))
    big = s * SS // 2
    # diagonal gradient rounded square
    yy, xx = np.mgrid[0:big, 0:big]
    t = (xx + yy) / (2.0 * big)
    a = np.array(c1, dtype=np.float32)
    b = np.array(c2, dtype=np.float32)
    grad = (a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]).astype(np.uint8)
    base = Image.fromarray(grad, "RGB").convert("RGBA")
    m = Image.new("L", (big, big), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, big - 1, big - 1], big * 0.26, fill=255)
    img.paste(base, (0, 0), m)
    d = ImageDraw.Draw(img)
    if glyph == "chip":
        c = big // 2
        k = int(big * 0.22)
        d.rounded_rectangle([c - k, c - k, c + k, c + k], int(k * 0.3), outline=(255, 255, 255, 255), width=int(big * 0.05))
        for i in (-1, 0, 1):
            off = int(i * k * 0.9 * 0.55)
            d.line([c + off, c - k - int(big * .1), c + off, c - k], fill=(255, 255, 255, 255), width=int(big * 0.04))
            d.line([c + off, c + k, c + off, c + k + int(big * .1)], fill=(255, 255, 255, 255), width=int(big * 0.04))
            d.line([c - k - int(big * .1), c + off, c - k, c + off], fill=(255, 255, 255, 255), width=int(big * 0.04))
            d.line([c + k, c + off, c + k + int(big * .1), c + off], fill=(255, 255, 255, 255), width=int(big * 0.04))
    else:
        f = ImageFont.truetype(INTER_BOLD, int(big * 0.58))
        bbox = d.textbbox((0, 0), letter, font=f)
        d.text(((big - (bbox[2] - bbox[0])) / 2 - bbox[0], (big - (bbox[3] - bbox[1])) / 2 - bbox[1]),
               letter, font=f, fill=(255, 255, 255, 255))
    img.resize((64, 64), Image.LANCZOS).save(os.path.join(OUT, "icons", f"{name}.png"))


def fonts():
    # -n sets the family name; theme.txt refers to "Dragon UI Regular <size>"
    for size in (16, 20, 30):
        subprocess.run(["grub-mkfont", "-s", str(size), "-n", "Dragon UI", "-o",
                        os.path.join(OUT, f"dragon-ui-{size}.pf2"), INTER], check=True)


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "icons"), exist_ok=True)
    background().save(os.path.join(OUT, "background.png"))
    selection_slices()
    purple, rose, deep = (150, 118, 255), (240, 96, 122), (74, 52, 170)
    icon("W", (110, 140, 255), (88, 70, 220), "windows")           # generic monogram, not a brand logo
    icon("F", purple, deep, "fedora")
    icon("L", purple, deep, "gnu-linux")
    icon("", rose, (150, 40, 90), "efi", glyph="chip")
    icon("", rose, (150, 40, 90), "uefi", glyph="chip")
    icon("N", purple, rose, "os")
    if "--no-fonts" not in sys.argv:
        fonts()
    print("wrote", OUT)
