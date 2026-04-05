from sqlalchemy.orm import Session

from models import AgentLog


class LogService:
    """Сервис для работы с логами действий агента."""

    @staticmethod
    def add_log(
        db: Session,
        session_id: int,
        step: int,
        action: str,
        details: str | None = None,
    ) -> AgentLog:
        """Добавить лог действия агента."""
        log = AgentLog(
            session_id=session_id,
            step=step,
            action=action,
            details=details,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_session_logs(db: Session, session_id: int) -> list[AgentLog]:
        """Получить все логи сессии."""
        return db.query(AgentLog).filter(AgentLog.session_id == session_id).all()

    @staticmethod
    def get_last_logs(
        db: Session,
        session_id: int,
        count: int = 10,
    ) -> list[AgentLog]:
        """Получить последние логи сессии."""
        return (
            db.query(AgentLog)
            .filter(AgentLog.session_id == session_id)
            .order_by(AgentLog.created_at.desc())
            .limit(count)
            .all()[::-1]
        )
