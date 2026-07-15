"""
DLP Sistemi - Olay Yönetimi Yönlendiricisi
Güvenlik ihlali olayları için tam CRUD, durum yönetimi, atama ve yorumlar
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import get_db
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log

router = APIRouter(prefix="/incidents", tags=["Olaylar"])


def _build_incident_response(incident: models.Incident, db: Session) -> schemas.IncidentResponse:
    """Olay nesnesini response şemasına dönüştür"""
    comment_count = db.query(func.count(models.IncidentComment.id)).filter(
        models.IncidentComment.incident_id == incident.id
    ).scalar() or 0

    policy_data = None
    if incident.policy:
        policy_data = schemas.PolicyResponse(
            id=incident.policy.id,
            name=incident.policy.name,
            description=incident.policy.description,
            is_active=incident.policy.is_active,
            severity=incident.policy.severity,
            data_types=incident.policy.data_types or [],
            actions=incident.policy.actions or [],
            file_types=incident.policy.file_types or [],
            cloud_sources=incident.policy.cloud_sources or [],
            created_at=incident.policy.created_at,
            updated_at=incident.policy.updated_at,
            created_by=incident.policy.created_by,
        )

    assignee_data = None
    if incident.assignee:
        assignee_data = schemas.UserResponse(
            id=incident.assignee.id,
            email=incident.assignee.email,
            full_name=incident.assignee.full_name,
            role=incident.assignee.role,
            is_active=incident.assignee.is_active,
            created_at=incident.assignee.created_at,
            last_login=incident.assignee.last_login,
        )

    return schemas.IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        policy_id=incident.policy_id,
        file_path=incident.file_path,
        file_name=incident.file_name,
        file_type=incident.file_type,
        file_size=incident.file_size,
        cloud_source=incident.cloud_source,
        source_url=incident.source_url,
        detected_patterns=incident.detected_patterns or [],
        risk_score=incident.risk_score,
        assignee_id=incident.assignee_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
        assignee=assignee_data,
        policy=policy_data,
        comment_count=comment_count,
    )


@router.get("", response_model=schemas.IncidentListResponse)
async def list_incidents(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    policy_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    cloud_source: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Güvenlik olaylarını filtreli ve sayfalandırılmış listele"""
    query = db.query(models.Incident)

    if search:
        query = query.filter(
            models.Incident.title.ilike(f"%{search}%") |
            models.Incident.description.ilike(f"%{search}%") |
            models.Incident.file_name.ilike(f"%{search}%")
        )

    if severity:
        query = query.filter(models.Incident.severity == severity)

    if status:
        query = query.filter(models.Incident.status == status)

    if policy_id:
        query = query.filter(models.Incident.policy_id == policy_id)

    if assignee_id:
        query = query.filter(models.Incident.assignee_id == assignee_id)

    if cloud_source:
        query = query.filter(models.Incident.cloud_source == cloud_source)

    if date_from:
        query = query.filter(models.Incident.created_at >= date_from)

    if date_to:
        query = query.filter(models.Incident.created_at <= date_to)

    # Sıralama
    sort_column = getattr(models.Incident, sort_by, models.Incident.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()
    offset = (page - 1) * page_size
    incidents = query.offset(offset).limit(page_size).all()

    incident_responses = [_build_incident_response(inc, db) for inc in incidents]

    return schemas.IncidentListResponse(
        items=incident_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("", response_model=schemas.IncidentResponse, status_code=201)
async def create_incident(
    incident_data: schemas.IncidentCreate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Yeni güvenlik olayı oluştur"""
    # Politika varlığını kontrol et
    if incident_data.policy_id:
        policy = db.query(models.Policy).filter(
            models.Policy.id == incident_data.policy_id
        ).first()
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"#{incident_data.policy_id} ID'li politika bulunamadı"
            )

    new_incident = models.Incident(
        title=incident_data.title,
        description=incident_data.description,
        severity=incident_data.severity,
        status=incident_data.status,
        policy_id=incident_data.policy_id,
        file_path=incident_data.file_path,
        file_name=incident_data.file_name,
        file_type=incident_data.file_type,
        file_size=incident_data.file_size,
        cloud_source=incident_data.cloud_source,
        source_url=incident_data.source_url,
        detected_patterns=incident_data.detected_patterns,
        risk_score=incident_data.risk_score,
        assignee_id=incident_data.assignee_id,
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="incident.created",
        resource_type="incident",
        resource_id=new_incident.id,
        details={"title": new_incident.title, "severity": new_incident.severity},
        ip_address=request.client.host if request.client else None,
    )

    return _build_incident_response(new_incident, db)


@router.get("/stats")
async def get_incident_stats(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Olay istatistiklerini döndür"""
    total = db.query(func.count(models.Incident.id)).scalar() or 0

    by_severity = {}
    for sev in ["critical", "high", "medium", "low"]:
        count = db.query(func.count(models.Incident.id)).filter(
            models.Incident.severity == sev
        ).scalar() or 0
        by_severity[sev] = count

    by_status = {}
    for st in ["open", "investigating", "resolved", "false_positive", "closed"]:
        count = db.query(func.count(models.Incident.id)).filter(
            models.Incident.status == st
        ).scalar() or 0
        by_status[st] = count

    avg_risk = db.query(func.avg(models.Incident.risk_score)).scalar() or 0

    return {
        "total": total,
        "by_severity": by_severity,
        "by_status": by_status,
        "average_risk_score": round(float(avg_risk), 1),
        "unassigned": db.query(func.count(models.Incident.id)).filter(
            models.Incident.assignee_id == None,
            models.Incident.status == models.IncidentStatus.OPEN
        ).scalar() or 0,
    }


@router.get("/{incident_id}", response_model=schemas.IncidentResponse)
async def get_incident(
    incident_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Belirli bir olayın detayını döndür"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    return _build_incident_response(incident, db)


@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
async def update_incident(
    incident_id: int,
    update_data: schemas.IncidentUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Olay bilgilerini güncelle"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    changes = {}
    update_fields = update_data.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        old_value = getattr(incident, field)
        if str(old_value) != str(value):
            changes[field] = {"eski": str(old_value), "yeni": str(value)}
        setattr(incident, field, value)

    # Çözüldüyse tarih ekle
    if update_data.status in (models.IncidentStatus.RESOLVED, models.IncidentStatus.CLOSED):
        if not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()
            changes["resolved_at"] = {"eski": None, "yeni": incident.resolved_at.isoformat()}

    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)

    if changes:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="incident.updated",
            resource_type="incident",
            resource_id=incident_id,
            details=changes,
            ip_address=request.client.host if request.client else None,
        )

    return _build_incident_response(incident, db)


@router.delete("/{incident_id}")
async def delete_incident(
    incident_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Olayı sil (Sadece Yönetici)"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    title = incident.title
    db.delete(incident)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="incident.deleted",
        resource_type="incident",
        resource_id=incident_id,
        details={"title": title},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Olay '{title}' başarıyla silindi"}


@router.post("/{incident_id}/status")
async def update_incident_status(
    incident_id: int,
    new_status: str,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Olay durumunu güncelle"""
    valid_statuses = ["open", "investigating", "resolved", "false_positive", "closed"]

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz durum. Geçerli değerler: {', '.join(valid_statuses)}"
        )

    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    old_status = incident.status
    incident.status = new_status
    incident.updated_at = datetime.utcnow()

    if new_status in ("resolved", "closed") and not incident.resolved_at:
        incident.resolved_at = datetime.utcnow()

    db.commit()

    status_tr = {
        "open": "Açık",
        "investigating": "İnceleniyor",
        "resolved": "Çözüldü",
        "false_positive": "Yanlış Pozitif",
        "closed": "Kapatıldı"
    }

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="incident.status_changed",
        resource_type="incident",
        resource_id=incident_id,
        details={"eski_durum": str(old_status), "yeni_durum": new_status},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": f"Olay durumu '{status_tr.get(new_status, new_status)}' olarak güncellendi",
        "incident_id": incident_id,
        "old_status": str(old_status),
        "new_status": new_status,
    }


@router.post("/{incident_id}/assign")
async def assign_incident(
    incident_id: int,
    assignee_id: Optional[int],
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Olayı bir kullanıcıya ata"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    assignee_name = None
    if assignee_id:
        assignee = db.query(models.User).filter(models.User.id == assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail=f"#{assignee_id} ID'li kullanıcı bulunamadı"
            )
        assignee_name = assignee.full_name

    old_assignee_id = incident.assignee_id
    incident.assignee_id = assignee_id
    incident.updated_at = datetime.utcnow()
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="incident.assigned",
        resource_type="incident",
        resource_id=incident_id,
        details={
            "eski_atama": old_assignee_id,
            "yeni_atama": assignee_id,
            "atanan_kisi": assignee_name
        },
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": f"Olay {'bırakıldı' if not assignee_id else f'{assignee_name} kişisine atandı'}",
        "incident_id": incident_id,
        "assignee_id": assignee_id,
        "assignee_name": assignee_name,
    }


# ==========================================
# Olay Yorumları
# ==========================================

@router.get("/{incident_id}/comments", response_model=List[schemas.CommentResponse])
async def get_comments(
    incident_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bir olayın yorumlarını listele"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    comments = db.query(models.IncidentComment).filter(
        models.IncidentComment.incident_id == incident_id
    ).order_by(models.IncidentComment.created_at.asc()).all()

    result = []
    for comment in comments:
        user_data = None
        if comment.user:
            user_data = schemas.UserResponse(
                id=comment.user.id,
                email=comment.user.email,
                full_name=comment.user.full_name,
                role=comment.user.role,
                is_active=comment.user.is_active,
                created_at=comment.user.created_at,
                last_login=comment.user.last_login,
            )
        result.append(schemas.CommentResponse(
            id=comment.id,
            incident_id=comment.incident_id,
            user_id=comment.user_id,
            comment=comment.comment,
            created_at=comment.created_at,
            user=user_data,
        ))

    return result


@router.post("/{incident_id}/comments", response_model=schemas.CommentResponse, status_code=201)
async def add_comment(
    incident_id: int,
    comment_data: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Olaya yorum ekle"""
    incident = db.query(models.Incident).filter(
        models.Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"#{incident_id} ID'li olay bulunamadı"
        )

    if not comment_data.comment.strip():
        raise HTTPException(
            status_code=400,
            detail="Yorum boş olamaz"
        )

    new_comment = models.IncidentComment(
        incident_id=incident_id,
        user_id=current_user.id,
        comment=comment_data.comment.strip(),
    )
    db.add(new_comment)

    # Olayı güncelle
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(new_comment)

    return schemas.CommentResponse(
        id=new_comment.id,
        incident_id=new_comment.incident_id,
        user_id=new_comment.user_id,
        comment=new_comment.comment,
        created_at=new_comment.created_at,
        user=schemas.UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
        )
    )


@router.delete("/{incident_id}/comments/{comment_id}")
async def delete_comment(
    incident_id: int,
    comment_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Yorumu sil (kendi yorumu veya admin)"""
    comment = db.query(models.IncidentComment).filter(
        models.IncidentComment.id == comment_id,
        models.IncidentComment.incident_id == incident_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Yorum bulunamadı"
        )

    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Bu yorumu silme yetkiniz yok"
        )

    db.delete(comment)
    db.commit()

    return {"message": "Yorum başarıyla silindi"}
