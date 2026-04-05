import { useState } from 'react';
import VoiceInput from './VoiceInput';


function ChatInput({ onSendMessage, disabled = false }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (trimmed) {
      onSendMessage(trimmed);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    setMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
  };

  return (
    <div className="chat-input-container">
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="search-shell">
          <span className="search-icon" aria-hidden="true">⌕</span>
          <textarea
            className="query-textarea"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите команду... (Shift+Enter для переноса строки)"
            rows={2}
            disabled={disabled}
          />
        </div>

        <div className="query-actions">
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            disabled={disabled}
          />
          <button
            className="submit-button"
            type="submit"
            disabled={disabled || !message.trim()}
          >
            {disabled ? 'Обработка...' : 'Отправить'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
