from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default='New Chat')
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship('Message', back_populates='session', cascade='all, delete-orphan')
    logs = relationship('AgentLog', back_populates='session', cascade='all, delete-orphan')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship('ChatSession', back_populates='messages')


class AgentLog(Base):
    __tablename__ = 'agent_logs'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    step = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship('ChatSession', back_populates='logs')
