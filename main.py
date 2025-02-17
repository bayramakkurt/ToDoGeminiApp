from fastapi import FastAPI,Request
from starlette.responses import RedirectResponse
from starlette import status
from .models import Base
from .database import engine
from fastapi.staticfiles import StaticFiles
from .routers.todo import router as todo_router
from .routers.auth import router as auth_router
import os
#auth_router adında bir değişken oluşturuyoruz ve bu değişken routers/auth.py dosyasından gelir.
#todo_router adında bir değişken oluşturuyoruz ve bu değişken routers/todo.py dosyasından gelir.

app = FastAPI()
app.include_router(auth_router)
app.include_router(todo_router)

script_dir=os.path.dirname(__file__)
st_abs_file_path=os.path.join(script_dir,"static/")

app.mount("/static",StaticFiles(directory=st_abs_file_path),name="static")

@app.get("/")
async def read_root(request:Request):
    return RedirectResponse(url="/todo/todo-page",status_code=status.HTTP_302_FOUND)

Base.metadata.create_all(bind=engine) #Burada yaptığımız işlem veritabanında tabloları oluşturmak için Base classını kullanıyoruz.
