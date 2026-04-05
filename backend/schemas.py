from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):


    role: str
    content: str


class MessageCreate(BaseModel):

    content: str


class MessageResponse(MessageBase):

    id: int
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentLogResponse(BaseModel):

    id: int
    session_id: int
    step: int
    action: str
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionBase(BaseModel):

    title: Optional[str] = 'New Chat'


class SessionCreate(SessionBase):

    pass


class SessionResponse(SessionBase):

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatTurnResponse(BaseModel):

    session_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse
    recent_messages: List[MessageResponse]
    logs: List[AgentLogResponse]
    actions: List[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
