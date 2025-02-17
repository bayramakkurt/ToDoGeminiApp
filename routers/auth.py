from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import SessionLocal
from models import User
from jose import JWTError,jwt
from fastapi.templating import Jinja2Templates

router=APIRouter(
    prefix="/auth", #Path'de /auth ekleyerek bu router'ı kullanabiliriz.
    tags=["Kullanıcı Giriş İşlemleri"] #Bu router'ın tag'ını belirliyoruz.
)

templates=Jinja2Templates(directory="templates")

SECRET_KEY="dv1hyoGQsV09jMF1htLibVWGG4sSPLGZTEgeaVRZCZG26OikBUyQLEHxi9gY6CTV"
ALGORITHM="HS256"

def create_access_token(username:str,user_id:int,role:str,expires_delta:timedelta):
    to_encode={"sub":username,"id":user_id,"role":role}
    expire=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    db=SessionLocal() #SessionLocal fonksiyonunu çağırarak db adında bir değişken oluşturuyoruz.
    try:
        yield db #db yi döndürüyoruz.Return aynı mantıkta çalışır ancak yield daha çok generator fonksiyonlarda kullanılır.
    finally:
        db.close() #db yi kapatıyoruz.

db_dependency=Annotated[Session,Depends(get_db)] #db_dependency adında bir değişken oluşturuyoruz ve bu değişkenin tipi Session olacak.

class CreateUserRequest(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str
    role:str
    phone_number:str

class Token(BaseModel):
    access_token:str
    token_type:str

def authenticate_user(username:str,password:str,db):
    user=db.query(User).filter(User.username.ilike(username)).first()
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

async def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username= payload.get('sub')
        user_id=payload.get('id')
        user_role=payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        return {"username":username,"id":user_id,"user_role":user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")


@router.get("/login-page")
async def render_login_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

@router.get("/register-page")
async def render_register_page(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})


@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request:CreateUserRequest,db:db_dependency):
    user=User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=str(create_user_request.phone_number)
    )
    db.add(user)
    db.commit()

@router.post("/token",response_model=Token)
async def login_for_acces_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],db:db_dependency):
    user=authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid username or password")
    token=create_access_token(user.username,user.id,user.role,timedelta(minutes=60))
    return {"access_token":token,"token_type":"bearer"}