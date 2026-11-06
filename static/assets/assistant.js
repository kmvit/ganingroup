(() => {
  const script = document.currentScript;
  const api = (script?.dataset.api || '/assistant').replace(/\/$/, '');
  const site = script?.dataset.site || 'ganin';
  const policy = site === 'sd2' ? `${location.origin}/soglasie/` : `${location.origin}/consent/`;
  // Chat questions are answered without storing a dialogue; applications use their own consent form.
  const recordsChat = false;
  const chatConsent = new URL('/assistant/consent/', new URL(api, location.origin)).href;
  const sessionKey = `gg-assistant-session-v2-${site}`;
  let sessionId = '';
  if (recordsChat) {
    try { sessionId = sessionStorage.getItem(sessionKey) || ''; } catch (_) {}
  }
  const root = document.createElement('div');
  root.className = 'gg-assistant';
  root.dataset.site = site;
  root.innerHTML = `
    <button class="gg-assistant__toggle" type="button" aria-expanded="false" aria-controls="gg-assistant-panel">Спросить ассистента</button>
    <section class="gg-assistant__panel" id="gg-assistant-panel" aria-label="Ассистент сайта">
      <div class="gg-assistant__head"><span>${site === 'ganin' ? 'Ассистент Ганин групп' : 'Помощь по продукции и услугам'}</span><button class="gg-assistant__close" type="button" aria-label="Закрыть">×</button></div>
      <div class="gg-assistant__suggestions"><span class="gg-assistant__suggestions-label">Можно спросить</span><div class="gg-assistant__suggestions-list"></div></div>
      <div class="gg-assistant__messages" role="log" aria-live="polite"></div>
      <div class="gg-assistant__actions"><button class="gg-assistant__lead-toggle" type="button">Оставить заявку →</button></div>
      ${recordsChat ? `<label class="gg-assistant__agree gg-assistant__chat-consent"><input type="checkbox"><span>Согласен на запись диалога и обработку сообщения для ответа. <a href="${chatConsent}" target="_blank" rel="noopener">Условия обработки</a></span></label>` : ''}
      <form class="gg-assistant__form"><input class="gg-assistant__input" maxlength="1200" aria-label="Ваш вопрос" placeholder="Напишите ваш вопрос" required><button class="gg-assistant__send" type="submit">Отправить</button></form>
      <form class="gg-assistant__lead"><input class="gg-assistant__input" name="name" maxlength="120" placeholder="Как к вам обращаться *" required><input class="gg-assistant__input" name="phone" type="tel" maxlength="40" placeholder="Телефон *" required><textarea class="gg-assistant__input" name="details" maxlength="1500" rows="2" placeholder="Что нужно, объём, адрес и сроки"></textarea><input name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true"><label class="gg-assistant__agree"><input name="agree" type="checkbox" required><span>Согласен на обработку персональных данных. <a href="${policy}" target="_blank" rel="noopener">Текст согласия</a></span></label><button class="gg-assistant__submit" type="submit">Отправить заявку</button></form>
      <div class="gg-assistant__status" role="status"></div>
    </section>`;
  document.body.append(root);
  const $ = selector => root.querySelector(selector);
  const toggle = $('.gg-assistant__toggle');
  const messages = $('.gg-assistant__messages');
  const status = $('.gg-assistant__status');
  const chatConsentField = $('.gg-assistant__chat-consent');
  const chatConsentInput = chatConsentField?.querySelector('input');
  let previousQuestion = '';
  const path = location.pathname.toLowerCase();
  const questions = (() => {
    if (site === 'sd2') {
      if (path.startsWith('/dostavka/')) return ['Куда доставляете бетон?', 'Какие объёмы миксеров?', 'Есть ли бетононасосы?'];
      if (path.includes('zhelezobeton') || path.includes('zhb')) return ['Какие ЖБИ производите?', 'Есть ли блоки ФБС?', 'Как получить расчёт?'];
      if (path.includes('asfalt')) return ['Какие асфальтовые смеси есть?', 'Как заказать асфальт?', 'Куда доставляете?'];
      if (path.includes('karer')) return ['Какие инертные материалы есть?', 'Как заказать щебень?', 'Есть ли доставка?'];
      if (path.includes('kontakty')) return ['Где находится завод?', 'Как связаться с отделом продаж?', 'Какой график работы?'];
      return ['Какой бетон производите?', 'Куда доставляете?', 'Как получить расчёт?'];
    }
    if (path.startsWith('/uslugi/logistika/')) return ['Куда доставляете?', 'Какая техника есть?', 'Есть бетононасосы?'];
    if (path.startsWith('/uslugi/raschet-opalubki/')) return ['Как рассчитывают опалубку?', 'Какие данные нужны для расчёта?', 'Как запросить предложение?'];
    if (path.startsWith('/uslugi/shef-montazh/')) return ['Что входит в шеф-монтаж?', 'Где доступен шеф-монтаж?', 'Как заказать услугу?'];
    if (path.startsWith('/uslugi/laboratoriya/')) return ['Какие услуги у лаборатории?', 'Выдаёте паспорт качества?', 'Как обратиться?'];
    if (path.startsWith('/produkciya/mineralnyy-poroshok/')) return ['Какие марки порошка есть?', 'Где применяют порошок?', 'Как заказать?'];
    if (path.startsWith('/produkciya/cement/')) return ['Какой цемент поставляете?', 'Есть ли доставка цемента?', 'Как заказать?'];
    if (path.startsWith('/produkciya/')) {
      const product = document.querySelector('h1')?.textContent.trim().replace(/\s+/g, ' ').slice(0, 60) || 'продукции';
      return [`Какие характеристики у ${product}?`, `Как заказать ${product}?`, 'Есть ли доставка?'];
    }
    if (path.startsWith('/kariera/')) return ['Есть ли вакансии?', 'Как откликнуться?', 'Где находится завод?'];
    if (path.startsWith('/kontakty/')) return ['Как связаться с отделом продаж?', 'Где находится завод?', 'Какой график работы?'];
    if (path.startsWith('/obekty/')) return ['На какие объекты вы поставляли продукцию?', 'С какими задачами помогаете?', 'Как запросить предложение?'];
    if (path.startsWith('/resheniya/')) return ['Что можете поставить на объект?', 'Есть ли доставка и насосы?', 'Как получить ТКП?'];
    return ['Что производите?', 'Куда доставляете?', 'Как получить расчёт?'];
  })();
  for (const question of questions) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = question;
    button.addEventListener('click', () => {
      const input = $('.gg-assistant__form .gg-assistant__input');
      input.value = question;
      if (chatConsentInput && !sessionId && !chatConsentInput.checked) {
        status.textContent = 'Отметьте согласие и нажмите «Отправить».';
        chatConsentInput.focus();
        return;
      }
      $('.gg-assistant__form').requestSubmit();
    });
    $('.gg-assistant__suggestions-list').append(button);
  }
  if (sessionId) chatConsentField.hidden = true;
  function open(value) {
    root.classList.toggle('is-open', value);
    toggle.setAttribute('aria-expanded', String(value));
    if (value) $('.gg-assistant__input').focus();
  }
  function addMessage(text, user = false, sources = []) {
    const box = document.createElement('div');
    box.className = 'gg-assistant__message' + (user ? ' gg-assistant__message--user' : '');
    if (user) {
      box.textContent = text;
    } else {
      const allowedUrls = new Set(sources.map(source => source.url));
      let end = 0;
      for (const match of text.matchAll(/\[((?:\\[\\\[\]]|[^\\\[\]\n])+)\]\(([^\s)]*)\)/g)) {
        const [token, label, url] = match;
        box.append(text.slice(end, match.index));
        const title = label.replace(/\\([\\\[\]])/g, '$1');
        if (url.startsWith('https://') && allowedUrls.has(url)) {
          const link = document.createElement('a');
          link.href = url;
          link.target = '_blank';
          link.rel = 'noopener';
          link.textContent = title;
          box.append(link);
        } else {
          box.append(title);
        }
        end = match.index + token.length;
      }
      box.append(text.slice(end));
    }
    messages.append(box);
    messages.scrollTop = messages.scrollHeight;
  }
  addMessage('Здравствуйте! Чем могу помочь? Напишите свой вопрос или выберите подсказку.');
  if (site === 'ganin') messages.append($('.gg-assistant__suggestions'));
  toggle.addEventListener('click', () => open(!root.classList.contains('is-open')));
  $('.gg-assistant__close').addEventListener('click', () => open(false));
  $('.gg-assistant__lead-toggle').addEventListener('click', () => {
    root.classList.toggle('is-lead');
    $('.gg-assistant__lead-toggle').textContent = root.classList.contains('is-lead') ? '← Вернуться к вопросам' : 'Оставить заявку →';
    status.textContent = '';
  });
  $('.gg-assistant__form').addEventListener('submit', async event => {
    event.preventDefault();
    const input = $('.gg-assistant__form .gg-assistant__input');
    const question = input.value.trim();
    if (!question) return;
    if (chatConsentInput && !sessionId && !chatConsentInput.checked) {
      status.textContent = 'Сначала подтвердите согласие на запись диалога.';
      return;
    }
    input.value = '';
    $('.gg-assistant__suggestions').hidden = true;
    addMessage(question, true);
    status.textContent = 'Ищу ответ…';
    const button = $('.gg-assistant__send');
    button.disabled = true;
    try {
      const payload = {message: question};
      if (recordsChat) {
        payload.session_id = sessionId || undefined;
        payload.consent = !sessionId && chatConsentInput.checked;
      } else if (previousQuestion) {
        payload.previous_question = previousQuestion;
      }
      const response = await fetch(`${api}/chat/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Assistant-Site': site}, body: JSON.stringify(payload)});
      const data = await response.json();
      if (recordsChat && data.session_id) {
        sessionId = data.session_id;
        try { sessionStorage.setItem(sessionKey, sessionId); } catch (_) {}
        chatConsentField.hidden = true;
      }
      if (!response.ok) throw new Error(data.error || 'Ошибка связи');
      addMessage(data.answer, false, data.sources || []);
      if (!recordsChat) previousQuestion = data.sources?.length ? question : '';
      status.textContent = '';
    } catch (error) { status.textContent = error.message || 'Не удалось ответить. Попробуйте позже.'; }
    finally { button.disabled = false; }
  });
  $('.gg-assistant__lead').addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = $('.gg-assistant__submit');
    button.disabled = true;
    status.textContent = 'Отправляю заявку…';
    const data = Object.fromEntries(new FormData(form));
    data.agree = !!form.elements.agree.checked;
    data.page = location.href;
    try {
      const response = await fetch(`${api}/lead/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Assistant-Site': site}, body: JSON.stringify(data)});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Ошибка отправки');
      form.reset();
      root.classList.remove('is-lead');
      $('.gg-assistant__lead-toggle').textContent = 'Оставить заявку →';
      addMessage(result.message);
      status.textContent = '';
    } catch (error) { status.textContent = error.message || 'Не удалось отправить заявку.'; }
    finally { button.disabled = false; }
  });
})();
