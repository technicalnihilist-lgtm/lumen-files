#!/usr/bin/env python3
"""Generates the Lumen Files launcher icon (adaptive + legacy mipmaps + store icon)."""
from PIL import Image, ImageDraw, ImageFilter
import os, math

S = 4                      # supersample factor
N = 432 * S                # adaptive icon canvas (108dp @ xxxhdpi = 432px)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def blobs(size, inset=0):
    """Dark navy base with the four app gradient blobs."""
    img = Image.new('RGB', (size, size), (11, 16, 48))
    blobs_spec = [('#ff5fa2', 0.16, 0.14, 0.44), ('#5b6cff', 0.88, 0.20, 0.48),
                  ('#12d6b0', 0.72, 0.88, 0.50), ('#ff9d3d', 0.10, 0.86, 0.42)]
    for hexc, cx, cy, rad in blobs_spec:
        col = tuple(int(hexc[i:i+2], 16) for i in (1, 3, 5))
        layer = Image.new('L', (size, size), 0)
        d = ImageDraw.Draw(layer)
        r = int(rad * size)
        d.ellipse([cx * size - r, cy * size - r, cx * size + r, cy * size + r], fill=255)
        layer = layer.filter(ImageFilter.GaussianBlur(int(size * 0.09)))
        img = Image.composite(Image.new('RGB', (size, size), col), img, layer)
    return img

def folder_glyph(size):
    """White glass folder mark on transparency."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = size * 0.52
    x0 = (size - w) / 2
    h = size * 0.40
    y0 = (size - h) / 2 + size * 0.03
    r = size * 0.055
    # back tab
    tabw = w * 0.46
    d.rounded_rectangle([x0, y0 - h * 0.20, x0 + tabw, y0 + h * 0.25],
                        radius=r * 0.85, fill=(255, 255, 255, 235))
    # body
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=r, fill=(255, 255, 255, 250))
    # glass sheen across the body
    sheen = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sheen)
    ds.polygon([(x0, y0 + h * 0.10), (x0 + w, y0), (x0 + w, y0 + h * 0.34),
                (x0, y0 + h * 0.46)], fill=(255, 255, 255, 90))
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=r, fill=255)
    img = Image.composite(Image.alpha_composite(img, sheen), img, mask)
    # soft shadow under the mark
    sh = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + h * 0.9, x0 + w, y0 + h * 1.02],
                                         radius=r, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.02))
    out = Image.alpha_composite(sh, img)
    return out

def legacy(size, bg_full, fg_full):
    """Legacy launcher icon: rounded square, bg + glyph."""
    bg = bg_full.resize((size, size), Image.LANCZOS).convert('RGBA')
    fg = fg_full.resize((size, size), Image.LANCZOS)
    tile = Image.alpha_composite(bg, fg)
    mask = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1],
                                           radius=int(size * 4 * 0.22), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(tile, (0, 0), mask)
    return out

root = os.path.dirname(os.path.abspath(__file__))
res = os.path.join(root, 'app', 'src', 'main', 'res')
os.makedirs(os.path.join(res, 'drawable'), exist_ok=True)

bg = blobs(N)
fg = folder_glyph(N)
bg.resize((N // S, N // S), Image.LANCZOS).save(os.path.join(res, 'drawable', 'ic_bg.png'))
fg.resize((N // S, N // S), Image.LANCZOS).save(os.path.join(res, 'drawable', 'ic_fg.png'))

bg_full = bg.resize((1024, 1024), Image.LANCZOS)
fg_full = folder_glyph(1024)
for dpi, px in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
    p = os.path.join(res, 'mipmap-' + dpi, 'ic_launcher.png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    legacy(px, bg_full, fg_full).save(p)

# store / readme icon
legacy(512, bg_full, fg_full).save(os.path.join(root, 'icon-512.png'))
print('icons written')
