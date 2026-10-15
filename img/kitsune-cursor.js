(function () {
  var fine = matchMedia('(pointer: fine)');
  var reduced = matchMedia('(prefers-reduced-motion: reduce)');
  var root = document.documentElement;
  var timers = [];
  ['press', 'hop', 'happy'].forEach(function (frame) {
    var image = new Image();
    image.src = '/img/kitsune-cursor-' + frame + '.svg';
  });
  function reset() {
    timers.forEach(clearTimeout);
    timers = [];
    root.style.removeProperty('--kitsune-cursor');
  }
  function frame(name) {
    root.style.setProperty('--kitsune-cursor', 'url("/img/kitsune-cursor-' + name + '.svg")');
  }
  document.addEventListener('pointerdown', function (event) {
    if (!fine.matches || event.pointerType !== 'mouse' || event.button !== 0) return;
    reset();
    if (reduced.matches) {
      frame('happy');
    } else {
      frame('press');
      timers.push(setTimeout(function () { frame('hop'); }, 85));
      timers.push(setTimeout(function () { frame('happy'); }, 180));
    }
    timers.push(setTimeout(reset, 340));
  }, { passive: true });
  window.addEventListener('blur', reset);
  document.addEventListener('visibilitychange', reset);
})();
