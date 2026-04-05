import { useEffect, useRef } from 'react';


function MessageBubble({ role, content, timestamp, isUser }) {
  return (
    <div
      className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`.trim()}
    >
      <div className="message-content">
        {content}
      </div>
      {timestamp && (
        <div className="message-time">
          {new Date(timestamp).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      )}
    </div>
  );
}

export default MessageBubble;
