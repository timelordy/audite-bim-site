const video = document.querySelector('#film');
const error = document.querySelector('#media-error');
const fallback = document.querySelector('#download-fallback');
const portrait = window.matchMedia('(max-width: 700px)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function selectFilm() {
  const file = portrait.matches ? 'audite-portrait.mp4' : 'audite-landscape.mp4';
  const poster = portrait.matches ? 'audite-portrait-poster.png' : 'audite-landscape-poster.png';
  const url = new URL(`assets/${file}`, document.baseURI).href;
  if (video.src === url) return;
  video.src = url;
  video.poster = new URL(`assets/${poster}`, document.baseURI).href;
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

video.addEventListener('error', () => { error.hidden = false; });
video.addEventListener('loadeddata', () => { error.hidden = true; });
portrait.addEventListener('change', selectFilm);
reducedMotion.addEventListener('change', applyMotionPreference);
applyMotionPreference();
selectFilm();
