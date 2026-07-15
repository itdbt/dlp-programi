"""
DLP Sistemi - Politika Yönetimi Yönlendiricisi
DLP politikaları için tam CRUD ve yönetim endpoint'leri
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log

router = APIRouter(prefix="/policies", tags=["Politikalar"])


@router.get("", response_model=schemas.PolicyListResponse)
async def list_policies(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    severity: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Politikaları listele (filtreli ve sayfalandırılmış)"""
    query = db.query(models.Policy)

    if search:
        query = query.filter(
            models.Policy.name.ilike(f"%{search}%") |
            models.Policy.description.ilike(f"%{search}%")
        )

    if is_active is not None:
        query = query.filter(models.Policy.is_active == is_active)

    if severity:
        query = query.filter(models.Policy.severity == severity)

    total = query.count()
    offset = (page - 1) * page_size
    policies = query.order_by(models.Policy.created_at.desc()).offset(offset).limit(page_size).all()

    # Her politika için olay sayısını ekle
    policy_responses = []
    for policy in policies:
        incident_count = db.query(func.count(models.Incident.id)).filter(
            models.Incident.policy_id == policy.id
        ).scalar() or 0

        policy_dict = {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "is_active": policy.is_active,
            "severity": policy.severity,
            "data_types": policy.data_types or [],
            "actions": policy.actions or [],
            "file_types": policy.file_types or [],
            "cloud_sources": policy.cloud_sources or [],
            "created_at": policy.created_at,
            "updated_at": policy.updated_at,
            "created_by": policy.created_by,
            "incident_count": incident_count,
        }
        policy_responses.append(schemas.PolicyResponse(**policy_dict))

    return schemas.PolicyListResponse(
        items=policy_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("", response_model=schemas.PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: schemas.PolicyCreate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Yeni DLP politikası oluştur"""
    # İsim benzersizliğini kontrol et
    existing = db.query(models.Policy).filter(
        models.Policy.name == policy_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{policy_data.name}' adında bir politika zaten mevcut"
        )

    new_policy = models.Policy(
        name=policy_data.name,
        description=policy_data.description,
        is_active=policy_data.is_active,
        severity=policy_data.severity,
        data_types=policy_data.data_types,
        actions=policy_data.actions,
        file_types=policy_data.file_types,
        cloud_sources=policy_data.cloud_sources,
        created_by=current_user.id,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="policy.created",
        resource_type="policy",
        resource_id=new_policy.id,
        details={"name": new_policy.name, "severity": new_policy.severity},
        ip_address=request.client.host if request.client else None,
    )

    policy_dict = {
        "id": new_policy.id,
        "name": new_policy.name,
        "description": new_policy.description,
        "is_active": new_policy.is_active,
        "severity": new_policy.severity,
        "data_types": new_policy.data_types or [],
        "actions": new_policy.actions or [],
        "file_types": new_policy.file_types or [],
        "cloud_sources": new_policy.cloud_sources or [],
        "created_at": new_policy.created_at,
        "updated_at": new_policy.updated_at,
        "created_by": new_policy.created_by,
        "incident_count": 0,
    }
    return schemas.PolicyResponse(**policy_dict)


@router.get("/{policy_id}", response_model=schemas.PolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Belirli bir politikanın detayını döndür"""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{policy_id} ID'li politika bulunamadı"
        )

    incident_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.policy_id == policy_id
    ).scalar() or 0

    policy_dict = {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "is_active": policy.is_active,
        "severity": policy.severity,
        "data_types": policy.data_types or [],
        "actions": policy.actions or [],
        "file_types": policy.file_types or [],
        "cloud_sources": policy.cloud_sources or [],
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
        "created_by": policy.created_by,
        "incident_count": incident_count,
    }
    return schemas.PolicyResponse(**policy_dict)


@router.put("/{policy_id}", response_model=schemas.PolicyResponse)
async def update_policy(
    policy_id: int,
    update_data: schemas.PolicyUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Politikayı güncelle"""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{policy_id} ID'li politika bulunamadı"
        )

    changes = {}
    update_fields = update_data.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        old_value = getattr(policy, field)
        if old_value != value:
            changes[field] = {"eski": old_value, "yeni": value}
            setattr(policy, field, value)

    policy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(policy)

    if changes:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="policy.updated",
            resource_type="policy",
            resource_id=policy_id,
            details=changes,
            ip_address=request.client.host if request.client else None,
        )

    incident_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.policy_id == policy_id
    ).scalar() or 0

    policy_dict = {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "is_active": policy.is_active,
        "severity": policy.severity,
        "data_types": policy.data_types or [],
        "actions": policy.actions or [],
        "file_types": policy.file_types or [],
        "cloud_sources": policy.cloud_sources or [],
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
        "created_by": policy.created_by,
        "incident_count": incident_count,
    }
    return schemas.PolicyResponse(**policy_dict)


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Politikayı sil (Sadece Yönetici)"""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{policy_id} ID'li politika bulunamadı"
        )

    # İlişkili olayları kontrol et
    incident_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.policy_id == policy_id
    ).scalar() or 0

    if incident_count > 0:
        # Politikayı silmek yerine sadece deaktive et
        policy.is_active = False
        policy.updated_at = datetime.utcnow()
        db.commit()

        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="policy.deactivated",
            resource_type="policy",
            resource_id=policy_id,
            details={"reason": "İlişkili olaylar mevcut, silme yerine deaktive edildi"},
            ip_address=request.client.host if request.client else None,
        )

        return {
            "message": f"Politika '{policy.name}' deaktive edildi (silme yerine). "
                       f"{incident_count} adet ilişkili olay bulunduğundan tam silinmedi.",
            "deactivated": True
        }

    name = policy.name
    db.delete(policy)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="policy.deleted",
        resource_type="policy",
        resource_id=policy_id,
        details={"name": name},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Politika '{name}' başarıyla silindi"}


@router.post("/{policy_id}/toggle")
async def toggle_policy(
    policy_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Politikayı etkinleştir/deaktive et"""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{policy_id} ID'li politika bulunamadı"
        )

    policy.is_active = not policy.is_active
    policy.updated_at = datetime.utcnow()
    db.commit()

    action = "etkinleştirildi" if policy.is_active else "deaktive edildi"

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action=f"policy.{'activated' if policy.is_active else 'deactivated'}",
        resource_type="policy",
        resource_id=policy_id,
        details={"name": policy.name, "is_active": policy.is_active},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": f"Politika '{policy.name}' {action}",
        "is_active": policy.is_active
    }


@router.get("/{policy_id}/incidents")
async def get_policy_incidents(
    policy_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bir politikanın ilişkili olaylarını listele"""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{policy_id} ID'li politika bulunamadı"
        )

    query = db.query(models.Incident).filter(
        models.Incident.policy_id == policy_id
    )

    total = query.count()
    offset = (page - 1) * page_size
    incidents = query.order_by(
        models.Incident.created_at.desc()
    ).offset(offset).limit(page_size).all()

    return {
        "policy_id": policy_id,
        "policy_name": policy.name,
        "items": [
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "risk_score": i.risk_score,
                "file_name": i.file_name,
                "created_at": i.created_at,
            }
            for i in incidents
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
