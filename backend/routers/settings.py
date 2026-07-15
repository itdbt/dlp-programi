"""
DLP Sistemi - Sistem Ayarları Yönlendiricisi
Sistem geneli ayarlar, denetim logları ve yedekleme endpoint'leri
"""

import json
import io
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log

router = APIRouter(prefix="/settings", tags=["Sistem Ayarları"])


# ==========================================
# Sistem Ayarları
# ==========================================

@router.get("")
async def get_all_settings(
    category: Optional[str] = None,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Tüm sistem ayarlarını listele (Sadece Yönetici)"""
    query = db.query(models.SystemSetting)

    if category:
        query = query.filter(models.SystemSetting.category == category)

    settings = query.order_by(models.SystemSetting.category, models.SystemSetting.key).all()

    # Hassas ayarları maskele
    result = []
    for setting in settings:
        value = setting.value
        if setting.is_sensitive and value:
            value = "***gizlendi***"

        result.append(schemas.SystemSettingResponse(
            id=setting.id,
            key=setting.key,
            value=value,
            description=setting.description,
            category=setting.category,
            is_sensitive=setting.is_sensitive,
            updated_at=setting.updated_at,
        ))

    return {
        "items": result,
        "total": len(result),
        "categories": list(set(s.category for s in settings if s.category)),
    }


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Belirli bir sistem ayarını döndür"""
    setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == key
    ).first()

    if not setting:
        raise HTTPException(
            status_code=404,
            detail=f"'{key}' anahtarlı ayar bulunamadı"
        )

    value = setting.value
    if setting.is_sensitive and value:
        value = "***gizlendi***"

    return schemas.SystemSettingResponse(
        id=setting.id,
        key=setting.key,
        value=value,
        description=setting.description,
        category=setting.category,
        is_sensitive=setting.is_sensitive,
        updated_at=setting.updated_at,
    )


@router.put("/{key}")
async def update_setting(
    key: str,
    update_data: schemas.SystemSettingUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Sistem ayarını güncelle"""
    setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == key
    ).first()

    if not setting:
        # Ayar yoksa oluştur
        setting = models.SystemSetting(
            key=key,
            value=update_data.value,
            description=update_data.description,
        )
        db.add(setting)
        action = "settings.created"
    else:
        old_value = "***" if setting.is_sensitive else setting.value
        setting.value = update_data.value
        if update_data.description is not None:
            setting.description = update_data.description
        setting.updated_at = datetime.utcnow()
        action = "settings.updated"

    db.commit()
    db.refresh(setting)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action=action,
        resource_type="system_setting",
        resource_id=setting.id,
        details={
            "key": key,
            "old_value": "***" if setting.is_sensitive else "değişti",
        },
        ip_address=request.client.host if request.client else None,
    )

    value = setting.value
    if setting.is_sensitive and value:
        value = "***gizlendi***"

    return schemas.SystemSettingResponse(
        id=setting.id,
        key=setting.key,
        value=value,
        description=setting.description,
        category=setting.category,
        is_sensitive=setting.is_sensitive,
        updated_at=setting.updated_at,
    )


@router.post("/bulk-update")
async def bulk_update_settings(
    bulk_data: schemas.BulkSettingUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Birden fazla ayarı aynı anda güncelle"""
    updated = []
    errors = []

    for key, value in bulk_data.settings.items():
        try:
            setting = db.query(models.SystemSetting).filter(
                models.SystemSetting.key == key
            ).first()

            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                setting = models.SystemSetting(key=key, value=value)
                db.add(setting)

            updated.append(key)
        except Exception as e:
            errors.append({"key": key, "error": str(e)})

    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="settings.bulk_updated",
        resource_type="system_setting",
        details={"updated_keys": updated},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "updated": updated,
        "errors": errors,
        "total_updated": len(updated),
    }


# ==========================================
# Denetim Logları
# ==========================================

@router.get("/audit/logs")
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Denetim loglarını listele"""
    query = db.query(models.AuditLog)

    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if action:
        query = query.filter(models.AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(models.AuditLog.resource_type == resource_type)
    if date_from:
        query = query.filter(models.AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(models.AuditLog.created_at <= date_to)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(
        models.AuditLog.created_at.desc()
    ).offset(offset).limit(page_size).all()

    log_responses = []
    for log in logs:
        user_data = None
        if log.user:
            user_data = schemas.UserResponse(
                id=log.user.id,
                email=log.user.email,
                full_name=log.user.full_name,
                role=log.user.role,
                is_active=log.user.is_active,
                created_at=log.user.created_at,
                last_login=log.user.last_login,
            )

        log_responses.append(schemas.AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details or {},
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
            user=user_data,
        ))

    return schemas.AuditLogListResponse(
        items=log_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/audit/actions")
async def list_audit_actions(
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Kayıtlı tüm benzersiz denetim eylemlerini listele"""
    from sqlalchemy import distinct
    actions = db.query(distinct(models.AuditLog.action)).order_by(
        models.AuditLog.action
    ).all()
    return {"actions": [row[0] for row in actions]}


# ==========================================
# Sistem Yedekleme
# ==========================================

@router.get("/backup/export")
async def export_system_backup(
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Sistem verilerinin tam yedeğini JSON olarak indir.
    Politikaları, ayarları ve bildirim kurallarını içerir.
    (Hassas veriler ve olaylar dahil değil)
    """
    # Politikalar
    policies = db.query(models.Policy).all()
    policy_data = [
        {
            "name": p.name,
            "description": p.description,
            "is_active": p.is_active,
            "severity": p.severity,
            "data_types": p.data_types,
            "actions": p.actions,
            "file_types": p.file_types,
            "cloud_sources": p.cloud_sources,
        }
        for p in policies
    ]

    # Sistem ayarları (hassas olanlar hariç)
    settings = db.query(models.SystemSetting).filter(
        models.SystemSetting.is_sensitive == False
    ).all()
    settings_data = [
        {
            "key": s.key,
            "value": s.value,
            "description": s.description,
            "category": s.category,
        }
        for s in settings
    ]

    # Bildirim kuralları
    rules = db.query(models.NotificationRule).all()
    rules_data = [
        {
            "name": r.name,
            "description": r.description,
            "events": r.events,
            "channels": r.channels,
            "recipients": r.recipients,
            "filters": r.filters,
            "is_active": r.is_active,
        }
        for r in rules
    ]

    backup_data = {
        "backup_date": datetime.utcnow().isoformat(),
        "system": "DLP Güvenlik Sistemi",
        "version": "1.0.0",
        "policies": policy_data,
        "settings": settings_data,
        "notification_rules": rules_data,
    }

    content = json.dumps(backup_data, ensure_ascii=False, indent=2)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="system.backup_exported",
        resource_type="system",
        details={
            "policies": len(policy_data),
            "settings": len(settings_data),
            "rules": len(rules_data),
        },
    )

    return Response(
        content=content.encode("utf-8"),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=dlp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


@router.get("/system/info")
async def get_system_info(
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Sistem bilgileri ve istatistiklerini döndür"""
    import platform
    from sqlalchemy import func

    # Veritabanı boyutu
    import os
    db_size = 0
    db_url = os.getenv("DATABASE_URL", "sqlite:///./dlp_database.db")
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite:///./", "").replace("sqlite:///", "")
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)

    return {
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()}",
        "database": {
            "type": "SQLite" if "sqlite" in db_url else "PostgreSQL",
            "size_mb": round(db_size / (1024 * 1024), 2),
        },
        "statistics": {
            "total_users": db.query(func.count(models.User.id)).scalar() or 0,
            "total_policies": db.query(func.count(models.Policy.id)).scalar() or 0,
            "total_incidents": db.query(func.count(models.Incident.id)).scalar() or 0,
            "total_scans": db.query(func.count(models.ScanJob.id)).scalar() or 0,
            "total_audit_logs": db.query(func.count(models.AuditLog.id)).scalar() or 0,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
