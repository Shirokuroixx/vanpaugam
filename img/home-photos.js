(function () {
  var gallery = document.querySelector('.photo-slideshow');
  if (!gallery) return;
  var photos = Array.from(gallery.querySelectorAll('.photo-slide'));
  var pause = gallery.querySelector('[data-photo="pause"]');
  var reduced = matchMedia('(prefers-reduced-motion: reduce)');
  var index = 0, timer, paused = reduced.matches;
  function stop() { clearInterval(timer); }
  function show(next) {
    index = (next + photos.length) % photos.length;
    photos.forEach(function (photo, i) {
      photo.classList.toggle('is-current', i === index);
      photo.setAttribute('aria-hidden', String(i !== index));
    });
    gallery.querySelector('.photo-caption').textContent = photos[index].dataset.caption;
    gallery.querySelector('.photo-count').textContent = (index + 1) + ' / ' + photos.length;
  }
  function start() {
    stop();
    if (!paused && !reduced.matches && !document.hidden && !gallery.matches(':hover') && !gallery.contains(document.activeElement)) {
      timer = setInterval(function () { show(index + 1); }, 6500);
    }
  }
  function label() {
    pause.textContent = paused ? 'Play' : 'Pause';
    pause.setAttribute('aria-label', (paused ? 'Play' : 'Pause') + ' photo slideshow');
    pause.hidden = reduced.matches;
  }
  gallery.querySelector('[data-photo="prev"]').addEventListener('click', function () { show(index - 1); start(); });
  gallery.querySelector('[data-photo="next"]').addEventListener('click', function () { show(index + 1); start(); });
  pause.addEventListener('click', function () { paused = !paused; label(); start(); });
  gallery.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); show(index + (event.key === 'ArrowLeft' ? -1 : 1)); start();
    }
  });
  gallery.addEventListener('mouseenter', stop);
  gallery.addEventListener('mouseleave', start);
  gallery.addEventListener('focusin', stop);
  gallery.addEventListener('focusout', function () { setTimeout(start, 0); });
  document.addEventListener('visibilitychange', start);
  reduced.addEventListener('change', function () { paused = reduced.matches; label(); start(); });
  label(); start();
})();
