const video = document.querySelector('#film');
const error = document.querySelector('#media-error');
const fallback = document.querySelector('#download-fallback');
const soundToggle = document.querySelector('#sound-toggle');
const portrait = window.matchMedia('(max-aspect-ratio: 1/1)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const edition = '20261008-v2';
let useHd = false;
let qualityChecked = false;

function selectFilm() {
  const file = portrait.matches ? 'audite-portrait.mp4' :
    (useHd ? 'audite-landscape-hd.mp4' : 'audite-landscape.mp4');
  const poster = portrait.matches ? 'audite-portrait-poster.png' : 'audite-landscape-poster.png';
  const url = new URL(`assets/${file}?v=${edition}`, document.baseURI).href;
  if (video.src === url) return;
  video.src = url;
  video.poster = new URL(`assets/${poster}?v=${edition}`, document.baseURI).href;
  fallback.href = url;
  error.hidden = true;
  video.load();
  if (!reducedMotion.matches) video.play().catch(() => {});
}

function applyMotionPreference() {
  video.autoplay = !reducedMotion.matches;
  if (reducedMotion.matches) video.pause();
  else video.play().catch(() => {});
}

video.addEventListener('error', () => {
  if (!portrait.matches && !useHd) {
    useHd = true;
    selectFilm();
    return;
  }
  error.hidden = false;
});
video.addEventListener('loadeddata', () => { error.hidden = true; });
video.addEventListener('timeupdate', () => {
  if (qualityChecked || portrait.matches || useHd || video.currentTime < 3) return;
  qualityChecked = true;
  const quality = video.getVideoPlaybackQuality?.();
  if (quality?.totalVideoFrames > 60 &&
      quality.droppedVideoFrames / quality.totalVideoFrames > .15) {
    useHd = true;
    selectFilm();
  }
});
video.addEventListener('click', () => {
  if (video.paused) video.play().catch(() => {});
  else video.pause();
});
video.addEventListener('keydown', event => {
  if (event.code === 'Space' || event.code === 'Enter') {
    event.preventDefault();
    if (video.paused) video.play().catch(() => {});
    else video.pause();
  }
});
soundToggle.addEventListener('click', () => {
  video.muted = !video.muted;
  soundToggle.classList.toggle('is-muted', video.muted);
  soundToggle.setAttribute('aria-label', video.muted ? 'Включить звук' : 'Выключить звук');
  soundToggle.title = video.muted ? 'Включить звук' : 'Выключить звук';
  if (video.paused) video.play().catch(() => {});
});
portrait.addEventListener('change', selectFilm);
reducedMotion.addEventListener('change', applyMotionPreference);
applyMotionPreference();
selectFilm();
