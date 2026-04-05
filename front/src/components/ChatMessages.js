import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble.js';


function ChatMessages({ messages = [], loading = false, showEmptyState = true }) {
  const messagesEndRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, autoScroll]);

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  return (
    <div
      className={`chat-messages-container ${messages.length === 0 && showEmptyState ? 'start-screen-mode' : ''}`.trim()}
      onScroll={handleScroll}
    >
      {messages.length === 0 && showEmptyState ? (
        <div className="chat-empty-state">
          <h3>Начните общение с Chiki AI</h3>
          <p>Напишите команду или вопрос, и агент выполнит действия в браузере</p>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
              timestamp={msg.created_at}
              isUser={msg.role === 'user'}
            />
          ))}
          {loading && (
            <div className="message-bubble message-assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;
