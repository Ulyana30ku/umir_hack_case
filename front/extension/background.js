async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0] || null;
}

async function ensurePageContext(tabId) {
  await chrome.scripting.executeScript({
    target: { tabId },
    func: () => true,
  });
}

const appSchemeToWebUrl = {
  'app://youtube': 'https://www.youtube.com',
  'app://spotify': 'https://open.spotify.com',
  'app://netflix': 'https://www.netflix.com',
  'app://telegram': 'https://web.telegram.org',
  'app://instagram': 'https://www.instagram.com',
  'app://tiktok': 'https://www.tiktok.com',
  'app://twitter': 'https://twitter.com',
  'app://facebook': 'https://www.facebook.com',
  'app://whatsapp': 'https://web.whatsapp.com',
  'app://discord': 'https://discord.com/app',
  'app://slack': 'https://app.slack.com',
  'app://reddit': 'https://www.reddit.com',
  'app://linkedin': 'https://www.linkedin.com',
  'app://pinterest': 'https://www.pinterest.com',
  'app://zoom': 'https://zoom.us',
  'app://skype': 'https://web.skype.com',
  'app://teams': 'https://teams.microsoft.com',
  'app://dropbox': 'https://www.dropbox.com',
  'app://trello': 'https://trello.com',
  'app://asana': 'https://app.asana.com',
  'app://vk': 'https://vk.com',
  'app://viber': 'viber://',
  'app://messenger': 'https://www.messenger.com',
};

async function handleAppScheme(appScheme) {
  if (appScheme.startsWith('app://')) {
    const appName = appScheme.replace('app://', '');
    const nativeSchemes = [
      `${appName}://`,
      `${appName}://open`,
      `com.${appName}.app`,
    ];
    
    for (const scheme of nativeSchemes) {
      try {
        const openedTab = await chrome.tabs.create({ url: scheme, active: true });
        return { ok: true, type: 'open_app', appScheme, nextTab: openedTab };
      } catch (e) {
      }
    }
    
    const webUrl = appSchemeToWebUrl[appScheme];
    if (webUrl) {
      const openedTab = await chrome.tabs.create({ url: webUrl, active: true });
      return { ok: true, type: 'open_url', url: webUrl, fallback: true, nextTab: openedTab };
    }
  }
  
  return null;
}

async function handleAction(tab, action) {
  if (!tab || !tab.id) {
    return { ok: false, error: 'No active tab', nextTab: tab };
  }

  if (action.type === 'open_url') {
    const url = action.url || action.payload?.url || action.value;
    if (!url) {
      return { ok: false, error: 'Missing url', nextTab: tab };
    }

    if (url.startsWith('app://')) {
      const appResult = await handleAppScheme(url);
      if (appResult) {
        return appResult;
      }
    }

    const openedTab = await chrome.tabs.create({ url, active: true });
    return { ok: true, type: 'open_url', url, nextTab: openedTab };
  }

  await ensurePageContext(tab.id);

  return new Promise((resolve) => {
    chrome.tabs.sendMessage(
      tab.id,
      { type: 'perform_action', action },
      (response) => {
        if (chrome.runtime.lastError) {
          resolve({ ok: false, error: chrome.runtime.lastError.message, nextTab: tab });
          return;
        }
        resolve({ ...(response || { ok: false, error: 'No response from content script' }), nextTab: tab });
      },
    );
  });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== 'execute_actions') {
    return false;
  }

  (async () => {
    let tab = await getActiveTab();
    const actions = Array.isArray(message.actions) ? message.actions : [];
    const results = [];

    for (const action of actions) {
      const result = await handleAction(tab, action);
      if (result?.nextTab?.id) {
        tab = result.nextTab;
      }
      results.push({ action, result });
    }

    sendResponse({ ok: true, results });
  })();

  return true;
});
