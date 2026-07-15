"""
DLP Sistemi - Kimlik Doğrulama Yönlendiricisi
Giriş, kullanıcı yönetimi ve profil endpoint'leri
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
    require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_audit_log
)

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


# ==========================================
# Giriş Yapma
# ==========================================

@router.post("/login", response_model=schemas.Token)
async def login(
    login_data: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    E-posta ve şifre ile giriş yap, JWT token döndür.
    """
    user = authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz e-posta veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı bırakılmış. Lütfen yöneticinizle iletişime geçin."
        )

    # Son giriş zamanını güncelle
    user.last_login = datetime.utcnow()
    db.commit()

    # Token oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        },
        expires_delta=access_token_expires
    )

    # Denetim logu
    create_audit_log(
        db=db,
        user_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        }
    )


# ==========================================
# Mevcut Kullanıcı Profili
# ==========================================

@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(
    current_user: models.User = Depends(get_current_active_user)
):
    """Giriş yapan kullanıcının profilini döndür"""
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_my_profile(
    update_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Giriş yapan kullanıcının profilini güncelle"""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    # Rol ve is_active sadece admin tarafından değiştirilebilir
    if update_data.role is not None and current_user.role == "admin":
        current_user.role = update_data.role

    db.commit()
    db.refresh(current_user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.profile_updated",
        resource_type="user",
        resource_id=current_user.id,
    )

    return current_user


@router.post("/change-password")
async def change_password(
    password_data: schemas.ChangePasswordRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mevcut kullanıcının şifresini değiştir"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre yanlış"
        )

    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre mevcut şifreyle aynı olamaz"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.password_changed",
        resource_type="user",
        resource_id=current_user.id,
    )

    return {"message": "Şifreniz başarıyla değiştirildi"}


# ==========================================
# Kullanıcı Yönetimi (Sadece Admin)
# ==========================================

@router.get("/users", response_model=schemas.UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Tüm kullanıcıları listele (Sadece Yönetici)"""
    query = db.query(models.User)

    if search:
        query = query.filter(
            models.User.email.ilike(f"%{search}%") |
            models.User.full_name.ilike(f"%{search}%")
        )

    if role:
        query = query.filter(models.User.role == role)

    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(models.User.created_at.desc()).offset(offset).limit(page_size).all()

    return schemas.UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: schemas.UserCreate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Yeni kullanıcı oluştur (Sadece Yönetici)"""
    # E-posta benzersizliğini kontrol et
    existing = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{user_data.email}' e-posta adresi zaten kullanımda"
        )

    new_user = models.User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.created",
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role},
        ip_address=request.client.host if request.client else None,
    )

    return new_user


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Belirli bir kullanıcının detayını döndür (Sadece Yönetici)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{user_id} ID'li kullanıcı bulunamadı"
        )
    return user


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    update_data: schemas.UserUpdate,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Kullanıcı bilgilerini güncelle (Sadece Yönetici)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{user_id} ID'li kullanıcı bulunamadı"
        )

    # Kendini deaktive etmeyi önle
    if user_id == current_user.id and update_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı devre dışı bırakamazsınız"
        )

    changes = {}
    if update_data.full_name is not None:
        changes["full_name"] = {"eski": user.full_name, "yeni": update_data.full_name}
        user.full_name = update_data.full_name
    if update_data.role is not None:
        changes["role"] = {"eski": user.role, "yeni": update_data.role}
        user.role = update_data.role
    if update_data.is_active is not None:
        changes["is_active"] = {"eski": user.is_active, "yeni": update_data.is_active}
        user.is_active = update_data.is_active

    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.updated",
        resource_type="user",
        resource_id=user_id,
        details=changes,
        ip_address=request.client.host if request.client else None,
    )

    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Kullanıcıyı sil (Sadece Yönetici)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı silemezsiniz"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"#{user_id} ID'li kullanıcı bulunamadı"
        )

    email = user.email
    db.delete(user)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.deleted",
        resource_type="user",
        resource_id=user_id,
        details={"email": email},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"'{email}' kullanıcısı başarıyla silindi"}
