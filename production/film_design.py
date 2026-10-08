"""Timing, typography and composition for the native UHD Audite film."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FPS = 30
LENGTH = 15
INK = '#11154F'
PAPER = '#FFFFFF'
LIME = '#DFFF00'
BLUE = '#284CFF'
VIOLET = '#6D31F4'
FONT = Path(__file__).parent / 'fonts' / 'Manrope.ttf'
TIMELINE = [
    (0, 1, 'bookend', None), (1, 3, 'hero', 0),
    (3, 3.5, 'bumper', None), (3.5, 5.5, 'rules', 1),
    (5.5, 6, 'bumper', None), (6, 8, 'findings', 2),
    (8, 8.5, 'bumper', None), (8.5, 10.5, 'plan', 3),
    (10.5, 12.5, 'ai', None), (12.5, 14, 'outro', None),
    (14, 15, 'bookend', None),
]
COPY = {
    'hero': ('Проверь модель', 'до стройки.'),
    'rules': ('Найди ошибки', 'в модели.'),
    'findings': ('Разберись,', 'что исправить.'),
    'plan': ('Получи план', 'исправлений.'),
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
              'plan': '#1741E8', 'ai': VIOLET, 'outro': BLUE,
              'bookend': BLUE, 'bumper': LIME}
    return Image.new('RGB', (width, height), colors[name])


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


def scene_heading(canvas, name):
    width, height = canvas.size
    portrait = height > width
    d = ImageDraw.Draw(canvas)
    color = INK if name == 'findings' else PAPER
    x = width * (.09 if portrait else .065)
    first, second = COPY[name]
    size = width * (.119 if portrait else .062)
    y = height * (.18 if portrait else .34)
    maximum = width * (.82 if portrait else .40)
    longest = max(font(size).getlength(value) for value in (first, second))
    size *= min(1, maximum / longest)
    line = size * 1.23
    text(d, first, x, y, size, color, maximum)
    text(d, second, x, y + line, size, color, maximum)


def ai_card(canvas, progress):
    width, height = canvas.size
    portrait = height > width
    d = ImageDraw.Draw(canvas)
    # A small settling movement keeps the complete question readable throughout.
    scale = 1 + .025 * (1 - ease(progress * 3))
    text(d, 'А может,', width / 2, height * (.31 if portrait else .30),
         width * (.095 if portrait else .040) * scale,
         PAPER, width * .84, True, 650)
    question = 'ИИ исправит' if portrait else 'ИИ исправит сам?'
    face = fit_font(question, width * (.12 if portrait else .080) * scale,
                    width * .84)
    x = (width - face.getlength(question)) / 2
    y = height * (.405 if portrait else .445)
    d.text((round(x), round(y)), 'ИИ', font=face, fill=LIME, anchor='lt')
    x += face.getlength('ИИ')
    d.text((round(x), round(y)), question[2:], font=face, fill=PAPER, anchor='lt')
    if portrait:
        text(d, 'сам?', width / 2, height * .49, width * .12 * scale,
             PAPER, width * .84, True)


def brand_card(canvas, name):
    width, height = canvas.size
    portrait = height > width
    d = ImageDraw.Draw(canvas)
    if name == 'bumper':
        size = width * (.115 if portrait else .084)
        y = height * .46
        text(d, 'Это Audite!', width / 2, y, size, INK, width * .84, True)
        return
    text(d, 'Audite', width / 2, height * .31,
         width * (.215 if portrait else .14), PAPER, width * .82, True)
    if name == 'bookend':
        size = width * (.050 if portrait else .023)
        y = height * (.49 if portrait else .59)
        text(d, 'Аудит BIM-моделей', width / 2, y,
             size, PAPER, width * .84, True, 550)
        return
    text(d, 'Скоро.', width / 2, height * (.505 if portrait else .59),
         width * (.066 if portrait else .029), LIME, width * .80, True, 650)
    text(d, 'audite-bim.ru', width / 2, height * (.595 if portrait else .685),
         width * (.032 if portrait else .014), PAPER, width * .80, True, 500)


def compose(width, height, frame, model_dir):
    time = frame / FPS
    start, end, name, shot = next(x for x in TIMELINE if x[0] <= time < x[1])
    canvas = background(width, height, name).copy()
    local = time - start
    if name == 'ai':
        ai_card(canvas, local / (end - start))
        return canvas
    if shot is None:
        brand_card(canvas, name)
        return canvas
    progress = local / (end - start)
    model_frame = min(74, round(progress * 74))
    place_model(canvas, model_dir / f'shot-{shot}-{model_frame:03d}.png', progress)
    scene_heading(canvas, name)
    return canvas
