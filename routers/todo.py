from alembic.util import status
from fastapi import APIRouter, Depends, Path, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.testing import db
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import google.generativeai as genai
import os
import markdown
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,AIMessage
from models import Base,Todo
from database import engine,SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
#Status kütüphanesi FastAPI'nin HTTP status kodlarını kullanabilmemizi sağlar.
#BaseModel kütüphanesi Pydantic kütüphanesinden gelir ve Pydantic kütüphanesi veri doğrulama işlemlerinde kullanılır.
#Field kütüphanesi Pydantic kütüphanesinden gelir ve Pydantic kütüphanesi veri doğrulama işlemlerinde kullanılır.
#Base kütüphanesi models.py dosyasından gelir ve veritabanı tablolarını oluşturmak için kullanılır.
#Todo kütüphanesi models.py dosyasından gelir ve veritabanında oluşturduğumuz tabloyu temsil eder.
#engine kütüphanesi database.py dosyasından gelir ve veritabanı işlemlerini yapabilmemizi sağlar.
#SessionLocal kütüphanesi database.py dosyasından gelir ve veritabanı işlemlerini yapabilmemizi sağlar.
#Annotated kütüphanesi Pydantic kütüphanesinden gelir ve Pydantic kütüphanesi veri doğrulama işlemlerinde kullanılır.
#Session kütüphanesi SQLAlchemy kütüphanesinden gelir ve veritabanı işlemlerini yapabilmemizi sağlar.
#Depends kütüphanesi FastAPI kütüphanesinden gelir ve Dependency Injection yapısını kullanarak bir fonksiyonu bir değişkene bağlamamızı sağlar.
#Path kütüphanesi FastAPI kütüphanesinden gelir ve URL'den parametre alabilmemizi sağlar.


router = APIRouter(
    prefix="/todo",
    tags=["Todo İşlemleri"]
)


class TodoRequest(BaseModel):
    title:str=Field(min_length=3)
    description:str=Field(min_length=3,max_length=1000)
    priority:int=Field(gt=0,lt=6)
    complete: bool
#TodoRequest adında bir class oluşturuyoruz ve bu class BaseModel classından miras alıyor.
#BaseModel olma sebebi Pydantic kütüphanesini kullanarak veri doğrulama işlemlerini yapabilmemiz.

def get_db():
    db=SessionLocal() #SessionLocal fonksiyonunu çağırarak db adında bir değişken oluşturuyoruz.
    try:
        yield db #db yi döndürüyoruz.Return aynı mantıkta çalışır ancak yield daha çok generator fonksiyonlarda kullanılır.
    finally:
        db.close() #db yi kapatıyoruz.

templates=Jinja2Templates(directory="templates")

db_dependency=Annotated[Session,Depends(get_db)] #db_dependency adında bir değişken oluşturuyoruz ve bu değişkenin tipi Session olacak.
#Depends(get_db) ile get_db fonksiyonunu db_dependency değişkenine bağlıyoruz.
#Annotated olmasının nedeni ise FastAPI'nin Dependency Injection yapısını kullanarak get_db fonksiyonunu db_dependency değişkenine bağlamak.
user_dependency=Annotated[dict,Depends(get_current_user)] #user_dependency adında bir değişken oluşturuyoruz ve bu değişkenin tipi Session olacak.

def redirect_to_login():
    redirect_response=RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response

@router.get("/todo-page")
async def render_todo_page(request:Request,db:db_dependency):
    try:
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos=db.query(Todo).filter(Todo.owner_id==user.get('id')).all()
        return templates.TemplateResponse("todo.html",{"request":request,"todos":todos,"user":user})
    except:
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_add_todo_page(request:Request):
    try:
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html",{"request":request,"user":user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_todo_page(request:Request,todo_id:int,db:db_dependency):
    try:
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todo=db.query(Todo).filter(Todo.id==todo_id).first()
        return templates.TemplateResponse("edit-todo.html",{"request":request,"todo":todo,"user":user})
    except:
        return redirect_to_login()




@router.get("/")
async def read_all(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    return db.query(Todo).filter(Todo.owner_id==user.get('id')).all() #db değişkenine bağlı olan veritabanından Todo tablosundaki tüm verileri çekiyoruz.

@router.get("/todo/{todo_id}" ,status_code=status.HTTP_200_OK)
async def read_by_id(user:user_dependency,db: db_dependency,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get('id')).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo not found")
#Path kütüphanesi ile URL'den parametre alabiliyoruz.
#gt=0 ile id parametresinin 0'dan büyük olmasını sağlıyoruz.
#HTTPException ile hata mesajı döndürüyoruz.
#status_code=status.HTTP_404_NOT_FOUND ile HTTP status kodu döndürüyoruz.
#db_dependency ile veritabanı işlemlerini yapabilmemizi sağlıyoruz.
#db.query(Todo).filter(Todo.id==id).first() ile veritabanından id parametresine göre veri çekiyoruz.

@router.post("/todo",status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency,todo_request:TodoRequest,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    updated_description = create_todo_with_gemini(todo_request.description)
    print(updated_description)
    # Güncellenmiş açıklama ile Todo nesnesini oluştur
    todo = Todo(
        title=todo_request.title,
        description=updated_description,
        priority=todo_request.priority,
        complete=todo_request.complete,
        owner_id=user.get('id')
    )

    db.add(todo)
    db.commit()


#TodoRequest ile veri doğrulama işlemlerini yapıyoruz.
#db_todo=Todo(**todo_request.dict()) ile Todo tablosuna veri ekliyoruz.
#db.add(db_todo) ile veritabanına veri ekliyoruz.
#db.commit() ile veritabanındaki değişiklikleri kaydediyoruz.
#db.refresh(db_todo) ile veritabanındaki değişiklikleri güncelliyoruz.
#db.add ile **todo_request.dict() arasındaki fark şudur: db.add ile veritabanına veri eklerken **todo_request.dict() ile veritabanına veri eklerken veri doğrulama işlemlerini yaparız.

@router.put("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency,db:db_dependency,todo_request:TodoRequest,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo not found")
    todo.title=todo_request.title
    todo.description=todo_request.description
    todo.complete=todo_request.complete
    todo.priority=todo_request.priority
    db.add(todo)
    db.commit()

#todo.title=todo_request.title ile title sütununu güncelliyoruz.
#db.add(todo) ile veritabanına veriyi ekliyoruz.
#db.commit() ile veritabanındaki değişiklikleri kaydediyoruz.
#db.query(Todo).filter(Todo.id==id).first() ile veritabanından id parametresine göre veri çekiyoruz.
#todo_request:TodoRequest ile veri doğrulama işlemlerini yapıyoruz.

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    todo=db.query(Todo).filter(Todo.id==todo_id).filter(Todo.owner_id==user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo not found")
    db.delete(todo)
    db.commit()

#db.query(Todo).filter(Todo.id==id).first() ile veritabanından id parametresine göre veri çekiyoruz.
#db.delete(todo) ile veritabanından veriyi siliyoruz.
#db.commit() ile veritabanındaki değişiklikleri kaydediyoruz.

def markdown_to_text(markdown_string):
    html = markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text()
    return text

def create_todo_with_gemini(todo_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
    llm=ChatGoogleGenerativeAI(model="gemini-pro")
    response=llm.invoke(
        [
            HumanMessage(
                content="I will provide you a todo item to add my to do list. What i want you to do is to create a longer and more comprehensive description of that todo item, my next message will be my todo and your answer in Turkish:"),
            HumanMessage(content=todo_string)
        ]
    )
    return markdown_to_text(response.content)

