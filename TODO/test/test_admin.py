from .test_utils import *
from TODO.routers.admin import get_db, get_current_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def test_todo():
    todo = TODOS(
        title="Learn to code!",
        description="Need to learn daily",
        priority=5,
        complete =False,
        owner=1
    )
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

def test_read_all_authenticated(test_todo):
    response = client.get("admin/todo/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'title': 'Learn to code!', 'description': 'Need to learn daily',
                                'priority': 5, 'complete': False,
                                'owner': 1, 'id': 1}]


def test_read_one_authenticated(test_todo):
    response = client.get("admin/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'title': 'Learn to code!', 'description': 'Need to learn daily',
                                'priority': 5, 'complete': False,
                                'owner': 1, 'id': 1}]
    
def test_read_one_authenticated(test_todo):
    response = client.get("admin/todo/2")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Todo Not Found'}


def test_create_todo(test_todo):
    request_data = {
                    'title': 'Learn to code!', 
                    'description': 'Need to learn daily',
                    'priority': 5, 
                    'complete': False,
                    'owner': 1, 
                    'id':2
                    }
    
    response = client.post("admin/todo/add-todo/", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    model = db.query(TODOS).filter(TODOS.id == 2).first()
    assert model.title == request_data.get('title')
    assert model.description == request_data.get('description')
    assert model.priority == request_data.get('priority')
    assert model.complete == request_data.get('complete')

def test_update_todo(test_todo):
    request_data = {
                    'title': 'Learn to code with fun!', 
                    'description': 'Need to learn daily',
                    'priority': 5, 
                    'complete': False,
                    'owner': 1, 
                    'id': 1
                    }
    
    response = client.put("admin/todo/update-todo/1", json=request_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = db.query(TODOS).filter(TODOS.id == 1).first()
    model.title = request_data.get("title")

def test_update_todo_not_found(test_todo):
    request_data={
        'title':'Change the title of the todo already saved!',
        'description': 'Need to learn everyday!',
        'priority': 5,
        'complete': False,
    }

    response = client.put('admin/todo/update-todo/10', json=request_data)
    assert response.status_code == 404
    assert response.json() == {'detail': 'Todo Not Found'}


def test_delete_one(test_todo):
    response = client.delete("admin/todo/delete/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = db.query(TODOS).filter(TODOS.id == 1).first()
    assert model is None

def test_delete_not_found(test_todo):
    response = client.delete("admin/todo/delete/2")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Todo Not Found'}
