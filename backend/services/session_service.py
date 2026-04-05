from sqlalchemy.orm import Session

from models import ChatSession, Message


class SessionService:

    @staticmethod
    def create_session(
        db: Session,
        title: str = 'New Chat',
    ) -> ChatSession:
        """Создать новую сессию."""
        session = ChatSession(title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(
        db: Session,
        session_id: int,
    ) -> ChatSession | None:
        """Получить сессию по ID."""
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()

    @staticmethod
    def get_all_sessions(db: Session) -> list[ChatSession]:
        return (
            db.query(ChatSession)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    @staticmethod
    def delete_session(
        db: Session,
        session_id: int,
    ) -> bool:
        session = SessionService.get_session(db, session_id)
        if not session:
            return False

        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def get_session_messages(
        db: Session,
        session_id: int,
    ) -> list[Message]:
        return (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def get_recent_context(
        db: Session,
        session_id: int,
        limit: int = 10,
    ) -> list[Message]:
        return (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()[::-1]
        )

    @staticmethod
    def get_recent_messages(
        db: Session,
        session_id: int,
        limit: int = 20,
    ) -> list[Message]:
        return SessionService.get_recent_context(db, session_id, limit=limit)

    @staticmethod
    def add_message(
        db: Session,
        session_id: int,
        role: str,
        content: str,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
