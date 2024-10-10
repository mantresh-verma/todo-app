from datetime import timedelta
from fastapi import HTTPException
import pytest
from .test_utils import *
from TODO.routers.auth import create_access_token, get_current_user, get_db, user_authentication, bcrypt_context, jwt, SECRET_KEY, ALGORITHM

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def test_user():
    user = USERS(
        id=1,
        username="mantresh24",
        email="test@email.com",
        firstname="Mantresh",
        lastname="Verma",
        hashed_password=bcrypt_context.hash("testpassword"),
        role="admin",
        phone_number="(143)-242-4242"
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()


def test_user_authentication(test_user):
    db = TestingSessionLocal()
    user = user_authentication(test_user.username, "testpassword", db)
    assert user is not None
    assert user.username == test_user.username

    non_existent_user = user_authentication(
        'WrongUserName', 'testpassword', db)
    assert non_existent_user is False

    wrong_password_user = user_authentication(
        test_user.username, 'wrongpassword', db)
    assert wrong_password_user is False


def test_create_token():
    username = 'testuser'
    user_id = 1
    role = 'user'
    expires_delta = timedelta(days=1)
    token = create_access_token(username, user_id, role, expires_delta)

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert decoded_token['sub'] == username
    assert decoded_token['id'] == user_id
    assert decoded_token['role'] == role


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    encode = {'sub': 'testuser', 'id': 1, 'role': 'admin'}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    user = await get_current_user(token=token)
    assert user == {'username': 'testuser', 'id': 1, 'user_role': 'admin'}


@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
    encode = {'role': 'user'}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == {
        "error": "Could not validate user",
        "username": None,
        "user_id": None
    }
