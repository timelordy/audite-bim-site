"""Timing, typography and composition for the native UHD Audite film."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FPS = 30
LENGTH = 15
INK = '#11154F'
PAPER = '#FFFFFF'
LIME = '#DFFF00'
BLUE = '#284CFF'
VIOLET = '#6D31F4'
FONT = Path(__file__).parent / 'fonts' / 'Manrope.ttf'
TIMELINE = [
    (0, 2.5, 'hero', 0), (2.5, 3.5, 'bumper', None),
    (3.5, 6, 'rules', 1), (6, 7, 'bumper', None),
    (7, 9.5, 'findings', 2), (9.5, 10.5, 'bumper', None),
    (10.5, 13, 'plan', 3), (13, 15, 'outro', None),
]
COPY = {
    'rules': ('Проверка', 'по правилам.'),
    'findings': ('Находки', 'в фокусе.'),
    'plan': ('План', 'исправлений.'),
}


def ease(value):
    value = max(0, min(1, value))
    return 1 - (1 - value) ** 3


@lru_cache(maxsize=48)
def font(size, weight=800):
    result = ImageFont.truetype(str(FONT), round(size))
    result.set_variation_by_axes([weight])
    return result


def fit_font(text, size, width, weight=800):
    result = font(size, weight)
    if result.getlength(text) <= width:
        return result
    return font(size * width / result.getlength(text), weight)


def text(draw, value, x, y, size, color, max_width, centered=False, weight=800):
    face = fit_font(value, size, max_width, weight)
    if centered:
        x -= face.getlength(value) / 2
    draw.text((round(x), round(y)), value, font=face, fill=color, anchor='lt')


@lru_cache(maxsize=8)
def background(width, height, name):
    colors = {'hero': BLUE, 'rules': VIOLET, 'findings': LIME,
              'plan': '#1741E8', 'outro': BLUE, 'bumper': LIME}
    image = Image.new('RGB', (width, height), colors[name])
    if name in ('bumper', 'outro'):
        return image
    # A colored studio halo frames the architecture without competing with copy.
    glow = Image.new('RGBA', (width // 4, height // 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    center = (.72, .51) if width > height else (.5, .67)
    cx, cy = int(center[0] * glow.width), int(center[1] * glow.height)
    radius = int(min(glow.size) * .57)
    d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
              fill=(255, 255, 255, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(radius * .65))
    mask = glow.getchannel('A').resize(image.size, Image.Resampling.BILINEAR)
    light = Image.new('RGB', image.size, '#7C91FF' if name != 'findings' else '#EDFF72')
    image.paste(light, (0, 0), mask)
    return image


def place_model(canvas, layer_path, progress):
    width, height = canvas.size
    portrait = height > width
    scale = 1 + .025 * ease(progress)
    size = round(width * (1.14 if portrait else .565) * scale)
    layer = Image.open(layer_path).convert('RGBA')
    layer = layer.resize((size, size), Image.Resampling.LANCZOS)
    center = (width * .50, height * .66) if portrait else (width * .728, height * .51)
    position = (round(center[0] - size / 2), round(center[1] - size / 2))
    canvas.paste(layer, position, layer)


def scene_heading(canvas, name, local):
    width, height = canvas.size
    portrait = height > width
    d = ImageDraw.Draw(canvas)
    color = INK if name == 'findings' else PAPER
    x = width * (.09 if portrait else .065)
    shift = (1 - ease(local / .3)) * height * .013
    if name == 'hero':
        y = height * (.17 if portrait else .355) + shift
        text(d, 'Audite', x, y, width * (.215 if portrait else .102), color,
             width * (.82 if portrait else .4))
        text(d, 'Модель под контролем.', x, y + height * (.10 if portrait else .175),
             width * (.051 if portrait else .0215), LIME,
             width * (.82 if portrait else .4), weight=550)
        return
    first, second = COPY[name]
    size = width * (.119 if portrait else .062)
    y = height * (.18 if portrait else .34) + shift
    line = size * 1.23
    maximum = width * (.82 if portrait else .40)
    text(d, first, x, y, size, color, maximum)
    text(d, second, x, y + line, size, color, maximum)


def brand_card(canvas, name, local):
    width, height = canvas.size
    portrait = height > width
    d = ImageDraw.Draw(canvas)
    if name == 'bumper':
        size = width * (.115 if portrait else .084)
        y = height * .46 - (1 - ease(local / .18)) * height * .018
        text(d, 'Это Audite!', width / 2, y, size, INK, width * .84, True)
        return
    text(d, 'Audite', width / 2, height * .335,
         width * (.215 if portrait else .14), PAPER, width * .82, True)
    text(d, 'Скоро.', width / 2, height * (.505 if portrait else .59),
         width * (.066 if portrait else .029), LIME, width * .80, True, 650)
    text(d, 'audite-bim.ru', width / 2, height * (.595 if portrait else .685),
         width * (.032 if portrait else .014), PAPER, width * .80, True, 500)


def compose(width, height, frame, model_dir):
    time = frame / FPS
    start, end, name, shot = next(x for x in TIMELINE if x[0] <= time < x[1])
    canvas = background(width, height, name).copy()
    local = time - start
    if shot is None:
        brand_card(canvas, name, local)
        return canvas
    progress = local / (end - start)
    model_frame = min(74, round(progress * 74))
    place_model(canvas, model_dir / f'shot-{shot}-{model_frame:03d}.png', progress)
    scene_heading(canvas, name, local)
    return canvas
