# Audite — 15-second motion teaser

A full-screen GitHub Pages advertisement with a native **3840×2160** desktop
film, **1080×1920** portrait film, and an HD fallback for devices that cannot
play UHD smoothly. No text is cropped on unusual screen proportions. Each scene
has a flat background. The decoded frame and its viewport extension are painted
on one opaque canvas, extending a flat corner pixel from that exact frame. This
keeps the whole background uniform without gradients, masks or edge fades.

Electric blue, violet and acid lime form the visual palette. The fictional
architectural model rotates, reveals its structure, separates into floors,
and becomes a plan view. Three identical **“Это Audite!”** bumpers connect
those scenes. Cuts follow the measured 120 BPM percussion grid; bumper copy
is in position from its first frame. Autoplay starts muted; the sound button enables music. Clicking
the film or pressing Space/Enter pauses and resumes it. Reduced-motion
preferences pause playback.

## Reproduce

Requires Blender 5.2, Python, and `production/requirements.txt`. Manrope and its
OFL license are included. Download the licensed soundtrack separately from
its source, keeping the raw MP3 outside this public repository.

```sh
python production/render_teaser.py /path/to/export \
  --frames /path/to/intermediate-frames \
  --music /path/to/licensed-frenzy.mp3
```

Copy only the finished MP4 files and posters to `assets/`; keep raw audio and
intermediate model frames outside the repository. Export manifests and review
sheets document the native dimensions, timeline and music source.

## Sources

See [media provenance](production/MEDIA_SOURCES.md). Architecture is authored
procedural geometry and contains no private Revit model, client project, audit
report, or application source. Music is a licensed synchronized excerpt of
**Frenzy (no vocal) by ScrewedQueen**, used under the Pixabay Content License.
It is registered with YouTube Content ID; use Pixabay's license certificate
if an automated YouTube claim needs to be released.
