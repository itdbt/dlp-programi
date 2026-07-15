"""
DLP Sistemi - JWT Kimlik Doğrulama Modülü
Token oluşturma, doğrulama ve yetki kontrol bağımlılıkları
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
import models
import schemas

load_dotenv()

# Güvenlik ayarları
SECRET_KEY = os.getenv("SECRET_KEY", "dlp-super-gizli-anahtar-degistirin-32-karakter-minimum")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Şifre hashleme context'i (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 şeması - /api/auth/login endpoint'ini token URL olarak gösterir
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ==========================================
# Şifre İşlemleri
# ==========================================

def get_password_hash(password: str) -> str:
    """Şifreyi bcrypt ile hashle"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Düz şifreyi hashlenmiş şifreyle karşılaştır"""
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# Token İşlemleri
# ==========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT access token oluştur.
    
    Args:
        data: Token içine eklenecek veri (genellikle kullanıcı ID ve email)
        expires_delta: Token geçerlilik süresi (varsayılan: .env'den alınır)
    
    Returns:
        Kodlanmış JWT token string'i
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> schemas.TokenData:
    """
    JWT token'ı doğrula ve içindeki veriyi çıkar.
    
    Args:
        token: Doğrulanacak JWT token
    
    Returns:
        TokenData nesnesi
    
    Raises:
        HTTPException: Token geçersiz veya süresi dolmuşsa
    """
    kimlik_dogrulama_hatasi = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama bilgileri geçersiz",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            raise kimlik_dogrulama_hatasi
        
        token_data = schemas.TokenData(
            user_id=int(user_id),
            email=email,
            role=role
        )
        return token_data
        
    except JWTError:
        raise kimlik_dogrulama_hatasi


# ==========================================
# FastAPI Bağımlılıkları
# ==========================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Geçerli giriş yapmış kullanıcıyı döndür.
    Her korumalı endpoint bu bağımlılığı kullanır.
    """
    kimlik_dogrulama_hatasi = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama bilgileri geçersiz",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    
    user = db.query(models.User).filter(
        models.User.id == token_data.user_id
    ).first()
    
    if user is None:
        raise kimlik_dogrulama_hatasi
    
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Aktif (deaktive edilmemiş) kullanıcıyı kontrol et"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı bırakılmış. Lütfen yöneticinizle iletişime geçin."
        )
    return current_user


def require_role(allowed_roles: List[str]):
    """
    Belirli rollere sahip kullanıcılar için bağımlılık fabrikası.
    
    Kullanım:
        @router.get("/admin-only")
        def admin_endpoint(user = Depends(require_role(["admin"]))):
            ...
    
    Args:
        allowed_roles: İzin verilen roller listesi (örn: ["admin", "analyst"])
    
    Returns:
        FastAPI bağımlılık fonksiyonu
    """
    async def role_checker(
        current_user: models.User = Depends(get_current_active_user)
    ) -> models.User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bu işlem için yetkiniz bulunmamaktadır. Gerekli roller: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    E-posta ve şifre ile kullanıcı doğrulama.
    
    Returns:
        Geçerli kullanıcı nesnesi veya None
    """
    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.is_active == True
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: dict = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Denetim logu oluştur"""
    audit = models.AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit)
    db.commit()
