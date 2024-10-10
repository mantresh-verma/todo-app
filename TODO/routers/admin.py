from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from starlette import status
from TODO.routers.auth import get_current_user
from TODO.models import TODOS, USERS
from sqlalchemy.orm import Session
from TODO.database import SessionLocal


router = APIRouter(
    prefix="/admin",
    tags=['admin']
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependecy = (Annotated[Session, Depends(get_db)])
user_dependency = (Annotated[dict, Depends(get_current_user)])

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, example="Buy Pen")
    description: str = Field(min_length=1, max_length=100, example="Buy a new pen from market")
    priority: int = Field(gt=0, lt=6, example=4)
    complete: bool = Field(default=False)


@router.get('/todo', status_code=status.HTTP_200_OK)
async def read_all_todos(user: user_dependency ,db: db_dependecy):
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "User Not Authenticated", "user_info": None})

    role = user.get('user_role')
    if role != "admin":
        raise HTTPException(status_code=403, detail={"error": "Access Forbidden", "user_role": role})
    
    data = db.query(TODOS).all()
    if data is not None:
        return data
    else:
        raise HTTPException(status_code=404, detail='Todo Not Found')
    


@router.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency ,db: db_dependecy, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail={"error": "User Not Authenticated", "user_info": None})

    role = user.get('user_role')
    if role != "admin":
        raise HTTPException(status_code=403, detail={"error": "Access Forbidden", "user_role": role})
    
    data = db.query(TODOS).filter(TODOS.id == todo_id).first()
    if data is not None:
        return data
    else:
        raise HTTPException(status_code=404, detail='Todo Not Found')



@router.post('/todo/add-todo/', status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependecy, new_todo: TodoRequest):
    
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "User Not Authenticated", "user_info": None})

    role = user.get('user_role')
    if role != "admin":
        raise HTTPException(status_code=403, detail={"error": "Access Forbidden", "user_role": role})
    
    try:
        todo_data = TODOS(**new_todo.dict(), owner=user.get('id'))
        db.add(todo_data)
        db.commit()
        return todo_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    


@router.put('/todo/update-todo/{todo_id}',status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency , db: db_dependecy, updated_todo: TodoRequest, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail={"error": "User Not Authenticated", "user_info": None})

    role = user.get('user_role')
    if role != "admin":
        raise HTTPException(status_code=403, detail={"error": "Access Forbidden", "user_role": role})

    get_todo = db.query(TODOS).filter(TODOS.id == todo_id).first()

    if get_todo is None:
        raise HTTPException(status_code=404, detail="Todo Not Found")
    
    get_todo.title = updated_todo.title
    get_todo.description = updated_todo.description
    get_todo.priority = updated_todo.priority
    get_todo.complete = updated_todo.complete

    db.add(get_todo)
    db.commit()
    


@router.delete('/todo/delete/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency ,db: db_dependecy, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail={"error": "User Not Authenticated", "user_info": None})

    role = user.get('user_role')
    if role != "admin":
        raise HTTPException(status_code=403, detail={"error": "Access Forbidden", "user_role": role})
    
    data = db.query(TODOS).filter(TODOS.id == todo_id).first()

    if data is None:
        raise HTTPException(status_code=404, detail='Todo Not Found')
        
    db.delete(data)
    db.commit()

