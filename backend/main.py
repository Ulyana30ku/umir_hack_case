import sys
import importlib
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, get_db, SessionLocal
from schemas import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    AgentLogResponse,
    ChatTurnResponse,
)
from services.session_service import SessionService
from services.log_service import LogService
from services.orchestrator import Orchestrator

init_db()

app = FastAPI(
    title='AI Browser Assistant',
    description='Chat-based AI assistant for browser automation',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _mount_ml_agent_routes() -> None:

    ml_project_root = Path(__file__).resolve().parent / 'hack-parser-ml'
    ml_project_path = str(ml_project_root)

    if ml_project_path not in sys.path:
        sys.path.append(ml_project_path)

    try:
        ml_agent_router = importlib.import_module('app.api.routes.agent')

        app.include_router(ml_agent_router.router, prefix='/ml', tags=['ML Agent'])
    except Exception as exc:
        print(f'[WARN] Failed to mount hack-parser-ml routes: {exc}')


_mount_ml_agent_routes()

@app.get('/health')
def health_check():

    return {'status': 'ok', 'service': 'AI Browser Assistant'}

@app.get('/sessions', response_model=list[SessionResponse])
def get_sessions(db: Session = Depends(get_db)):

    sessions = SessionService.get_all_sessions(db)
    return sessions


@app.post('/sessions', response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
):
    title = session_data.title or 'New Chat'
    session = SessionService.create_session(db, title=title)
    return session


@app.get('/sessions/{session_id}', response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    return session


@app.delete('/sessions/{session_id}')
def delete_session(session_id: int, db: Session = Depends(get_db)):
    deleted = SessionService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Session not found')
    return {'status': 'ok', 'session_id': session_id}

@app.get('/sessions/{session_id}/messages', response_model=list[MessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    messages = SessionService.get_session_messages(db, session_id)
    return messages


@app.post('/sessions/{session_id}/messages', response_model=ChatTurnResponse)
def send_message(
    session_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
):

    session = SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    user_message = SessionService.add_message(
        db,
        session_id,
        'user',
        message_data.content,
    )

    history = SessionService.get_recent_context(db, session_id, limit=20)

    assistant_response_content, logs, actions = Orchestrator.handle_chat_message(
        db,
        session_id,
        message_data.content,
        history,
    )

    assistant_message = SessionService.add_message(
        db,
        session_id,
        'assistant',
        assistant_response_content,
    )

    recent_messages = SessionService.get_recent_context(db, session_id, limit=20)

    db_logs = LogService.get_last_logs(db, session_id, count=20)

    return ChatTurnResponse(
        session_id=session_id,
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        recent_messages=[MessageResponse.model_validate(msg) for msg in recent_messages],
        logs=[AgentLogResponse.model_validate(log) for log in db_logs],
        actions=actions,
    )

@app.get('/sessions/{session_id}/logs', response_model=list[AgentLogResponse])
def get_session_logs(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    logs = LogService.get_session_logs(db, session_id)
    return logs


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app',
        host='127.0.0.1',
        port=8000,
        reload=True,
    )
