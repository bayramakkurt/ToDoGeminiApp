from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todo(Base): #Todo adında bir class oluşturuyoruz ve Base classından miras alıyoruz.Neden Base classından miras aldık?Çünkü Base classı veritabanı tablolarını oluşturmak için kullanılır.
    __tablename__="todos"  #todos adında bir tablo oluşturuyoruz.
    id=Column(Integer,primary_key=True,index=True) #id adında bir sütun oluşturuyoruz ve bu sütun primary key olacak.
    title=Column(String) #title adında bir sütun oluşturuyoruz ve bu sütun string tipinde olacak.
    description=Column(String) #description adında bir sütun oluşturuyoruz ve bu sütun string tipinde olacak.
    priority = Column(Integer)  # priority adında bir sütun oluşturuyoruz ve bu sütun integer tipinde olacak.
    complete=Column(Boolean,default=False) #completed adında bir sütun oluşturuyoruz ve bu sütun boolean tipinde olacak.
#Yukarıda oluşturduğumuz sütunlar veritabanında tablo oluşturulurken kullanılacak sütunlardır.
    owner_id=Column(Integer,ForeignKey("users.id")) #owner_id adında bir sütun oluşturuyoruz ve bu sütun integer tipinde olacak.

class User(Base): #User adında bir class oluşturuyoruz ve Base classından miras alıyoruz.Neden Base classından miras aldık?Çünkü Base classı veritabanı tablolarını oluşturmak için kullanılır.
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    email=Column(String,unique=True)
    username=Column(String,unique=True)
    first_name=Column(String)
    last_name=Column(String)
    hashed_password=Column(String)
    is_active=Column(Boolean,default=True)
    role=Column(String,default="user")
    phone_number=Column(String,unique=True)