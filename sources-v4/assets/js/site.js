/* La Cuisine de Jeanine — scripts (aucune dépendance externe) */
(function () {
  'use strict';

  /* ---- header : ombre au scroll + barre CTA mobile ---- */
  var header = document.querySelector('.site-header');
  var bar = document.getElementById('mobileBar');
  var devis = document.getElementById('devis');
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('scrolled', y > 8);
    if (bar) {
      var hide = false;
      if (devis) {
        var r = devis.getBoundingClientRect();
        hide = r.top < window.innerHeight && r.bottom > 0;
      }
      bar.classList.toggle('show', y > 500 && !hide);
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- menu mobile ---- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('nav');
  if (toggle && nav) {
    var iconMenu = toggle.innerHTML;
    var iconClose = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>';
    function setNav(open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open);
      toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
      toggle.innerHTML = open ? iconClose : iconMenu;
      document.body.style.overflow = open ? 'hidden' : '';
    }
    toggle.addEventListener('click', function () { setNav(!nav.classList.contains('open')); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) setNav(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setNav(false); });
  }

  /* ---- boutons qui pré-cochent un motif dans le formulaire ---- */
  document.querySelectorAll('[data-motif]').forEach(function (a) {
    a.addEventListener('click', function () {
      var box = document.querySelector('[data-motif-box="' + a.dataset.motif + '"]');
      if (box) box.checked = true;
    });
  });

  /* ---- formulaire de devis ---- */
  var form = document.getElementById('devisForm');
  if (!form) return;
  var ts = document.getElementById('f-ts');
  if (ts) ts.value = String(Date.now());
  var status = document.getElementById('formStatus');
  var btn = form.querySelector('button[type="submit"]');

  function show(kind, msg) {
    status.className = 'form-status ' + kind;
    status.textContent = msg;
  }
  // retour du formulaire sans JavaScript (?envoi=ok|erreur)
  var q = new URLSearchParams(location.search).get('envoi');
  if (q === 'ok') show('ok', 'Merci ! Votre demande est bien partie. On vous recontacte sous 24 h ouvrées.');
  if (q === 'erreur') show('err', "L'envoi a échoué. Écrivez-nous à contact@lacuisinedejeanine.fr.");

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var bad = null;
    ['f-nom', 'f-entreprise', 'f-email'].forEach(function (id) {
      var el = document.getElementById(id);
      var ok = el.value.trim() !== '' && (el.type !== 'email' || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim()));
      el.setAttribute('aria-invalid', ok ? 'false' : 'true');
      if (!ok && !bad) bad = el;
    });
    if (bad) {
      show('err', 'Merci de renseigner votre nom, votre entreprise et une adresse email valide.');
      bad.focus();
      return;
    }
    btn.disabled = true;
    var label = btn.innerHTML;
    btn.textContent = 'Envoi en cours…';

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'Accept': 'application/json' }
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        if (data && data.ok) {
          form.reset();
          show('ok', 'Merci ! Votre demande est bien partie. On vous recontacte sous 24 h ouvrées.');
        } else {
          show('err', (data && data.error) || "L'envoi a échoué. Écrivez-nous à contact@lacuisinedejeanine.fr.");
        }
      })
      .catch(function () {
        show('err', "L'envoi a échoué. Écrivez-nous à contact@lacuisinedejeanine.fr.");
      })
      .finally(function () { btn.disabled = false; btn.innerHTML = label; });
  });
})();

/* ---- v4 : un peu de vie (plats qui tournent au scroll, pictos qui apparaissent) ---- */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;
  // pictos et « Hmmm. » : petite apparition quand on arrive dessus
  var pops = document.querySelectorAll('.doodle, .hmmm');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('popped'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -12% 0px' });
  pops.forEach(function (el) { el.classList.add('pop-ready'); io.observe(el); });
  // plats détourés : rotation douce liée au défilement
  var spins = Array.prototype.slice.call(document.querySelectorAll('[data-spin]'));
  if (!spins.length) return;
  var base = spins.map(function (el) { return parseFloat(el.dataset.base || '0'); });
  var ticking = false;
  function draw() {
    var y = window.scrollY;
    spins.forEach(function (el, i) { el.style.transform = 'rotate(' + (base[i] + y * parseFloat(el.dataset.spin)) + 'deg)'; });
    ticking = false;
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(draw); } }, { passive: true });
  draw();
})();
