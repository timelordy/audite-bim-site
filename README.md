# Audite — launch teaser

Static GitHub Pages site showing a 15-second full-screen motion film. It selects a landscape or portrait MP4 and includes original synthesized audio. Autoplay starts muted; browser controls let visitors unmute or replay.

The building visuals in `production/visual-assets/` are **fictional illustrations**. This repository contains no Revit model, object profile, audit report, client data, or source from the private application repository.

## Regenerate the films

On macOS, install the Python packages in `production/requirements.txt`, then run:

```sh
python production/render_teaser.py assets
rm audite-synth.wav
```

The renderer uses macOS Arial Black from `/System/Library/Fonts/Supplemental/`. It writes both MP4 cuts and their posters to `assets/`.
