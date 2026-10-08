// Paint the frame and its flat extension in one color space.
export function createFilmStage(video, canvas) {
  const context = canvas.getContext('2d', {
    alpha: false, colorSpace: 'srgb', willReadFrequently: false,
  });
  if (!context) return null;
  let poster = null;
  let lastPaint = 0;
  context.imageSmoothingQuality = 'high';

  function paint(source) {
    const width = source === video ? video.videoWidth : source.naturalWidth;
    const height = source === video ? video.videoHeight : source.naturalHeight;
    if (!width || !height) return;
    const scale = Math.min(canvas.width / width, canvas.height / height);
    const drawnWidth = Math.round(width * scale);
    const drawnHeight = Math.round(height * scale);
    const x = Math.floor((canvas.width - drawnWidth) / 2);
    const y = Math.floor((canvas.height - drawnHeight) / 2);
    // Extend a flat corner pixel from this exact frame, then paint the film.
    // Both draws share the source texture and color conversion, including cuts.
    context.drawImage(source, 2, 2, 1, 1, 0, 0, canvas.width, canvas.height);
    context.drawImage(source, x, y, drawnWidth, drawnHeight);
  }

  function paintVideo() {
    if (video.readyState < 2) return;
    paint(video);
  }

  function resize() {
    const density = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(4, Math.round(window.innerWidth * density));
    canvas.height = Math.max(4, Math.round(window.innerHeight * density));
    context.imageSmoothingQuality = 'high';
    context.fillStyle = '#284cff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    if (video.readyState >= 2) paintVideo();
    else if (poster?.complete && poster.naturalWidth) paint(poster);
  }

  function showPoster(url) {
    const next = new Image();
    poster = next;
    next.onload = () => {
      if (poster === next && video.readyState < 2) paint(next);
    };
    next.src = url;
  }

  function animate(now) {
    if (!video.paused && now - lastPaint >= 1000 / 30 - 1) {
      paintVideo();
      lastPaint = now;
    }
    requestAnimationFrame(animate);
  }

  window.addEventListener('resize', resize);
  video.addEventListener('loadeddata', paintVideo);
  video.addEventListener('seeked', paintVideo);
  video.addEventListener('pause', paintVideo);
  resize();
  requestAnimationFrame(animate);
  return { showPoster };
}
