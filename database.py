from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#Bu kütüphaneleri import ederek veritabanı işlemlerini yapabiliriz.
#create_engine ile veritabanı bağlantısını oluşturuyoruz.
#sessionmaker ile veritabanı işlemlerini yapabilmek için bir session yani oturum oluşturuyoruz.
#declarative_base ile veritabanı tablolarını oluşturuyoruz.

sqlalchemy_database_url = "sqlite:///./todoai_app.db"
#sqlite veritabanı oluşturuyoruz.
engine=create_engine(sqlalchemy_database_url,connect_args={"check_same_thread":False})
#engine oluşturuyoruz.
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
#SessionLocal oluşturuyoruz.
Base=declarative_base()
#Base oluşturuyoruz.
