(() => {
  const script = document.currentScript;
  const api = (script?.dataset.api || '/assistant').replace(/\/$/, '');
  const site = script?.dataset.site || 'ganin';
  const policy = site === 'sd2' ? `${location.origin}/soglasie/` : `${location.origin}/consent/`;
  const chatConsent = new URL('/assistant/consent/', api).href;
  const sessionKey = `gg-assistant-session-v2-${site}`;
  let sessionId = '';
  try { sessionId = sessionStorage.getItem(sessionKey) || ''; } catch (_) {}
  const root = document.createElement('div');
  root.className = 'gg-assistant';
  root.innerHTML = `
    <button class="gg-assistant__toggle" type="button" aria-expanded="false" aria-controls="gg-assistant-panel">Спросить ассистента</button>
    <section class="gg-assistant__panel" id="gg-assistant-panel" aria-label="Ассистент сайта">
      <div class="gg-assistant__head"><span>Помощь по продукции и услугам</span><button class="gg-assistant__close" type="button" aria-label="Закрыть">×</button></div>
      <div class="gg-assistant__messages" role="log" aria-live="polite"></div>
      <div class="gg-assistant__actions"><button class="gg-assistant__lead-toggle" type="button">Оставить заявку →</button></div>
      <label class="gg-assistant__agree gg-assistant__chat-consent"><input type="checkbox"><span>Согласен на запись диалога и обработку сообщения для ответа. <a href="${chatConsent}" target="_blank" rel="noopener">Условия обработки</a></span></label>
      <form class="gg-assistant__form"><input class="gg-assistant__input" maxlength="1200" aria-label="Ваш вопрос" placeholder="Напишите ваш вопрос" required><button class="gg-assistant__send" type="submit">Отправить</button></form>
      <form class="gg-assistant__lead"><input class="gg-assistant__input" name="name" maxlength="120" placeholder="Как к вам обращаться *" required><input class="gg-assistant__input" name="phone" type="tel" maxlength="40" placeholder="Телефон *" required><textarea class="gg-assistant__input" name="details" maxlength="1500" rows="2" placeholder="Что нужно, объём, адрес и сроки"></textarea><input name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true"><label class="gg-assistant__agree"><input name="agree" type="checkbox" required><span>Согласен на обработку персональных данных. <a href="${policy}" target="_blank" rel="noopener">Текст согласия</a></span></label><button class="gg-assistant__submit" type="submit">Отправить заявку</button></form>
      <div class="gg-assistant__status" role="status"></div>
    </section>`;
  document.body.append(root);
  const $ = selector => root.querySelector(selector);
  const toggle = $('.gg-assistant__toggle');
  const messages = $('.gg-assistant__messages');
  const status = $('.gg-assistant__status');
  const history = [];
  if (sessionId) $('.gg-assistant__chat-consent').hidden = true;
  function open(value) {
    root.classList.toggle('is-open', value);
    toggle.setAttribute('aria-expanded', String(value));
    if (value) $('.gg-assistant__input').focus();
  }
  function addMessage(text, user = false, sources = []) {
    const box = document.createElement('div');
    box.className = 'gg-assistant__message' + (user ? ' gg-assistant__message--user' : '');
    box.textContent = text;
    if (!user && sources.length) {
      const title = document.createElement('strong');
      title.textContent = '\nИсточники:';
      box.append(title);
      sources.slice(0, 3).forEach(source => {
        const link = document.createElement('a');
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = source.title;
        box.append(link);
      });
    }
    messages.append(box);
    messages.scrollTop = messages.scrollHeight;
  }
  addMessage('Здравствуйте! Спросите о продукции, доставке или услугах. Для расчёта заказа можно оставить заявку.');
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
    if (!sessionId && !$('.gg-assistant__chat-consent input').checked) {
      status.textContent = 'Сначала подтвердите согласие на запись диалога.';
      return;
    }
    input.value = '';
    addMessage(question, true);
    status.textContent = 'Ищу ответ…';
    const button = $('.gg-assistant__send');
    button.disabled = true;
    try {
      const response = await fetch(`${api}/chat/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Assistant-Site': site}, body: JSON.stringify({message: question, session_id: sessionId || undefined, consent: !sessionId && $('.gg-assistant__chat-consent input').checked})});
      const data = await response.json();
      if (data.session_id) {
        sessionId = data.session_id;
        try { sessionStorage.setItem(sessionKey, sessionId); } catch (_) {}
        $('.gg-assistant__chat-consent').hidden = true;
      }
      if (!response.ok) throw new Error(data.error || 'Ошибка связи');
      addMessage(data.answer, false, data.sources || []);
      history.push({role: 'user', content: question}, {role: 'assistant', content: data.answer});
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
