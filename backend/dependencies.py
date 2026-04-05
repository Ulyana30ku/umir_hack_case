from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db as _get_db


def get_db() -> Session:
    db = _get_db()
    return next(db)
