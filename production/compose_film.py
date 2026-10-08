"""Encode native typography and 3D layers with a licensed phonk soundtrack."""
from __future__ import annotations

import argparse
from array import array
import json
import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

from film_design import FPS, LENGTH, compose

MUSIC_START = 16.035  # 120 BPM grid fitted to the source percussion attacks.
MUSIC_OVERLAP = .5  # One aligned beat; the output stays exactly 30 beats long.
AUDIO_RATE = 48000


def loop_gain(samples, peak):
    pcm = array('f', samples)
    if sys.byteorder != 'little':
        pcm.byteswap()
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-f', 'f32le',
         '-ar', str(AUDIO_RATE), '-ac', '2', '-i', '-',
         '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json',
         '-f', 'null', '-'], input=pcm.tobytes(), capture_output=True, check=True)
    report = result.stderr.decode()
    loudness, _ = json.JSONDecoder().raw_decode(report[report.rfind('{'):])
    # Apply one constant gain so normalization cannot change either seam edge.
    return min(10 ** ((-14 - float(loudness['input_i'])) / 20),
               (10 ** (-1.5 / 20)) / peak)


def prepare_audio(source, output):
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error',
               '-ss', str(MUSIC_START), '-i', str(source),
               # Decode a little beyond the cut; resampler timestamps can be a
               # sample short. Slice to exact PCM counts below.
               '-t', str(LENGTH + MUSIC_OVERLAP + .01), '-ar', str(AUDIO_RATE),
               '-ac', '2', '-f', 'f32le', '-']
    samples = array('f', subprocess.run(command, check=True, capture_output=True).stdout)
    if sys.byteorder != 'little':
        samples.byteswap()
    count = AUDIO_RATE * LENGTH * 2
    overlap_frames = round(AUDIO_RATE * MUSIC_OVERLAP)
    if len(samples) < count + overlap_frames * 2:
        raise ValueError('Soundtrack is too short for the circular crossfade')
    loop = samples[:count]
    # Continue the ending into the extra source beat, then blend into the opening.
    # The first output sample follows the last one naturally, with no silence.
    for frame in range(overlap_frames):
        incoming = frame / (overlap_frames - 1)
        for channel in range(2):
            index = frame * 2 + channel
            loop[index] = (samples[count + index] * (1 - incoming)
                           + samples[index] * incoming)
    peak = max(abs(value) for value in loop)
    if peak == 0:
        raise ValueError('Soundtrack contains only silence')
    gain = loop_gain(loop, peak)
    pcm = array('h', (round(value * gain * 32767) for value in loop))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(output), 'wb') as stream:
        stream.setparams((2, 2, AUDIO_RATE, 0, 'NONE', 'not compressed'))
        stream.writeframes(pcm.tobytes())


def render_video(width, height, models, audio, output):
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error',
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{height}',
               '-r', str(FPS), '-i', '-', '-i', str(audio),
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
               '-pix_fmt', 'yuv420p', '-profile:v', 'high',
               '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart',
               '-t', str(LENGTH), str(output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(FPS * LENGTH):
            process.stdin.write(compose(width, height, frame, models).tobytes())
            if frame % 75 == 0:
                print(f'{output.name}: {frame}/450', flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f'Video encoder failed: {output}')
    poster = compose(width, height, 0, models)
    poster.save(output.with_name(output.stem + '-poster.png'), optimize=True)


def review_sheet(models, output, portrait=False, tests=False):
    times = [0, 1.6, 4.5, 6.8, 9.5, 11.5, 13.2, 14.9]
    width, height = (1080, 1920) if portrait else (1920, 1080)
    thumb_w, thumb_h = ((270, 480) if portrait else (640, 360))
    sheet = Image.new('RGB', (thumb_w * 4, (thumb_h + 34) * 2), '#252B28')
    for i, time in enumerate(times):
        if tests:
            # Duplicate the four accepted pose previews only for art-direction QA.
            source = models / f'shot-{min(3, i // 2)}-000.png'
            for frame in range(75):
                target = models / f'shot-{min(3, i // 2)}-{frame:03d}.png'
                if not target.exists():
                    target.symlink_to(source)
        image = compose(width, height, round(time * FPS), models)
        image = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x, y = (i % 4) * thumb_w, (i // 4) * (thumb_h + 34)
        sheet.paste(image, (x, y))
        ImageDraw.Draw(sheet).text((x + 12, y + thumb_h + 9), f'{time:.1f}s', fill='white')
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--music', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--review-only', action='store_true')
    parser.add_argument('--tests', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    review_sheet(args.models, args.out / 'desktop-review.jpg', tests=args.tests)
    review_sheet(args.models, args.out / 'portrait-review.jpg', True, args.tests)
    if args.review_only:
        return
    audio = args.out / 'licensed-cut.wav'
    prepare_audio(args.music, audio)
    render_video(3840, 2160, args.models, audio, args.out / 'audite-landscape.mp4')
    render_video(1080, 1920, args.models, audio, args.out / 'audite-portrait.mp4')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error',
                    '-i', str(args.out / 'audite-landscape.mp4'),
                    '-vf', 'scale=1920:1080', '-c:v', 'libx264', '-crf', '20',
                    '-preset', 'fast', '-c:a', 'copy', '-movflags', '+faststart',
                    str(args.out / 'audite-landscape-hd.mp4')], check=True)
    audio.unlink()
    manifest = {'duration': LENGTH, 'fps': FPS, 'desktop': [3840, 2160],
                'desktop_fallback': [1920, 1080], 'portrait': [1080, 1920],
                'bumper_copy': 'Это Audite!', 'bumper_count': 3,
                'loop_bookends': [0, 14], 'entry_hold_seconds': 1.8,
                'plan_scene': [8.5, 10.5], 'ai_scene': [10.5, 12.5],
                'ai_copy': 'А может, ИИ исправит сам?',
                'music': 'Frenzy (no vocal) — ScrewedQueen',
                'music_source': 'https://pixabay.com/music/242261/',
                'music_license': 'Pixabay Content License',
                'music_source_window': [MUSIC_START, MUSIC_START + LENGTH + MUSIC_OVERLAP],
                'music_circular_crossfade_seconds': MUSIC_OVERLAP,
                'music_bpm_measured': 120}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
