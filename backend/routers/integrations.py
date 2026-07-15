"""
DLP Sistemi - Entegrasyon Yönetimi Yönlendiricisi
Google Workspace ve Microsoft 365 entegrasyonları için CRUD ve test endpoint'leri
"""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log

router = APIRouter(prefix="/integrations", tags=["Entegrasyonlar"])


@router.get("", response_model=schemas.IntegrationListResponse)
async def list_integrations(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Tüm entegrasyonları listele"""
    integrations = db.query(models.Integration).order_by(
        models.Integration.created_at.desc()
    ).all()

    total = len(integrations)

    # Hassas config alanlarını maskele
    items = []
    for intg in integrations:
        config = dict(intg.config or {})
        # Şifre ve secret alanlarını maskele
        for key in ["client_secret", "password", "private_key", "api_key", "token"]:
            if key in config:
                config[key] = "***gizlendi***"

        items.append(schemas.IntegrationResponse(
            id=intg.id,
            name=intg.name,
            type=intg.type,
            config=config,
            is_active=intg.is_active,
            last_sync=intg.last_sync,
            last_sync_status=intg.last_sync_status,
            last_sync_message=intg.last_sync_message,
            created_at=intg.created_at,
        ))

    return schemas.IntegrationListResponse(items=items, total=total)


@router.post("", response_model=schemas.IntegrationResponse, status_code=201)
async def create_integration(
    integration_data: schemas.IntegrationCreate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Yeni entegrasyon oluştur (Sadece Yönetici)"""
    # Aynı isimde entegrasyon var mı?
    existing = db.query(models.Integration).filter(
        models.Integration.name == integration_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"'{integration_data.name}' adında bir entegrasyon zaten mevcut"
        )

    new_integration = models.Integration(
        name=integration_data.name,
        type=integration_data.type,
        config=integration_data.config,
        is_active=integration_data.is_active,
    )
    db.add(new_integration)
    db.commit()
    db.refresh(new_integration)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="integration.created",
        resource_type="integration",
        resource_id=new_integration.id,
        details={"name": new_integration.name, "type": new_integration.type},
        ip_address=request.client.host if request.client else None,
    )

    # Config'i maskele
    config = dict(new_integration.config or {})
    for key in ["client_secret", "password", "private_key", "api_key", "token"]:
        if key in config:
            config[key] = "***gizlendi***"

    return schemas.IntegrationResponse(
        id=new_integration.id,
        name=new_integration.name,
        type=new_integration.type,
        config=config,
        is_active=new_integration.is_active,
        last_sync=new_integration.last_sync,
        last_sync_status=new_integration.last_sync_status,
        last_sync_message=new_integration.last_sync_message,
        created_at=new_integration.created_at,
    )


@router.get("/{integration_id}", response_model=schemas.IntegrationResponse)
async def get_integration(
    integration_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Belirli bir entegrasyonun detayını döndür"""
    intg = db.query(models.Integration).filter(
        models.Integration.id == integration_id
    ).first()

    if not intg:
        raise HTTPException(
            status_code=404,
            detail=f"#{integration_id} ID'li entegrasyon bulunamadı"
        )

    config = dict(intg.config or {})
    for key in ["client_secret", "password", "private_key", "api_key", "token"]:
        if key in config:
            config[key] = "***gizlendi***"

    return schemas.IntegrationResponse(
        id=intg.id,
        name=intg.name,
        type=intg.type,
        config=config,
        is_active=intg.is_active,
        last_sync=intg.last_sync,
        last_sync_status=intg.last_sync_status,
        last_sync_message=intg.last_sync_message,
        created_at=intg.created_at,
    )


@router.put("/{integration_id}", response_model=schemas.IntegrationResponse)
async def update_integration(
    integration_id: int,
    update_data: schemas.IntegrationUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Entegrasyonu güncelle"""
    intg = db.query(models.Integration).filter(
        models.Integration.id == integration_id
    ).first()

    if not intg:
        raise HTTPException(
            status_code=404,
            detail=f"#{integration_id} ID'li entegrasyon bulunamadı"
        )

    if update_data.name is not None:
        intg.name = update_data.name
    if update_data.config is not None:
        # Mevcut config ile birleştir (gizlendi değerlerini koru)
        existing_config = dict(intg.config or {})
        new_config = dict(update_data.config)
        for key, value in new_config.items():
            if value != "***gizlendi***":
                existing_config[key] = value
        intg.config = existing_config
    if update_data.is_active is not None:
        intg.is_active = update_data.is_active

    db.commit()
    db.refresh(intg)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="integration.updated",
        resource_type="integration",
        resource_id=integration_id,
        details={"name": intg.name},
        ip_address=request.client.host if request.client else None,
    )

    config = dict(intg.config or {})
    for key in ["client_secret", "password", "private_key", "api_key", "token"]:
        if key in config:
            config[key] = "***gizlendi***"

    return schemas.IntegrationResponse(
        id=intg.id,
        name=intg.name,
        type=intg.type,
        config=config,
        is_active=intg.is_active,
        last_sync=intg.last_sync,
        last_sync_status=intg.last_sync_status,
        last_sync_message=intg.last_sync_message,
        created_at=intg.created_at,
    )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Entegrasyonu sil"""
    intg = db.query(models.Integration).filter(
        models.Integration.id == integration_id
    ).first()

    if not intg:
        raise HTTPException(
            status_code=404,
            detail=f"#{integration_id} ID'li entegrasyon bulunamadı"
        )

    name = intg.name
    db.delete(intg)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="integration.deleted",
        resource_type="integration",
        resource_id=integration_id,
        details={"name": name},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Entegrasyon '{name}' başarıyla silindi"}


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: int,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Entegrasyon bağlantısını test et"""
    intg = db.query(models.Integration).filter(
        models.Integration.id == integration_id
    ).first()

    if not intg:
        raise HTTPException(
            status_code=404,
            detail=f"#{integration_id} ID'li entegrasyon bulunamadı"
        )

    config = intg.config or {}
    success = False
    message = ""

    try:
        if intg.type == models.IntegrationType.GOOGLE_WORKSPACE:
            from engines.cloud_scanner import GoogleWorkspaceScanner
            scanner = GoogleWorkspaceScanner(config)
            success = scanner.authenticate()
            message = "Google Workspace bağlantısı başarılı" if success else "Google Workspace kimlik doğrulaması başarısız"

        elif intg.type == models.IntegrationType.OFFICE365:
            from engines.cloud_scanner import Office365Scanner
            scanner = Office365Scanner(
                tenant_id=config.get("tenant_id", ""),
                client_id=config.get("client_id", ""),
                client_secret=config.get("client_secret", "")
            )
            success = scanner.authenticate()
            message = "Microsoft 365 bağlantısı başarılı" if success else "Microsoft 365 kimlik doğrulaması başarısız"

        elif intg.type == models.IntegrationType.SMTP:
            # SMTP bağlantı testi
            import socket
            host = config.get("host", "")
            port = int(config.get("port", 587))
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            success = True
            message = f"SMTP sunucusu {host}:{port} erişilebilir"

        elif intg.type == models.IntegrationType.WEBHOOK:
            import requests
            webhook_url = config.get("url", "")
            if not webhook_url:
                message = "Webhook URL'si yapılandırılmamış"
            else:
                response = requests.post(
                    webhook_url,
                    json={"test": True, "source": "DLP Güvenlik Sistemi"},
                    timeout=5
                )
                success = response.ok
                message = f"Webhook yanıtı: {response.status_code}"

        elif intg.type in (models.IntegrationType.SLACK, models.IntegrationType.TEAMS):
            import requests
            webhook_url = config.get("webhook_url", "")
            if not webhook_url:
                message = "Webhook URL'si yapılandırılmamış"
            else:
                payload = {"text": "DLP Güvenlik Sistemi - Bağlantı Testi ✅"}
                response = requests.post(webhook_url, json=payload, timeout=5)
                success = response.ok
                message = f"Mesaj gönderildi: {response.status_code}"

        else:
            message = f"'{intg.type}' türü için test desteklenmiyor"

    except Exception as e:
        message = f"Bağlantı hatası: {str(e)}"

    # Son test durumunu kaydet
    intg.last_sync = datetime.utcnow()
    intg.last_sync_status = "success" if success else "failed"
    intg.last_sync_message = message
    db.commit()

    return {
        "integration_id": integration_id,
        "integration_name": intg.name,
        "success": success,
        "message": message,
        "tested_at": datetime.utcnow().isoformat(),
    }


@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Entegrasyon ile senkronizasyon başlat (arka planda)"""
    intg = db.query(models.Integration).filter(
        models.Integration.id == integration_id
    ).first()

    if not intg:
        raise HTTPException(
            status_code=404,
            detail=f"#{integration_id} ID'li entegrasyon bulunamadı"
        )

    if not intg.is_active:
        raise HTTPException(
            status_code=400,
            detail="Deaktif entegrasyon senkronize edilemez"
        )

    intg.last_sync_status = "syncing"
    intg.last_sync_message = "Senkronizasyon başlatıldı..."
    db.commit()

    background_tasks.add_task(
        _sync_integration_background,
        integration_id=integration_id,
        created_by=current_user.id,
    )

    return {
        "message": f"'{intg.name}' entegrasyonu için senkronizasyon başlatıldı",
        "integration_id": integration_id,
    }


def _sync_integration_background(integration_id: int, created_by: int):
    """Entegrasyon senkronizasyonunu arka planda çalıştır"""
    db = SessionLocal()
    try:
        intg = db.query(models.Integration).filter(
            models.Integration.id == integration_id
        ).first()

        if not intg:
            return

        config = intg.config or {}
        files_synced = 0
        message = ""

        if intg.type == models.IntegrationType.GOOGLE_WORKSPACE:
            from engines.cloud_scanner import GoogleWorkspaceScanner
            scanner = GoogleWorkspaceScanner(config)
            if scanner.authenticate():
                files = scanner.list_drive_files()
                files_synced = len(files)
                message = f"Google Drive'dan {files_synced} dosya listelendi"
            else:
                message = "Google kimlik doğrulaması başarısız"

        elif intg.type == models.IntegrationType.OFFICE365:
            from engines.cloud_scanner import Office365Scanner
            scanner = Office365Scanner(
                tenant_id=config.get("tenant_id", ""),
                client_id=config.get("client_id", ""),
                client_secret=config.get("client_secret", "")
            )
            if scanner.authenticate():
                files = scanner.list_onedrive_files()
                files_synced = len(files)
                message = f"OneDrive'dan {files_synced} dosya listelendi"
            else:
                message = "Microsoft kimlik doğrulaması başarısız"

        intg.last_sync = datetime.utcnow()
        intg.last_sync_status = "success" if files_synced > 0 or "listelendi" in message else "warning"
        intg.last_sync_message = message or f"{files_synced} öğe senkronize edildi"
        db.commit()

    except Exception as e:
        try:
            intg = db.query(models.Integration).filter(
                models.Integration.id == integration_id
            ).first()
            if intg:
                intg.last_sync = datetime.utcnow()
                intg.last_sync_status = "failed"
                intg.last_sync_message = f"Hata: {str(e)}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
