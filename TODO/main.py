from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from TODO import models
from starlette import status
from TODO.routers import auth, todos, user, admin
from TODO.database import engine
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="TODO/templates")
app.mount("/static", StaticFiles(directory="TODO/static"), name="static")

@app.get("/")
def test(request: Request):
    return RedirectResponse(url="/user/todo/", status_code=status.HTTP_302_FOUND)




@app.get('/healthy')
def read_root():
    return {'status': 'Healthy'}

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)
# app.include_router(todos.router)



