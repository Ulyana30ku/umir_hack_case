import { useState, useEffect } from 'react';
import SplashCursor from './components/SplashCursor.js';
import HeroArea from './components/HeroArea.js';
import SessionList from './components/SessionList.js';
import ChatMessages from './components/ChatMessages.js';
import ChatInput from './components/ChatInput.js';
import LogsPanel from './components/LogsPanel.js';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId);
    }
  }, [currentSessionId]);

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        if (data.length > 0 && !currentSessionId) {
          setCurrentSessionId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      });
      if (response.ok) {
        const newSession = await response.json();
        setSessions((prev) => [newSession, ...prev]);
        setCurrentSessionId(newSession.id);
        setMessages([]);
        setLogs([]);
      }
    } catch (err) {
      setError('Ошибка при создании сессии');
      console.error('Failed to create session:', err);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      setSessions((prev) => {
        const remainingSessions = prev.filter((session) => session.id !== sessionId);

        if (currentSessionId === sessionId) {
          const nextSessionId = remainingSessions.length > 0 ? remainingSessions[0].id : null;
          setCurrentSessionId(nextSessionId);
          setMessages([]);
          setLogs([]);
        }

        return remainingSessions;
      });
    } catch (err) {
      setError('Ошибка при удалении сессии');
      console.error('Failed to delete session:', err);
    }
  };

  const sendMessage = async (content) => {
    if (!currentSessionId) {
      setError('Выберите или создайте сессию');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Backend request failed');
      }

      const result = await response.json();
      setMessages(result.recent_messages || []);
      setLogs(result.logs || []);

      const actions = Array.isArray(result.actions) ? result.actions : [];
      for (const action of actions) {
        if (action?.type === 'open_url') {
          const targetUrl = action.url || action.payload?.url || action.value;
          if (targetUrl) {
            window.location.assign(targetUrl);
            return;
          }
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Ошибка при отправке сообщения',
      );
      console.error('Send message error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell">
      <SplashCursor
        DENSITY_DISSIPATION={3.2}
        SPLAT_RADIUS={0.22}
        SPLAT_FORCE={5600}
        COLOR_UPDATE_SPEED={8}
      />

      <div className="page-blur page-blur-a" aria-hidden="true" />
      <div className="page-blur page-blur-b" aria-hidden="true" />
      <div className="page-blur page-blur-c" aria-hidden="true" />

      <div className="app-chat-layout">
        <SessionList
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={setCurrentSessionId}
          onNewSession={createNewSession}
          onDeleteSession={deleteSession}
        />

        <main className="chat-main">
          {messages.length === 0 && (
            <HeroArea
              title="Начните общение с Chiki AI"
              subtitle="Напишите команду или вопрос, и агент выполнит действия в браузере"
            />
          )}

          {messages.length > 0 && (
            <div className="chat-area">
              <ChatMessages
                messages={messages}
                loading={loading}
              />
              <LogsPanel logs={logs} />
            </div>
          )}

          {error && (
            <div className="chat-error">
              {error}
            </div>
          )}

          <ChatInput
            onSendMessage={sendMessage}
            disabled={loading || !currentSessionId}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
