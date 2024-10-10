from .test_utils import *
from TODO.routers.auth import bcrypt_context
from TODO.routers.user import get_db, get_current_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


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


def test_user_details(test_user):
    response = client.get("user/details/")
    assert response.status_code == 200
    assert response.json()['username'] == "mantresh24"
    assert response.json()['email'] == "test@email.com"
    assert response.json()['firstname'] == "Mantresh"
    assert response.json()['lastname'] == "Verma"
    assert bcrypt_context.verify(
        "testpassword", response.json()['hashed_password'])
    assert response.json()['role'] == "admin"
    assert response.json()['phone_number'] == "(143)-242-4242"


def test_change_password(test_user):
    request_psw = {
        "old_password": "testpassword",
        "new_password": "newpassword",
        "cnf_password": "newpassword"
    }
    response = client.put("user/change-password/", json=request_psw)
    assert response.status_code == 204

    hashed_password = bcrypt_context.hash(request_psw.get('old_password'))
    assert bcrypt_context.verify("testpassword", hashed_password)


def test_change_password_not_match(test_user):
    request_psw = {
        "old_password": "testpassword",
        "new_password": "newpassword",
        "cnf_password": "newpassword1"
    }
    response = client.put("user/change-password/", json=request_psw)
    assert response.status_code == 400


def test_update_profile(test_user):
    request_data = {
        'id': 1, 
        'username': "mantresh24",
        'email': "test@email.com",
        'firstname': "Mantresh",
        'lastname': "Verma",
        'hashed_password': bcrypt_context.hash("testpassword"),
        'role': "admin",
        'phone_number': "(143)-242-4242"
    }

    response = client.put("user/update-profile/", json=request_data) 
    
    # Check if response status code is 204 No Content
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Fetch the updated user from the database
    db = TestingSessionLocal()
    model = db.query(USERS).filter(USERS.id == 1).first()
    
    # Verify that the fields have been updated
    assert model.firstname == request_data.get("firstname")
    assert model.lastname == request_data.get("lastname")
    assert model.username == request_data.get("username")
    assert model.email == request_data.get("email")
    assert model.phone_number == request_data.get("phone_number")
    assert model.role == request_data.get("role")


