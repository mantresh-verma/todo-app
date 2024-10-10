from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette import status
from TODO.models import USERS
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from TODO.database import SessionLocal
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt

router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

templates = Jinja2Templates(directory="TODO/templates")

SECRET_KEY = "3eed4bf55e770ac5af530390fa8cbf84bffb9087d9f61bd13a41ee05f316d306"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class UserRequest(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=3, example="man@infomail.com")
    firstname: str = Field(min_length=1 , example="man")
    lastname: str = Field(min_length=1, example="ver")
    password: str = Field(min_length=1, example="Abc#20@24")
    is_active: bool 
    role: str = Field(min_length=1)
    phone_number: str = Field(min_length=10, example="2234561234")

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependecy = (Annotated[Session, Depends(get_db)])


def user_authentication(username: str, password: str, db):
    user = db.query(USERS).filter(USERS.username == username).first()

    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    
    return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp":expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail={"error": "Could not validate user", "username": username, "user_id": user_id})
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=401,detail='Could not validate user.')

# PAGES #

@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



# END_POINTS #
@router.post('/add-user/', status_code=status.HTTP_201_CREATED )
async def create_user(db: db_dependecy, create_user_request: UserRequest):
    new_user_model = USERS(
        email=create_user_request.email,
        username=create_user_request.username,
        firstname=create_user_request.firstname,
        lastname=create_user_request.lastname,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
        phone_number=create_user_request.phone_number
    )

    if new_user_model is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
    db.add(new_user_model)
    db.commit()


@router.post('/token/', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependecy):
    
    user = user_authentication(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(status_code=401,detail='Could not validate user.')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}

