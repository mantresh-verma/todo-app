from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from starlette import status
import TODO
from TODO.database import engine
from TODO.models import TODOS, USERS
from TODO.routers import auth
from TODO.routers.auth import get_current_user
from sqlalchemy.orm import Session
from TODO.database import SessionLocal
from typing import Annotated, Optional
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

TODO.models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="TODO/templates")


router = APIRouter(
    prefix="/user",
    tags=['user']
)


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserProfileResponse(BaseModel):
    firstname: str = Field(min_length=1, example="man")
    lastname: str = Field(min_length=1, example="ver")
    email: str = Field(min_length=3, example="man@infomail.com")
    phone_number: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    firstname: str
    lastname: str
    hashed_password: str
    is_active: bool
    phone_number: Optional[str] = None


class TodoRequest(BaseModel):
    title: str = Field(min_length=3, example="Buy Pen")
    description: str = Field(min_length=1, max_length=100,
                             example="Buy a new pen from market")
    priority: int = Field(gt=0, lt=6, example=4)
    complete: bool = Field(default=False)


class PasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, example="Enter Your Old Password")
    new_password: str = Field(min_length=6, example="Enter Your New Password")
    cnf_password: str = Field(
        min_length=6, example="Enter Your New Password Again For Confirmation")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def redirect_to_login():
    redirect_response = RedirectResponse(
        url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response


db_dependecy = (Annotated[Session, Depends(get_db)])
user_dependency = (Annotated[dict, Depends(auth.get_current_user)])

### PAGES ###


@router.get('/test', response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/todo-page", response_class=HTMLResponse)
async def render_todo_page(request: Request, db: db_dependecy):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()

        # print("something goes wrong")
        todos = db.query(TODOS).filter(TODOS.owner == user.get("id")).all()

        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})

    except:
        return redirect_to_login()


@router.get('/add-todo-page', response_class=HTMLResponse)
async def render_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}", response_class=HTMLResponse)
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependecy):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(TODOS).filter(TODOS.id == todo_id).first()

        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

    except:
        return redirect_to_login()


### ENDPOINTS ###
@router.get('/details/', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependecy):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    user_data = db.query(USERS).filter(user.get('id') == USERS.id).first()
    return user_data


@router.put('/change-password/', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependecy, password: PasswordRequest):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    user_data = db.query(USERS).filter(user.get('id') == USERS.id).first()

    if not user or not bcrypt_context.verify(password.old_password, user_data.hashed_password):
        raise HTTPException(status_code=401, detail={
                            "error": "bad credential"})

    if password.new_password != password.cnf_password:
        raise HTTPException(status_code=400, detail={
                            "error": "your new password dosenot matche with confirm password"})

    user_data.hashed_password = bcrypt_context.hash(password.cnf_password)

    db.add(user_data)
    db.commit()


@router.put('/update-profile/', status_code=status.HTTP_204_NO_CONTENT)
async def update_profile(user: user_dependency, db: db_dependecy, profile: UserProfileResponse):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    user_data = db.query(USERS).filter(user.get('id') == USERS.id).first()
    user_data.firstname = profile.firstname
    user_data.lastname = profile.lastname
    user_data.email = profile.email
    user_data.phone_number = profile.phone_number

    db.add(user_data)
    db.commit()

### todos ###
@router.get('/todo/', status_code=status.HTTP_200_OK)
async def read_all_todos(user: user_dependency, db: db_dependecy):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    data = db.query(TODOS).filter(TODOS.owner == user.get('id')).all()
    if data is not None:
        return data
    else:
        raise HTTPException(status_code=404, detail='Todo Not Found')


@router.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
async def read_todos(user: user_dependency, db: db_dependecy, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    data = db.query(TODOS).filter(
        TODOS.owner == user.get('id'), TODOS.id == todo_id).first()

    if data is not None:
        return data
    else:
        raise HTTPException(status_code=404, detail='Todo Not Found')


@router.post('/todo/add-todo/', status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependecy, new_todo: TodoRequest):

    if user is None:
        raise HTTPException(status_code=401, detail="User Not Authenticated")

    try:
        todo_data = TODOS(**new_todo.dict(), owner=user.get('id'))
        db.add(todo_data)
        db.commit()
        return todo_data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put('/todo/update-todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependecy, updated_todo: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    get_todo = db.query(TODOS).filter(
        TODOS.owner == user.get('id'), TODOS.id == todo_id).first()

    if get_todo is None:
        raise HTTPException(status_code=404, detail="Todo Not Found")

    get_todo.title = updated_todo.title
    get_todo.description = updated_todo.description
    get_todo.priority = updated_todo.priority
    get_todo.complete = updated_todo.complete

    db.add(get_todo)
    db.commit()


@router.delete('/todo/delete/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependecy, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail={
                            "error": "User Not Authenticated", "user_info": None})

    get_todo = db.query(TODOS).filter(
        TODOS.owner == user.get('id'), TODOS.id == todo_id).first()
    if get_todo is None:
        raise HTTPException(status_code=404, detail='Todo Not Found')

    db.delete(get_todo)
    db.commit()
