"""
DLP Sistemi - Veritabanı Yapılandırması
SQLAlchemy engine, session ve base sınıfı kurulumu
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Veritabanı bağlantı URL'si
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dlp_database.db")

# SQLite için özel ayarlar
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Engine oluştur
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # SQL sorgularını loglamak için True yapın
    pool_pre_ping=True,  # Bağlantı sağlığını kontrol et
)

# SQLite için yabancı anahtar kısıtlamalarını etkinleştir
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # Yazma performansını artır
        cursor.close()

# Session fabrikası
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tüm modeller için temel sınıf
Base = declarative_base()


def get_db():
    """
    FastAPI bağımlılığı - Her istek için yeni bir veritabanı oturumu sağlar.
    İstek tamamlandığında oturumu otomatik olarak kapatır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Tüm tabloları oluştur (yoksa)"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Tüm tabloları sil (dikkatli kullanın!)"""
    Base.metadata.drop_all(bind=engine)
