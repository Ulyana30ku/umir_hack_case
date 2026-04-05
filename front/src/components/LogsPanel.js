import { useState } from 'react';

function LogsPanel({ logs = [] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <div className="logs-panel">
      <button
        className="logs-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="logs-toggle-text">
          {isExpanded ? '▼' : '▶'} Ход выполнения ({logs.length})
        </span>
      </button>

      {isExpanded && (
        <div className="logs-list">
          {logs.map((log) => (
            <div key={log.id} className="log-item">
              <div className="log-step">
                Шаг {log.step}
              </div>
              <div className="log-action">
                {log.action}
              </div>
              {log.details && (
                <div className="log-details">
                  {log.details}
                </div>
              )}
              <div className="log-time">
                {new Date(log.created_at).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LogsPanel;
