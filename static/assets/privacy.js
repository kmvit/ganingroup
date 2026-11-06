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
  const banner = document.createElement('div');
  banner.className = 'site-privacy-choice';
  banner.setAttribute('role', 'dialog');
  banner.setAttribute('aria-label', 'Настройки аналитики');
  const text = document.createElement('span');
  text.textContent = 'Разрешить аналитику посещений? Сайт работает и без неё. ';
  const link = document.createElement('a');
  link.href = policy;
  link.textContent = 'Политика обработки данных';
  banner.append(text, link);
  for (const [label, value] of [['Разрешить', 'yes'], ['Без аналитики', 'no']]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', () => {
      try { localStorage.setItem(key, value); } catch (_) {}
      banner.remove();
      if (value === 'yes') startAnalytics();
    });
    banner.append(button);
  }
  document.body.append(banner);
})();
