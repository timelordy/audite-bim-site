import { createFilmStage } from './film-stage.js?v=20261008-v6';

const video = document.querySelector('#film');
const canvas = document.querySelector('#film-stage');
const error = document.querySelector('#media-error');
const fallback = document.querySelector('#download-fallback');
const soundToggle = document.querySelector('#sound-toggle');
const portrait = window.matchMedia('(max-aspect-ratio: 1/1)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const edition = '20261008-v6';
let useHd = false;
let qualityChecked = false;

const stage = createFilmStage(video, canvas);
if (!stage) {
  canvas.hidden = true;
  soundToggle.disabled = true;
}

function selectFilm() {
  const file = portrait.matches ? 'audite-portrait.mp4' :
    (useHd ? 'audite-landscape-hd.mp4' : 'audite-landscape.mp4');
  const poster = portrait.matches ? 'audite-portrait-poster.png' : 'audite-landscape-poster.png';
  const url = new URL(`assets/${file}?v=${edition}`, document.baseURI).href;
  if (video.src === url) return;
  video.src = url;
  video.poster = new URL(`assets/${poster}?v=${edition}`, document.baseURI).href;
  fallback.href = url;
  error.hidden = Boolean(stage);
  video.load();
  stage?.showPoster(video.poster);
  if (stage && !reducedMotion.matches) video.play().catch(() => {});
}

function applyMotionPreference() {
  video.autoplay = Boolean(stage) && !reducedMotion.matches;
  if (!stage || reducedMotion.matches) video.pause();
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
video.addEventListener('loadeddata', () => {
  error.hidden = Boolean(stage);
});
video.addEventListener('timeupdate', () => {
  if (qualityChecked || portrait.matches || useHd || video.currentTime < 3) return;
  const quality = video.getVideoPlaybackQuality?.();
  if (!quality || quality.totalVideoFrames <= 60) return;
  qualityChecked = true;
  if (quality.droppedVideoFrames / quality.totalVideoFrames > .15) {
    useHd = true;
    selectFilm();
  }
});
function togglePlayback() {
  if (video.paused) video.play().catch(() => {});
  else video.pause();
}

function updatePlaybackLabel() {
  canvas.setAttribute('aria-label', video.paused ?
    'Продолжить анонс Audite' : 'Поставить анонс Audite на паузу');
}

canvas.addEventListener('click', togglePlayback);
canvas.addEventListener('keydown', event => {
  if (event.code === 'Space' || event.code === 'Enter') {
    event.preventDefault();
    togglePlayback();
  }
});
video.addEventListener('play', updatePlaybackLabel);
video.addEventListener('pause', updatePlaybackLabel);
soundToggle.addEventListener('click', () => {
  video.muted = !video.muted;
  soundToggle.classList.toggle('is-muted', video.muted);
  soundToggle.setAttribute('aria-label', video.muted ? 'Включить звук' : 'Выключить звук');
  soundToggle.title = video.muted ? 'Включить звук' : 'Выключить звук';
  if (video.paused) video.play().catch(() => {});
});
portrait.addEventListener('change', selectFilm);
reducedMotion.addEventListener('change', applyMotionPreference);
selectFilm();
applyMotionPreference();
updatePlaybackLabel();
