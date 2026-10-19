// Newsletter sticky bar: shows after scrolling, hides while another signup form is visible,
// dismissal remembered in localStorage (no cookies). Desktop/tablet only (>= 900px wide).
(function () {
  var bar = document.getElementById('nl-bar'); if (!bar) return;
  var KEY = 'eurogpu_nl_bar_dismissed';
  try { if (localStorage.getItem(KEY)) return; } catch (e) {}
  var forms = [].slice.call(document.querySelectorAll('.nl-form')).filter(function (f) { return !bar.contains(f); });
  var formVisible = false;
  if ('IntersectionObserver' in window) {
    var seen = new Set();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { en.isIntersecting ? seen.add(en.target) : seen.delete(en.target); });
      formVisible = seen.size > 0; update();
    });
    forms.forEach(function (f) { io.observe(f); });
  }
  function update() {
    var wide = window.matchMedia('(min-width: 900px)').matches;
    var scrolled = window.scrollY > window.innerHeight * 1.2;
    bar.hidden = !(wide && scrolled && !formVisible);
  }
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  bar.querySelector('.nl-close').addEventListener('click', function () {
    bar.hidden = true; try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
    window.removeEventListener('scroll', update);
  });
  bar.querySelector('form').addEventListener('submit', function () { try { localStorage.setItem(KEY, 'subscribed'); } catch (e) {} setTimeout(function () { bar.hidden = true; }, 300); });
  update();
})();
