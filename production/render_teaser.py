"""Reproduce the Audite film with Blender and a licensed local soundtrack."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--music', type=Path, required=True,
                        help='Locally downloaded and licensed Frenzy MP3')
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--skip-models', action='store_true')
    args = parser.parse_args()
    if not args.music.is_file():
        parser.error('The licensed music file does not exist.')
    source = Path(__file__).resolve().parent
    if not args.skip_models:
        subprocess.run(['blender', '-b', '-t', '6', '-P',
                        str(source / 'architecture.py'), '--',
                        '--out', str(args.frames.resolve()), '--size', '2400'], check=True)
    subprocess.run([sys.executable, str(source / 'compose_film.py'),
                    '--models', str(args.frames.resolve()),
                    '--music', str(args.music.resolve()),
                    '--out', str(args.output.resolve())], check=True)


if __name__ == '__main__':
    main()
