from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from TODO.models import TODOS, USERS
from .test_db import engine, TestingSessionLocal
from starlette import status
from TODO.database import Base
from TODO.main import app

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def override_get_current_user():
    return {"username": "admin24", "id":1, "user_role": "admin"}

