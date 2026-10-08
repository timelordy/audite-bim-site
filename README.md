# Audite — 15-second motion teaser

A full-screen GitHub Pages advertisement with a native **3840×2160** desktop
film, **1080×1920** portrait film, and an HD fallback for devices that cannot
play UHD smoothly. No text is cropped on unusual screen proportions. Each scene
has a flat background. Each delivered video frame is captured once as an immutable
bitmap. Its background extension and full frame are composed offscreen, then
presented together in one canvas update. This keeps colors synchronized at cuts.

Electric blue, violet and acid lime form the visual palette. The fictional
architectural model rotates, reveals its structure, separates into floors,
and becomes a plan view. Three identical **“Это Audite!”** bumpers connect
those scenes. Copy introduces **Audite as an audit of BIM models** and leads with
**“Проверь модель до стройки.”** Cuts follow the measured 120 BPM percussion grid.
The opening and final cards are identical, and audio fades through the loop boundary.
A quiet 1.8-second entry card precedes playback, which waits for decoded video
and at least three buffered seconds. Autoplay starts muted; the sound button enables music. Clicking
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
procedural geometry and contains no private BIM model, client project, audit
report, or application source. Music is a licensed synchronized excerpt of
**Frenzy (no vocal) by ScrewedQueen**, used under the Pixabay Content License.
It is registered with YouTube Content ID; use Pixabay's license certificate
if an automated YouTube claim needs to be released.
