const API_BASE = 'http://127.0.0.1:8000';
const STORAGE_KEY = 'ai_browser_assistant_session_id';

const messagesEl = document.getElementById('messages');
const formEl = document.getElementById('chatForm');
const inputEl = document.getElementById('messageInput');
const sendBtnEl = document.getElementById('sendBtn');
const newChatBtnEl = document.getElementById('newChatBtn');

let sessionId = null;
let messages = [];
let isSending = false;

async function createSession(title = 'Chrome Chat') {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error('Не удалось создать сессию');
  }

  const data = await response.json();
  sessionId = data.id;
  await chrome.storage.local.set({ [STORAGE_KEY]: sessionId });
  return sessionId;
}

function renderMessages() {
  messagesEl.innerHTML = '';

  if (!messages.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'Начните диалог: отправьте первую команду';
    messagesEl.appendChild(empty);
    return;
  }

  for (const msg of messages) {
    const item = document.createElement('div');
    const role = msg.role || 'assistant';
    item.className = `msg-${role}`;
    
    const content = document.createElement('div');
    content.textContent = msg.content;
    item.appendChild(content);
    
    if (msg.created_at) {
      const time = document.createElement('div');
      time.className = 'msg-time';
      const date = new Date(msg.created_at);
      time.textContent = date.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      item.appendChild(time);
    }
    
    messagesEl.appendChild(item);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setSendingState(flag) {
  isSending = flag;
  sendBtnEl.disabled = flag;
  inputEl.disabled = flag;
  sendBtnEl.textContent = flag ? '...' : 'Отправить';
}

async function ensureSession() {
  if (sessionId) {
    return sessionId;
  }

  const saved = await chrome.storage.local.get(STORAGE_KEY);
  if (saved && saved[STORAGE_KEY]) {
    sessionId = saved[STORAGE_KEY];
    const check = await fetch(`${API_BASE}/sessions/${sessionId}`);
    if (check.ok) {
      return sessionId;
    }

    sessionId = null;
    await chrome.storage.local.remove(STORAGE_KEY);
  }

  return createSession('Chrome Chat');
}

async function loadHistory() {
  try {
    const sid = await ensureSession();
    const response = await fetch(`${API_BASE}/sessions/${sid}/messages`);
    if (!response.ok) {
      if (response.status === 404) {
        sessionId = null;
        await chrome.storage.local.remove(STORAGE_KEY);
        const newSid = await createSession('Chrome Chat');
        const retry = await fetch(`${API_BASE}/sessions/${newSid}/messages`);
        if (!retry.ok) {
          throw new Error('Не удалось загрузить историю');
        }
        messages = await retry.json();
        renderMessages();
        return;
      }

      throw new Error('Не удалось загрузить историю');
    }
    messages = await response.json();
    renderMessages();
  } catch (error) {
    messages = [{ role: 'system', content: `Ошибка: ${error.message}` }];
    renderMessages();
  }
}

async function sendMessage(content) {
  if (isSending) return;

  const trimmed = content.trim();
  if (!trimmed) return;

  setSendingState(true);

  try {
    const sid = await ensureSession();

    const response = await fetch(`${API_BASE}/sessions/${sid}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: trimmed }),
    });

    if (!response.ok) {
      const text = await response.text();
      if (response.status === 404) {
        sessionId = null;
        await chrome.storage.local.remove(STORAGE_KEY);
        const newSid = await createSession('Chrome Chat');
        const retry = await fetch(`${API_BASE}/sessions/${newSid}/messages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: trimmed }),
        });

        if (!retry.ok) {
          const retryText = await retry.text();
          throw new Error(retryText || 'Ошибка backend');
        }

        const retryData = await retry.json();
        messages = retryData.recent_messages || [];
        renderMessages();

        if (retryData.actions && Array.isArray(retryData.actions) && retryData.actions.length > 0) {
          chrome.runtime.sendMessage({
            type: 'execute_actions',
            sessionId: newSid,
            actions: retryData.actions,
          });
        }

        return;
      }

      throw new Error(text || 'Ошибка backend');
    }

    const data = await response.json();
    messages = data.recent_messages || [];
    renderMessages();

    if (data.actions && Array.isArray(data.actions) && data.actions.length > 0) {
      chrome.runtime.sendMessage({
        type: 'execute_actions',
        sessionId: sid,
        actions: data.actions,
      });
    }
  } catch (error) {
    messages.push({ role: 'system', content: `Ошибка: ${error.message}` });
    renderMessages();
  } finally {
    setSendingState(false);
  }
}

async function createNewDialog() {
  try {
    const response = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Новый диалог' }),
    });

    if (!response.ok) {
      throw new Error('Не удалось создать диалог');
    }

    const data = await response.json();
    sessionId = data.id;
    messages = [];
    await chrome.storage.local.set({ [STORAGE_KEY]: sessionId });
    renderMessages();
    inputEl.focus();
  } catch (error) {
    messages = [{ role: 'system', content: `Ошибка: ${error.message}` }];
    renderMessages();
  }
}

formEl.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = inputEl.value;
  inputEl.value = '';
  await sendMessage(text);
});

inputEl.addEventListener('keydown', async (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    const text = inputEl.value;
    inputEl.value = '';
    await sendMessage(text);
  }
});

newChatBtnEl.addEventListener('click', createNewDialog);

loadHistory();
