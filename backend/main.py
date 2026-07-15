from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base, SessionLocal
import models
from routers import (
    auth_router,
    dashboard,
    policies,
    incidents,
    scans,
    reports,
    integrations,
    notifications,
    settings
)
from seed import seed_db

# Veritabanı tablolarını oluştur ve gerekirse örnek veri ekle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.drop_all(bind=engine) # Geliştirme aşamasında sıfırlamak isterseniz
    Base.metadata.create_all(bind=engine)
    
    # DB bağlantısı açıp seed işlemi yap
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
    
    # APScheduler gibi arka plan servisleri başlatılabilir
    yield
    # Kapatılırken yapılacak temizlikler

app = FastAPI(
    title="DLP API",
    description="Veri Kaybı Önleme Sistemi Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için * kullanılıyor. Prod'da arayüzün URL'si olmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Sistem çalışıyor"}
