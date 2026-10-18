#!/usr/bin/env python3
"""Generate the two wallpapers (light + dark): soft layered ridges on a pastel sky.
Original artwork, generated procedurally. Needs: pip install pillow numpy scipy"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, gaussian_filter

W, H = 3840, 2160


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def vgrad(stops):
    """Vertical multi-stop gradient. stops = [(pos 0..1, '#hex'), ...]"""
    ys = np.linspace(0, 1, H)[:, None]
    pos = [p for p, _ in stops]
    cols = np.stack([hexrgb(c) for _, c in stops])
    out = np.stack([np.interp(ys[:, 0], pos, cols[:, k]) for k in range(3)], axis=1)
    return np.repeat(out[:, None, :], W, axis=1)


def ridge(rng, base, amp, seed_freqs):
    x = np.linspace(0, 1, W)
    y = np.zeros(W)
    for f in seed_freqs:
        y += rng.uniform(0.4, 1.0) * np.sin(2 * np.pi * (f * x + rng.uniform(0, 1)))
    y = gaussian_filter1d(y, 40)
    y = (y - y.min()) / (y.max() - y.min() + 1e-9)
    return (base + amp * (y - 0.5)) * H


def layer(img, rng, base, amp, freqs, top, bottom, haze):
    r = ridge(rng, base, amp, freqs)
    yy = np.arange(H)[:, None]
    mask = np.clip((yy - r[None, :]) / 3.0, 0, 1)  # anti-aliased edge
    t = np.clip((yy - r[None, :]) / (H * 0.45), 0, 1)
    col = hexrgb(top)[None, None, :] * (1 - t[..., None]) + hexrgb(bottom)[None, None, :] * t[..., None]
    col = col * (1 - haze) + img * haze  # atmospheric haze toward background
    return img * (1 - mask[..., None]) + col * mask[..., None]


def glow(img, cx, cy, radius, color, strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - cx * W) / (radius * W)) ** 2 + ((yy - cy * H) / (radius * W)) ** 2)
    g = np.exp(-d ** 2 * 2.2)[..., None] * strength
    return img * (1 - g) + hexrgb(color)[None, None, :] * g


def build(mode):
    rng = np.random.default_rng(7 if mode == "light" else 11)
    if mode == "light":
        img = vgrad([(0, "#c9d3ff"), (0.45, "#e6d3fb"), (0.75, "#fbd2e4"), (1, "#ffe3d2")])
        img = glow(img, 0.72, 0.62, 0.45, "#ffd9e6", 0.55)
        layers = [
            (0.62, 0.22, [1.0, 1.7, 2.9], "#d9ccf7", "#cdbdf2", 0.35),
            (0.72, 0.20, [1.3, 2.1, 3.3], "#c4b4f1", "#b9a6ea", 0.22),
            (0.82, 0.18, [0.9, 1.9, 3.7], "#f1b7d2", "#e7a2c4", 0.12),
            (0.92, 0.14, [1.1, 2.6, 4.1], "#a98ee6", "#9478d8", 0.0),
        ]
    else:
        img = vgrad([(0, "#0d0a1f"), (0.5, "#1b1240"), (0.8, "#3a1646"), (1, "#4a1a3d")])
        img = glow(img, 0.7, 0.66, 0.38, "#ff4d6d", 0.42)
        img = glow(img, 0.3, 0.5, 0.5, "#6a42d9", 0.25)
        layers = [
            (0.62, 0.22, [1.0, 1.7, 2.9], "#3b2a7a", "#2b1d5e", 0.45),
            (0.72, 0.20, [1.3, 2.1, 3.3], "#2f2066", "#231650", 0.30),
            (0.82, 0.18, [0.9, 1.9, 3.7], "#4a1d55", "#341340", 0.18),
            (0.92, 0.14, [1.1, 2.6, 4.1], "#1a1038", "#120a2a", 0.0),
        ]
    for base, amp, freqs, top, bottom, haze in layers:
        img = layer(img, rng, base, amp, freqs, top, bottom, haze)
    img = gaussian_filter(img, sigma=(1.2, 1.2, 0))  # soften
    img += rng.normal(0, 1.4, img.shape)  # fine grain, avoids banding
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for m in ("light", "dark"):
        build(m).save(f"{out}/dragon-{m}.jpg", quality=92, subsampling=0)
        print("wrote", f"{out}/dragon-{m}.jpg")
