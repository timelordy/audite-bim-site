// Snapshot once, compose offscreen, and present the whole viewport together.
export function createFilmStage(video, canvas, onFailure) {
  const options = { alpha: false, colorSpace: 'srgb', willReadFrequently: false };
  const context = canvas.getContext('2d', options);
  const buffer = document.createElement('canvas');
  const composition = buffer.getContext('2d', options);
  if (!context || !composition || typeof createImageBitmap !== 'function') return null;
  let poster = null;
  let frame = null;
  let frameSource = '';
  let capturing = false;
  let captureQueued = false;
  let failed = false;
  let resolveReady;
  const ready = new Promise(resolve => { resolveReady = resolve; });

  function present(snapshot) {
    const scale = Math.min(buffer.width / snapshot.width, buffer.height / snapshot.height);
    const width = Math.round(snapshot.width * scale);
    const height = Math.round(snapshot.height * scale);
    const x = Math.floor((buffer.width - width) / 2);
    const y = Math.floor((buffer.height - height) / 2);
    composition.drawImage(snapshot, 2, 2, 1, 1, 0, 0, buffer.width, buffer.height);
    composition.drawImage(snapshot, x, y, width, height);
    context.drawImage(buffer, 0, 0);
    resolveReady(true);
  }

  function retain(snapshot, source) {
    const previous = frame;
    frame = snapshot;
    frameSource = source;
    present(frame);
    previous?.close();
  }

  async function captureVideo() {
    if (failed || video.readyState < 2) return;
    if (capturing) {
      captureQueued = true;
      return;
    }
    capturing = true;
    const source = video.src;
    try {
      // A live video can advance between drawImage calls. This bitmap cannot.
      const snapshot = await createImageBitmap(video);
      if (source !== video.src) snapshot.close();
      else retain(snapshot, source);
    } catch {
      if (source !== video.src || video.readyState < 2) return;
      failed = true;
      resolveReady(false);
      onFailure();
    } finally {
      capturing = false;
      if (captureQueued) {
        captureQueued = false;
        captureVideo();
      }
    }
  }

  function resize() {
    const density = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = buffer.width = Math.max(4, Math.round(innerWidth * density));
    canvas.height = buffer.height = Math.max(4, Math.round(innerHeight * density));
    context.imageSmoothingQuality = composition.imageSmoothingQuality = 'high';
    if (frame) present(frame);
    else {
      context.fillStyle = '#284cff';
      context.fillRect(0, 0, canvas.width, canvas.height);
    }
  }

  function showPoster(url) {
    const next = new Image();
    poster = next;
    return new Promise(resolve => {
      next.onload = async () => {
        try {
          const snapshot = await createImageBitmap(next);
          if (poster !== next || (frameSource === video.src && video.readyState >= 2)) {
            snapshot.close();
          } else retain(snapshot, url);
          resolve(true);
        } catch {
          resolve(false);
        }
      };
      next.onerror = () => resolve(false);
      next.src = url;
    });
  }

  function deliveredFrame() {
    captureVideo();
    video.requestVideoFrameCallback(deliveredFrame);
  }

  function fallbackFrame() {
    if (!video.paused) captureVideo();
    requestAnimationFrame(fallbackFrame);
  }

  window.addEventListener('resize', resize);
  video.addEventListener('loadeddata', captureVideo);
  video.addEventListener('seeked', captureVideo);
  video.addEventListener('pause', captureVideo);
  resize();
  if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(deliveredFrame);
  else requestAnimationFrame(fallbackFrame);
  return { showPoster, ready };
}
