import { createFilmStage } from './film-stage.js?v=20261008-v8';

const video = document.querySelector('#film');
const canvas = document.querySelector('#film-stage');
const error = document.querySelector('#media-error');
const fallback = document.querySelector('#download-fallback');
const soundToggle = document.querySelector('#sound-toggle');
const portrait = window.matchMedia('(max-aspect-ratio: 1/1)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const edition = '20261008-v8';
let useHd = false;
let qualityChecked = false;
let sourceRun = 0;
let manuallyPaused = false;
let introPending = false;
let stageFailed = false;

function stageFailure() {
  stageFailed = true;
  video.pause();
  soundToggle.disabled = true;
  canvas.setAttribute('aria-disabled', 'true');
  error.hidden = false;
}

const stage = createFilmStage(video, canvas, stageFailure);
if (!stage) {
  canvas.hidden = true;
  soundToggle.disabled = true;
}

function bufferedForStart() {
  if (video.readyState < 3) return false;
  const required = Math.min(3, video.duration - video.currentTime);
  for (let i = 0; i < video.buffered.length; i++) {
    if (video.buffered.start(i) <= video.currentTime &&
        video.buffered.end(i) - video.currentTime >= required) return true;
  }
  return false;
}

function waitForBuffer(run) {
  return new Promise(resolve => {
    const events = ['progress', 'canplay', 'loadeddata', 'error', 'abort', 'loadstart'];
    const check = () => {
      const stale = run !== sourceRun || Boolean(video.error);
      if (!stale && !bufferedForStart()) return;
      events.forEach(event => video.removeEventListener(event, check));
      resolve(!stale);
    };
    events.forEach(event => video.addEventListener(event, check));
    check();
  });
}

async function startAfterIntro(run, posterReady = Promise.resolve(true)) {
  if (!stage || stageFailed || reducedMotion.matches) return;
  if (!await waitForBuffer(run)) return;
  await posterReady;
  if (!await stage.ready || run !== sourceRun) return;
  await new Promise(resolve => setTimeout(resolve, 1800));
  if (run !== sourceRun || manuallyPaused || reducedMotion.matches || stageFailed) return;
  introPending = false;
  video.play().catch(() => {});
}

function selectFilm() {
  const file = portrait.matches ? 'audite-portrait.mp4' :
    (useHd ? 'audite-landscape-hd.mp4' : 'audite-landscape.mp4');
  const poster = portrait.matches ? 'audite-portrait-poster.png' : 'audite-landscape-poster.png';
  const url = new URL(`assets/${file}?v=${edition}`, document.baseURI).href;
  if (video.src === url) return;
  const run = ++sourceRun;
  video.autoplay = false;
  video.src = url;
  video.poster = new URL(`assets/${poster}?v=${edition}`, document.baseURI).href;
  fallback.href = url;
  error.hidden = Boolean(stage);
  video.load();
  introPending = Boolean(stage) && !reducedMotion.matches;
  startAfterIntro(run, stage?.showPoster(video.poster));
}

function applyMotionPreference() {
  const run = ++sourceRun;
  if (!stage || reducedMotion.matches) {
    introPending = false;
    video.pause();
  } else {
    introPending = true;
    startAfterIntro(run);
  }
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
  error.hidden = Boolean(stage) && !stageFailed;
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
  if (!stage || stageFailed) return;
  manuallyPaused = !video.paused;
  introPending = false;
  if (video.paused) video.play().catch(() => {});
  else video.pause();
}

function updatePlaybackLabel() {
  canvas.setAttribute('aria-label', video.paused ?
    (video.currentTime === 0 ? 'Начать анонс Audite' : 'Продолжить анонс Audite') :
    'Поставить анонс Audite на паузу');
}

canvas.addEventListener('click', togglePlayback);
canvas.addEventListener('keydown', event => {
  if (event.code === 'Space' || event.code === 'Enter') {
    event.preventDefault();
    togglePlayback();
  }
});
video.addEventListener('play', () => {
  manuallyPaused = false;
  introPending = false;
  updatePlaybackLabel();
});
video.addEventListener('pause', updatePlaybackLabel);
soundToggle.addEventListener('click', () => {
  video.muted = !video.muted;
  soundToggle.classList.toggle('is-muted', video.muted);
  soundToggle.setAttribute('aria-label', video.muted ? 'Включить звук' : 'Выключить звук');
  soundToggle.title = video.muted ? 'Включить звук' : 'Выключить звук';
  if (video.paused && !introPending) video.play().catch(() => {});
});
portrait.addEventListener('change', selectFilm);
reducedMotion.addEventListener('change', applyMotionPreference);
selectFilm();
updatePlaybackLabel();
