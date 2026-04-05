function normalizeText(text) {
  return (text || '').trim().toLowerCase();
}

function readPage() {
  const raw = document.body?.innerText || '';
  const content = raw.replace(/\s+/g, ' ').trim();
  return {
    ok: true,
    action: 'read_page',
    content: content.slice(0, 7000),
  };
}

function clickByText(targetText) {
  const needle = normalizeText(targetText);
  if (!needle) {
    return { ok: false, error: 'Missing text to click' };
  }

  const candidates = Array.from(
    document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]'),
  );

  const found = candidates.find((element) =>
    normalizeText(element.innerText || element.value || '').includes(needle),
  );

  if (!found) {
    return { ok: false, error: `Element with text not found: ${targetText}` };
  }

  found.click();
  return { ok: true, action: 'click_text', text: targetText };
}

function inputText(selector, value) {
  const text = value ?? '';
  let element = null;

  if (selector) {
    element = document.querySelector(selector);
  }

  if (!element) {
    element = document.querySelector('input:not([type="hidden"]), textarea, [contenteditable="true"]');
  }

  if (!element) {
    return { ok: false, error: 'Input element not found' };
  }

  if ('value' in element) {
    element.focus();
    element.value = text;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  } else {
    element.textContent = text;
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }

  return { ok: true, action: 'input_text', value: text };
}

function scrollDown(amount = 600) {
  window.scrollBy({ top: amount, behavior: 'smooth' });
  return { ok: true, action: 'scroll_down', amount };
}

function performAction(action) {
  const type = action?.type;

  if (!type) {
    return { ok: false, error: 'Action type is required' };
  }

  switch (type) {
    case 'read_page':
      return readPage();

    case 'click_text':
      return clickByText(action.text || action.payload?.text || action.value);

    case 'input_text':
      return inputText(
        action.selector || action.payload?.selector,
        action.value || action.payload?.value || '',
      );

    case 'scroll_down':
      return scrollDown(action.amount || action.payload?.amount || 600);

    default:
      return { ok: false, error: `Unsupported action type: ${type}` };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== 'perform_action') {
    return false;
  }

  try {
    const result = performAction(message.action);
    sendResponse(result);
  } catch (error) {
    sendResponse({
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }

  return true;
});
