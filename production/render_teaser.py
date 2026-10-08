"""Render Audite's 15-second kinetic launch film in landscape and portrait.

Everything is drawn from typography and abstract geometry. Audio is synthesized
here, so the exported film contains no external images, samples, or model data.
"""

from __future__ import annotations

import math
import random
import subprocess
import sys
import wave
from array import array
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


FPS, LENGTH = 30, 15
BLACK = (5, 8, 12)
LIME = (219, 255, 34)
COBALT = (38, 67, 237)
WHITE = (247, 249, 245)
ORANGE = (255, 100, 45)
ICE = (236, 244, 250)
NAVY = (10, 21, 48)
FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
ASSETS = Path(__file__).parent / "visual-assets"
MODELS = {
    "cutaway": Image.open(ASSETS / "bim-cutaway.png").convert("RGBA"),
    "exploded": Image.open(ASSETS / "bim-exploded.png").convert("RGBA"),
}

SCENES = [
    (0.0, 1.8, "brand", LIME),
    (1.8, 4.0, "model", BLACK),
    (4.0, 6.3, "check", ICE),
    (6.3, 8.6, "findings", ORANGE),
    (8.6, 10.9, "plan", NAVY),
    (10.9, 13.0, "decision", COBALT),
    (13.0, 15.0, "outro", BLACK),
]


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease(value: float) -> float:
    p = clamp(value)
    return 1 - (1 - p) ** 3


def font_fit(text: str, max_width: int, desired: int, path: str = FONT_HEAVY):
    size = desired
    while size > 22:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= max_width:
            return f
        size -= 2
    return ImageFont.truetype(path, 22)


def text_line(d: ImageDraw.ImageDraw, text: str, y: int, width: int,
              color: tuple[int, int, int], time: float, scene_start: float,
              scene_end: float, desired: int, centered: bool = False) -> None:
    local = time - scene_start
    departure = scene_end - time
    safe_margin = .14 if width < 900 else .06
    font = font_fit(text, int(width * (1 - 2 * safe_margin)), desired)
    length = font.getlength(text)
    target_x = (width - length) / 2 if centered else width * safe_margin
    shift = (1 - ease((local - .05) / .27)) * (-width * 1.05)
    shift += ease((.25 - departure) / .22) * width * 1.15
    x = int(target_x + shift)
    if local < .28 or departure < .23:
        d.text((x - 15, y), text, font=font, fill=COBALT if color != COBALT else ORANGE,
               stroke_width=0)
        d.text((x + 8, y), text, font=font, fill=ORANGE if color != ORANGE else LIME)
    d.text((x, y), text, font=font, fill=color)


def background(d: ImageDraw.ImageDraw, w: int, h: int, t: float, name: str,
               color: tuple[int, int, int]) -> None:
    line = {
        BLACK: (27, 36, 52), NAVY: (25, 47, 92), COBALT: (72, 100, 250),
        LIME: (180, 210, 38), ICE: (207, 222, 234), ORANGE: (230, 83, 39),
    }[color]
    for i in range(-15, 26):
        slide = (t * 175) % 150
        x = i * 112 + slide
        d.line([(x, 0), (x + int(h * .55), h)], fill=line, width=2 if i % 3 == 0 else 1)
    if name == "plan":
        for i in range(4):
            xx = int((t * 310 + i * w * .33) % (w + 300) - 220)
            yy = int(h * (.22 + i * .16))
            d.polygon([(xx, yy), (xx+180, yy), (xx+235, yy+22), (xx+180, yy+44), (xx, yy+44)], fill=LIME if i % 2 == 0 else COBALT)


def draw_model(image: Image.Image, w: int, h: int, t: float,
               start: float, name: str) -> None:
    if name not in ("model", "check", "findings", "plan", "decision"):
        return
    portrait = h > w
    asset = MODELS["exploded" if name in ("check", "plan") else "cutaway"]
    advance = ease((t - start) / .72)
    height = int(h * ((.59 if name in ("check", "plan") else .55) if portrait else
                      (1.1 if name in ("check", "plan") else 1.02)))
    height = int(height * (.86 + .11 * advance + .06 * clamp((t - start) / 2.2)))
    width = int(asset.width * height / asset.height)
    model = asset.resize((width, height), Image.Resampling.BILINEAR)
    if portrait:
        x = int((w - width) / 2 + (1 - advance) * 45)
        y = int(h * .045 - (1 - advance) * 75)
    else:
        x = int(w * (.56 if name in ("check", "plan") else .51) + (1 - advance) * 95)
        y = int((h - height) / 2 - (1 - advance) * 45)
    image.alpha_composite(model, (x, y))
    if name == "findings":
        d = ImageDraw.Draw(image)
        for i, (rx, ry) in enumerate(((.65, .38), (.83, .58), (.75, .77)) if not portrait else
                                     ((.36, .16), (.72, .33), (.46, .48))):
            cx, cy = int(w * rx), int(h * ry)
            radius = int((14 + i * 3) * (1 + .16 * math.sin(t * 9+i)))
            d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=WHITE, width=4)
            d.ellipse((cx-4, cy-4, cx+4, cy+4), fill=BLACK)


def scene_text(d: ImageDraw.ImageDraw, w: int, h: int, t: float,
               start: float, end: float, name: str) -> None:
    portrait = h > w
    base = int(w * (.10 if not portrait else .145))
    y1 = int(h * (.25 if not portrait else .65))
    gap = int(h * (.20 if not portrait else .11))
    area = w if portrait else int(w * .54)
    if name == "brand":
        y1 = int(h * (.28 if not portrait else .42))
        text_line(d, "Audite", y1, w, BLACK, t, start, end, int(w*.19), True)
        tagline_y = int(h * (.73 if not portrait else .56))
        text_line(d, "МОДЕЛЬ ПОД КОНТРОЛЕМ", tagline_y, w, BLACK, t, start+.12, end, int(w*.055), True)
    elif name == "model":
        text_line(d, "МОДЕЛЬ", y1, area, WHITE, t, start, end, base)
        text_line(d, "ПОД КОНТРОЛЕМ", y1 + gap, area, LIME, t, start+.16, end, base)
    elif name == "check":
        text_line(d, "ПРОВЕРКА", y1, area, BLACK, t, start, end, base)
        text_line(d, "ПО ПРАВИЛАМ", y1 + gap, area, COBALT, t, start+.15, end, base)
    elif name == "findings":
        text_line(d, "НАХОДКИ", y1, area, BLACK, t, start, end, base)
        text_line(d, "В ФОКУСЕ", y1 + gap, area, WHITE, t, start+.16, end, base)
    elif name == "plan":
        text_line(d, "ПЛАН", y1, area, WHITE, t, start, end, base)
        text_line(d, "ИСПРАВЛЕНИЙ", y1 + gap, area, LIME, t, start+.18, end, base)
    elif name == "decision":
        text_line(d, "ИИ ПРЕДЛАГАЕТ", y1, area, WHITE, t, start, end, base)
        text_line(d, "ТЫ РЕШАЕШЬ", y1 + gap, area, LIME, t, start+.15, end, base)
    else:
        text_line(d, "Audite", int(h * (.17 if not portrait else .32)), w, LIME,
                  t, start, end+.5, int(w*.20), True)
        text_line(d, "СКОРО", int(h * (.55 if not portrait else .53)), w, WHITE,
                  t, start+.12, end+.5, int(w*.12), True)
        text_line(d, "audite-bim.ru", int(h * (.76 if not portrait else .68)), w, LIME,
                  t, start+.23, end+.5, int(w*.058), True)


def frame(w: int, h: int, t: float) -> Image.Image:
    start, end, name, color = next(s for s in SCENES if s[0] <= t < s[1])
    image = Image.new("RGBA", (w, h), color)
    d = ImageDraw.Draw(image)
    background(d, w, h, t, name, color)
    draw_model(image, w, h, t, start, name)
    scene_text(d, w, h, t, start, end, name)
    flash = t - start
    if flash < .067 and start > 0:
        overlay = Image.new("RGBA", (w, h), WHITE if name != "findings" else COBALT)
        image = Image.blend(overlay, image, flash/.067)
    return image.convert("RGB")


def render_audio(out: Path) -> None:
    rate = 44100
    count = rate * LENGTH
    samples = array("f", [0.0]) * count
    rng = random.Random(3041)

    def kick(at: float, amp: float = .53) -> None:
        first = int(at * rate)
        for j in range(min(int(.31 * rate), count-first)):
            q = j / rate
            env = math.exp(-17*q)
            phase = 2*math.pi*(42*q + 58*(1-math.exp(-25*q))/25)
            samples[first+j] += amp*env*math.sin(phase)

    def snare(at: float) -> None:
        first = int(at * rate)
        for j in range(min(int(.16 * rate), count-first)):
            q = j/rate
            noise = rng.uniform(-1, 1)
            samples[first+j] += .19*math.exp(-32*q)*noise + .055*math.exp(-18*q)*math.sin(2*math.pi*185*q)

    for n in range(38):
        at = n * .4
        if at < LENGTH:
            kick(at, .65 if n % 4 == 0 else .45)
        off = at + .2
        if off < LENGTH:
            snare(off)
    for n in range(75):
        at = n * .2
        first = int(at*rate)
        for j in range(min(int(.055*rate), count-first)):
            q = j/rate
            samples[first+j] += .038*math.exp(-70*q)*rng.uniform(-1, 1)
    for boundary, *_ in SCENES[1:]:
        first = max(0, int((boundary-.28)*rate))
        end = min(count, int(boundary*rate))
        last = 0.0
        for i in range(first, end):
            q = (i-first)/(end-first)
            now = rng.uniform(-1, 1)
            samples[i] += .16*q*(now-last)
            last = now

    with wave.open(str(out), "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(rate)
        pcm = array("h")
        for i, value in enumerate(samples):
            fade = min(1, i/(rate*.08), (count-i)/(rate*.28))
            pcm.append(int(max(-1, min(1, value*fade))*32767))
        sound.writeframes(pcm.tobytes())


def render_video(w: int, h: int, audio: Path, out: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-i", str(audio),
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", str(LENGTH), str(out)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for n in range(FPS * LENGTH):
            process.stdin.write(frame(w, h, n / FPS).tobytes())
            if n % 120 == 0:
                print(f"{w}x{h}: {n}/{FPS*LENGTH}", file=sys.stderr)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"ffmpeg failed: {out}")
    frame(w, h, 13.9).save(out.with_name(out.stem + "-poster.png"), optimize=True)
    print(out)


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=True)
    audio_path = directory.parent / "audite-synth.wav"
    render_audio(audio_path)
    render_video(1280, 720, audio_path, directory / "audite-landscape.mp4")
    render_video(720, 1280, audio_path, directory / "audite-portrait.mp4")
