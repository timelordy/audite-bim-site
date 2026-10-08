const video = document.querySelector('#film');
const error = document.querySelector('#media-error');
const fallback = document.querySelector('#download-fallback');
const soundToggle = document.querySelector('#sound-toggle');
const portrait = window.matchMedia('(max-aspect-ratio: 1/1)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const edition = '20261008-v4';
let useHd = false;
let qualityChecked = false;
const colorPixel = document.createElement('canvas');
colorPixel.width = colorPixel.height = 1;
const colorReader = colorPixel.getContext('2d', { willReadFrequently: true });
let pixelAccess = Boolean(colorReader);
let sampledScene = '';
let fieldColor = '';

function sceneColor(time) {
  if (time < 2.5 || time >= 13) return '#284cff';
  if (time < 3.5 || (time >= 6 && time < 10.5)) return '#dfff00';
  if (time < 6) return '#6d31f4';
  return '#1741e8';
}

function matchFilmBackground(time = video.currentTime) {
  if (video.readyState < 2) return;
  let color = sceneColor(time);
  const scene = `${video.currentSrc}:${color}`;
  if (scene === sampledScene) return;
  sampledScene = scene;
  // The studio color is constant within a scene; sample only at its cut.
  if (pixelAccess) {
    try {
      colorReader.drawImage(video, 0, 0, 2, 2, 0, 0, 1, 1);
      const [red, green, blue] = colorReader.getImageData(0, 0, 1, 1).data;
      color = `rgb(${red}, ${green}, ${blue})`;
    } catch {
      // Browser pixel restrictions use the known palette of this film.
      pixelAccess = false;
    }
  }
  if (color === fieldColor) return;
  fieldColor = color;
  document.documentElement.style.setProperty('--film-color', color);
}

function followFilmFrame(now, frame) {
  matchFilmBackground(frame?.mediaTime);
  if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(followFilmFrame);
  else requestAnimationFrame(followFilmFrame);
}

function selectFilm() {
  document.documentElement.style.setProperty('--film-aspect', portrait.matches ? 9 / 16 : 16 / 9);
  const file = portrait.matches ? 'audite-portrait.mp4' :
    (useHd ? 'audite-landscape-hd.mp4' : 'audite-landscape.mp4');
  const poster = portrait.matches ? 'audite-portrait-poster.png' : 'audite-landscape-poster.png';
  const url = new URL(`assets/${file}?v=${edition}`, document.baseURI).href;
  if (video.src === url) return;
  video.src = url;
  fieldColor = '#284cff';
  document.documentElement.style.setProperty('--film-color', fieldColor);
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
video.addEventListener('loadeddata', () => {
  error.hidden = true;
  matchFilmBackground();
});
video.addEventListener('seeked', () => matchFilmBackground());
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
followFilmFrame();
