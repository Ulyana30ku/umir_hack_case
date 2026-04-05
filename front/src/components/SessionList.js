function SessionList({ className = '', sessions = [], currentSessionId = null, onSelectSession = null, onNewSession = null, onDeleteSession = null }) {
  return (
    <aside className={`session-sidebar ${className}`.trim()}>
      <div className="session-header">
        <h2>Сессии</h2>
        <button
          className="new-session-btn"
          onClick={() => onNewSession?.()}
          aria-label="Новая сессия"
        >
          +
        </button>
      </div>

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-sessions">
            <p>Нет сессий</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`session-item ${session.id === currentSessionId ? 'active' : ''}`.trim()}
              onClick={() => onSelectSession?.(session.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onSelectSession?.(session.id);
                }
              }}
            >
              <div className="session-item-content">
                <div className="session-title">
                  {session.title}
                </div>
                <div className="session-date">
                  {new Date(session.created_at).toLocaleDateString('ru-RU')}
                </div>
              </div>

              <button
                type="button"
                className="session-delete-btn"
                aria-label="Удалить сессию"
                onClick={(event) => {
                  event.stopPropagation();
                  onDeleteSession?.(session.id);
                }}
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

export default SessionList;
