/* AiYan — interactions: frosted nav, mobile drawer, scroll-reveal. */
(function () {
  'use strict';

  // ── Frosted nav: add shadow once the page scrolls past the top. ──────────
  var nav = document.querySelector('[data-nav]');
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ── Mobile drawer toggle. ────────────────────────────────────────────────
  var toggle = document.querySelector('[data-nav-toggle]');
  if (toggle && nav) {
    var setAria = function (open) { toggle.setAttribute('aria-expanded', open ? 'true' : 'false'); };
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      setAria(open);
    });
    nav.addEventListener('click', function (e) {
      if (e.target.matches('.nav__drawer-link')) {
        nav.classList.remove('is-open');
        setAria(false);
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        setAria(false);
      }
    });
  }

  // ── Scroll-reveal via IntersectionObserver, staggered by --i. ────────────
  var reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length) {
    if (!('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  // ── Footer category chips (optional, harmless if absent). ────────────────
  // Keep a simple year stamp in sync if present.
  var year = document.querySelector('[data-year]');
  if (year) { year.textContent = new Date().getFullYear(); }
})();
