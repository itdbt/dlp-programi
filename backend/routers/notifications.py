"""
DLP Sistemi - Bildirim Kuralları Yönlendiricisi
Bildirim kuralları, loglar ve test endpoint'leri
"""

import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log
from engines.email_notifier import EmailNotifier

router = APIRouter(prefix="/notifications", tags=["Bildirimler"])


def _get_email_notifier() -> Optional[EmailNotifier]:
    """SMTP yapılandırmasından EmailNotifier oluştur"""
    host = os.getenv("SMTP_HOST", "")
    if not host:
        return None

    return EmailNotifier(
        smtp_host=host,
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from=os.getenv("SMTP_FROM", "DLP Sistemi <noreply@dlp.local>"),
        use_tls=os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    )


# ==========================================
# Bildirim Kuralları
# ==========================================

@router.get("/rules")
async def list_notification_rules(
    page: int = 1,
    page_size: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bildirim kurallarını listele"""
    query = db.query(models.NotificationRule)
    total = query.count()
    offset = (page - 1) * page_size
    rules = query.order_by(
        models.NotificationRule.created_at.desc()
    ).offset(offset).limit(page_size).all()

    return {
        "items": [
            schemas.NotificationRuleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                events=r.events or [],
                channels=r.channels or [],
                recipients=r.recipients or {},
                filters=r.filters or {},
                is_active=r.is_active,
                created_at=r.created_at,
            )
            for r in rules
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/rules", response_model=schemas.NotificationRuleResponse, status_code=201)
async def create_notification_rule(
    rule_data: schemas.NotificationRuleCreate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Yeni bildirim kuralı oluştur"""
    # Geçerli olayları doğrula
    valid_events = [
        "incident_created", "incident_updated", "incident_resolved",
        "scan_completed", "scan_failed", "policy_violation",
        "high_risk_detected", "critical_detected"
    ]

    for event in rule_data.events:
        if event not in valid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz olay tipi: '{event}'. Geçerli değerler: {', '.join(valid_events)}"
            )

    valid_channels = ["email", "webhook", "slack", "teams"]
    for channel in rule_data.channels:
        if channel not in valid_channels:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz kanal: '{channel}'. Geçerli değerler: {', '.join(valid_channels)}"
            )

    new_rule = models.NotificationRule(
        name=rule_data.name,
        description=rule_data.description,
        events=rule_data.events,
        channels=rule_data.channels,
        recipients=rule_data.recipients,
        filters=rule_data.filters,
        is_active=rule_data.is_active,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="notification_rule.created",
        resource_type="notification_rule",
        resource_id=new_rule.id,
        details={"name": new_rule.name, "events": new_rule.events},
        ip_address=request.client.host if request.client else None,
    )

    return schemas.NotificationRuleResponse(
        id=new_rule.id,
        name=new_rule.name,
        description=new_rule.description,
        events=new_rule.events or [],
        channels=new_rule.channels or [],
        recipients=new_rule.recipients or {},
        filters=new_rule.filters or {},
        is_active=new_rule.is_active,
        created_at=new_rule.created_at,
    )


@router.get("/rules/{rule_id}", response_model=schemas.NotificationRuleResponse)
async def get_notification_rule(
    rule_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Belirli bir bildirim kuralının detayını döndür"""
    rule = db.query(models.NotificationRule).filter(
        models.NotificationRule.id == rule_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"#{rule_id} ID'li bildirim kuralı bulunamadı"
        )

    return schemas.NotificationRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        events=rule.events or [],
        channels=rule.channels or [],
        recipients=rule.recipients or {},
        filters=rule.filters or {},
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.put("/rules/{rule_id}", response_model=schemas.NotificationRuleResponse)
async def update_notification_rule(
    rule_id: int,
    update_data: schemas.NotificationRuleUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Bildirim kuralını güncelle"""
    rule = db.query(models.NotificationRule).filter(
        models.NotificationRule.id == rule_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"#{rule_id} ID'li bildirim kuralı bulunamadı"
        )

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="notification_rule.updated",
        resource_type="notification_rule",
        resource_id=rule_id,
        details={"name": rule.name},
        ip_address=request.client.host if request.client else None,
    )

    return schemas.NotificationRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        events=rule.events or [],
        channels=rule.channels or [],
        recipients=rule.recipients or {},
        filters=rule.filters or {},
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.delete("/rules/{rule_id}")
async def delete_notification_rule(
    rule_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Bildirim kuralını sil"""
    rule = db.query(models.NotificationRule).filter(
        models.NotificationRule.id == rule_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"#{rule_id} ID'li bildirim kuralı bulunamadı"
        )

    name = rule.name
    db.delete(rule)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="notification_rule.deleted",
        resource_type="notification_rule",
        resource_id=rule_id,
        details={"name": name},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Bildirim kuralı '{name}' silindi"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_notification_rule(
    rule_id: int,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Bildirim kuralını etkinleştir/deaktive et"""
    rule = db.query(models.NotificationRule).filter(
        models.NotificationRule.id == rule_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"#{rule_id} ID'li bildirim kuralı bulunamadı"
        )

    rule.is_active = not rule.is_active
    db.commit()

    return {
        "message": f"Kural {'etkinleştirildi' if rule.is_active else 'deaktive edildi'}",
        "is_active": rule.is_active
    }


# ==========================================
# Test Bildirimi
# ==========================================

@router.post("/test")
async def send_test_notification(
    test_request: schemas.TestNotificationRequest,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Test bildirimi gönder"""
    if test_request.channel == "email":
        notifier = _get_email_notifier()
        if not notifier:
            raise HTTPException(
                status_code=503,
                detail="E-posta sunucusu yapılandırılmamış. .env dosyasını kontrol edin."
            )

        success = await notifier.send_test_email(test_request.recipient)

        # Log kaydet
        log = models.NotificationLog(
            event_type="test",
            recipient=test_request.recipient,
            channel="email",
            status="success" if success else "failed",
            message="Test e-postası gönderildi" if success else "Test e-postası gönderilemedi",
        )
        db.add(log)
        db.commit()

        return {
            "success": success,
            "channel": "email",
            "recipient": test_request.recipient,
            "message": "Test e-postası gönderildi" if success else "E-posta gönderilemedi. Log dosyasını kontrol edin."
        }

    elif test_request.channel == "webhook":
        from engines.email_notifier import WebhookNotifier
        notifier = WebhookNotifier()
        success = notifier.send(
            url=test_request.recipient,
            payload={
                "event": "test",
                "message": test_request.message or "DLP Sistemi test mesajı",
                "source": "DLP Güvenlik Sistemi"
            }
        )

        return {
            "success": success,
            "channel": "webhook",
            "recipient": test_request.recipient,
            "message": "Webhook gönderildi" if success else "Webhook gönderilemedi"
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen bildirim kanalı: {test_request.channel}"
        )


# ==========================================
# Bildirim Logları
# ==========================================

@router.get("/logs")
async def list_notification_logs(
    page: int = 1,
    page_size: int = 50,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bildirim loglarını listele"""
    query = db.query(models.NotificationLog)

    if channel:
        query = query.filter(models.NotificationLog.channel == channel)
    if status:
        query = query.filter(models.NotificationLog.status == status)
    if event_type:
        query = query.filter(models.NotificationLog.event_type == event_type)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(
        models.NotificationLog.sent_at.desc()
    ).offset(offset).limit(page_size).all()

    return {
        "items": [
            schemas.NotificationLogResponse(
                id=log.id,
                rule_id=log.rule_id,
                event_type=log.event_type,
                recipient=log.recipient,
                channel=log.channel,
                status=log.status,
                message=log.message,
                error_detail=log.error_detail,
                sent_at=log.sent_at,
            )
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/logs/stats")
async def get_notification_stats(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bildirim istatistikleri"""
    from sqlalchemy import func

    total = db.query(func.count(models.NotificationLog.id)).scalar() or 0
    success = db.query(func.count(models.NotificationLog.id)).filter(
        models.NotificationLog.status == "success"
    ).scalar() or 0
    failed = db.query(func.count(models.NotificationLog.id)).filter(
        models.NotificationLog.status == "failed"
    ).scalar() or 0

    by_channel = db.query(
        models.NotificationLog.channel,
        func.count(models.NotificationLog.id).label("count")
    ).group_by(models.NotificationLog.channel).all()

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round((success / total * 100), 1) if total > 0 else 0,
        "by_channel": {row.channel: row.count for row in by_channel},
        "active_rules": db.query(func.count(models.NotificationRule.id)).filter(
            models.NotificationRule.is_active == True
        ).scalar() or 0,
    }


@router.get("/events/types")
async def list_event_types(
    current_user: models.User = Depends(get_current_active_user)
):
    """Kullanılabilir olay tiplerini listele"""
    return {
        "events": [
            {"key": "incident_created", "name": "Olay Oluşturuldu", "description": "Yeni bir güvenlik olayı tespit edildiğinde"},
            {"key": "incident_updated", "name": "Olay Güncellendi", "description": "Mevcut bir olay güncellendiğinde"},
            {"key": "incident_resolved", "name": "Olay Çözüldü", "description": "Bir olay çözüldüğünde veya kapatıldığında"},
            {"key": "scan_completed", "name": "Tarama Tamamlandı", "description": "Bir tarama işi tamamlandığında"},
            {"key": "scan_failed", "name": "Tarama Başarısız", "description": "Bir tarama işi hata ile sonlandığında"},
            {"key": "policy_violation", "name": "Politika İhlali", "description": "Bir DLP politikası ihlal edildiğinde"},
            {"key": "high_risk_detected", "name": "Yüksek Risk Tespit", "description": "Risk skoru 70+ olan içerik tespit edildiğinde"},
            {"key": "critical_detected", "name": "Kritik Tespit", "description": "Risk skoru 85+ olan içerik tespit edildiğinde"},
        ]
    }
