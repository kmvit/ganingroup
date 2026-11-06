(() => {
  const script = document.currentScript;
  const metrika = script?.dataset.metrika || '';
  const google = script?.dataset.google || '';
  const policy = script?.dataset.policy || '/policy/';
  const key = 'site-analytics-consent-v1';
  let choice = null;
  try { choice = localStorage.getItem(key); } catch (_) {}

  function startAnalytics() {
    if (metrika && /^\d+$/.test(metrika)) {
      window.ym = window.ym || function () { (window.ym.a = window.ym.a || []).push(arguments); };
      const tag = document.createElement('script');
      tag.async = true;
      tag.src = 'https://mc.yandex.ru/metrika/tag.js';
      document.head.append(tag);
      window.ym(Number(metrika), 'init', {clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: false});
    }
    if (google && /^G-[A-Z0-9]+$/.test(google)) {
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', google);
      const tag = document.createElement('script');
      tag.async = true;
      tag.src = `https://www.googletagmanager.com/gtag/js?id=${google}`;
      document.head.append(tag);
    }
  }

  if (choice === 'yes') { startAnalytics(); return; }
  if (choice === 'no') return;
  const banner = document.createElement('aside');
  banner.className = 'site-privacy-choice';
  banner.setAttribute('aria-label', 'Использование cookie');
  const copy = document.createElement('div');
  copy.className = 'site-privacy-choice__copy';
  const label = document.createElement('span');
  label.className = 'site-privacy-choice__label';
  label.textContent = 'Cookie на сайте';
  const message = document.createElement('p');
  message.append('Мы используем необходимые cookie для работы сайта. Аналитические cookie включим только с вашего согласия. ');
  const link = document.createElement('a');
  link.href = policy;
  link.textContent = 'Политика обработки данных';
  message.append(link);
  copy.append(label, message);
  const actions = document.createElement('div');
  actions.className = 'site-privacy-choice__actions';
  for (const [label, value] of [['Принять', 'yes'], ['Только необходимые', 'no']]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.choice = value;
    button.textContent = label;
    button.addEventListener('click', () => {
      try { localStorage.setItem(key, value); } catch (_) {}
      banner.remove();
      if (value === 'yes') startAnalytics();
    });
    actions.append(button);
  }
  banner.append(copy, actions);
  document.body.append(banner);
  const syncBannerHeight = () => document.documentElement.style.setProperty(
    '--privacy-banner-height', `${Math.ceil(banner.getBoundingClientRect().height) + 12}px`);
  syncBannerHeight();
  const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(syncBannerHeight);
  observer?.observe(banner);
  window.addEventListener('resize', syncBannerHeight);
  banner.addEventListener('click', event => {
    if (event.target.closest('button[data-choice]')) {
      observer?.disconnect();
      window.removeEventListener('resize', syncBannerHeight);
      document.documentElement.style.removeProperty('--privacy-banner-height');
    }
  });
})();
