"""
DLP Sistemi - Pydantic v2 Şemaları
API istek/yanıt modelleri ve doğrulama kuralları
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
from models import (
    UserRole, PolicySeverity, IncidentSeverity, IncidentStatus,
    ScanType, ScanStatus, IntegrationType, NotificationChannel
)


# ==========================================
# Temel Şema Sınıfları
# ==========================================

class BaseSchema(BaseModel):
    """ORM uyumlu temel şema"""
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Sayfalandırılmış liste yanıtı"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Token Şemaları
# ==========================================

class Token(BaseModel):
    """JWT token yanıtı"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[Dict[str, Any]] = None


class TokenData(BaseModel):
    """Token içinden çıkarılan kullanıcı verisi"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Giriş isteği"""
    email: EmailStr
    password: str


# ==========================================
# Kullanıcı Şemaları
# ==========================================

class UserBase(BaseSchema):
    """Kullanıcı temel alanları"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserCreate(BaseSchema):
    """Yeni kullanıcı oluşturma"""
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır")
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")
        if not any(c.islower() for c in v):
            raise ValueError("Şifre en az bir küçük harf içermelidir")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az bir rakam içermelidir")
        return v


class UserUpdate(BaseSchema):
    """Kullanıcı güncelleme"""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseSchema):
    """Kullanıcı yanıtı (şifre hariç)"""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Kullanıcı listesi yanıtı"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChangePasswordRequest(BaseModel):
    """Şifre değiştirme isteği"""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Yeni şifre en az 8 karakter olmalıdır")
        if not any(c.isupper() for c in v):
            raise ValueError("Yeni şifre en az bir büyük harf içermelidir")
        if not any(c.islower() for c in v):
            raise ValueError("Yeni şifre en az bir küçük harf içermelidir")
        if not any(c.isdigit() for c in v):
            raise ValueError("Yeni şifre en az bir rakam içermelidir")
        return v


# ==========================================
# Politika Şemaları
# ==========================================

class PolicyBase(BaseSchema):
    """Politika temel alanları"""
    name: str
    description: Optional[str] = None
    is_active: bool = True
    severity: PolicySeverity = PolicySeverity.MEDIUM
    data_types: List[str] = []
    actions: List[str] = []
    file_types: List[str] = []
    cloud_sources: List[str] = []


class PolicyCreate(PolicyBase):
    """Yeni politika oluşturma"""
    pass


class PolicyUpdate(BaseSchema):
    """Politika güncelleme"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    severity: Optional[PolicySeverity] = None
    data_types: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    cloud_sources: Optional[List[str]] = None


class PolicyResponse(PolicyBase):
    """Politika yanıtı"""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    incident_count: Optional[int] = None


class PolicyListResponse(BaseModel):
    """Politika listesi yanıtı"""
    items: List[PolicyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# Olay Şemaları
# ==========================================

class PatternMatchSchema(BaseModel):
    """Tespit edilen örüntü"""
    pattern_key: str
    pattern_name: str
    matched_text: str
    risk_score: int
    category: str
    line_number: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentBase(BaseSchema):
    """Olay temel alanları"""
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    policy_id: Optional[int] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    cloud_source: Optional[str] = None
    source_url: Optional[str] = None
    detected_patterns: List[Dict[str, Any]] = []
    risk_score: int = 0
    assignee_id: Optional[int] = None


class IncidentCreate(IncidentBase):
    """Yeni olay oluşturma"""
    pass


class IncidentUpdate(BaseSchema):
    """Olay güncelleme"""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assignee_id: Optional[int] = None
    resolved_at: Optional[datetime] = None


class IncidentResponse(IncidentBase):
    """Olay yanıtı"""
    id: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None
    policy: Optional[PolicyResponse] = None
    comment_count: Optional[int] = None


class IncidentListResponse(BaseModel):
    """Olay listesi yanıtı"""
    items: List[IncidentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# Olay Yorumu Şemaları
# ==========================================

class CommentCreate(BaseModel):
    """Yorum oluşturma"""
    comment: str


class CommentResponse(BaseSchema):
    """Yorum yanıtı"""
    id: int
    incident_id: int
    user_id: int
    comment: str
    created_at: datetime
    user: Optional[UserResponse] = None


# ==========================================
# Tarama Şemaları
# ==========================================

class ScanJobCreate(BaseSchema):
    """Tarama işi oluşturma"""
    name: str
    scan_type: ScanType
    target_path: Optional[str] = None
    policy_ids: List[int] = []
    pattern_keys: List[str] = []


class ScanJobUpdate(BaseSchema):
    """Tarama işi güncelleme"""
    status: Optional[ScanStatus] = None
    total_files: Optional[int] = None
    scanned_files: Optional[int] = None
    incidents_found: Optional[int] = None
    error_message: Optional[str] = None


class ScanJobResponse(BaseSchema):
    """Tarama işi yanıtı"""
    id: int
    name: str
    scan_type: ScanType
    target_path: Optional[str] = None
    status: ScanStatus
    total_files: int
    scanned_files: int
    incidents_found: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    error_message: Optional[str] = None
    policy_ids: List[int] = []
    pattern_keys: List[str] = []
    progress_percent: Optional[float] = None
    creator: Optional[UserResponse] = None


class ScanJobListResponse(BaseModel):
    """Tarama işi listesi yanıtı"""
    items: List[ScanJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScanResultResponse(BaseSchema):
    """Tarama sonucu yanıtı"""
    id: int
    scan_job_id: int
    file_path: Optional[str] = None
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    detected_patterns: List[Dict[str, Any]] = []
    risk_score: int
    incident_id: Optional[int] = None
    scanned_at: datetime
    error_message: Optional[str] = None


class ScanResultListResponse(BaseModel):
    """Tarama sonucu listesi yanıtı"""
    items: List[ScanResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScanRequest(BaseModel):
    """Tarama başlatma isteği"""
    name: str
    scan_type: ScanType
    target_path: Optional[str] = None
    policy_ids: List[int] = []
    pattern_keys: List[str] = []
    recursive: bool = True
    integration_id: Optional[int] = None


# ==========================================
# Entegrasyon Şemaları
# ==========================================

class IntegrationCreate(BaseSchema):
    """Entegrasyon oluşturma"""
    name: str
    type: IntegrationType
    config: Dict[str, Any] = {}
    is_active: bool = True


class IntegrationUpdate(BaseSchema):
    """Entegrasyon güncelleme"""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationResponse(BaseSchema):
    """Entegrasyon yanıtı"""
    id: int
    name: str
    type: IntegrationType
    config: Dict[str, Any] = {}
    is_active: bool
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_message: Optional[str] = None
    created_at: datetime


class IntegrationListResponse(BaseModel):
    """Entegrasyon listesi yanıtı"""
    items: List[IntegrationResponse]
    total: int


# ==========================================
# Bildirim Şemaları
# ==========================================

class NotificationRuleCreate(BaseSchema):
    """Bildirim kuralı oluşturma"""
    name: str
    description: Optional[str] = None
    events: List[str] = []
    channels: List[str] = []
    recipients: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}
    is_active: bool = True


class NotificationRuleUpdate(BaseSchema):
    """Bildirim kuralı güncelleme"""
    name: Optional[str] = None
    description: Optional[str] = None
    events: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    recipients: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class NotificationRuleResponse(BaseSchema):
    """Bildirim kuralı yanıtı"""
    id: int
    name: str
    description: Optional[str] = None
    events: List[str] = []
    channels: List[str] = []
    recipients: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}
    is_active: bool
    created_at: datetime


class NotificationLogResponse(BaseSchema):
    """Bildirim logu yanıtı"""
    id: int
    rule_id: Optional[int] = None
    event_type: str
    recipient: str
    channel: str
    status: str
    message: Optional[str] = None
    error_detail: Optional[str] = None
    sent_at: datetime


class NotificationLogListResponse(BaseModel):
    """Bildirim logu listesi"""
    items: List[NotificationLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestNotificationRequest(BaseModel):
    """Test bildirimi gönderme isteği"""
    recipient: str
    channel: str = "email"
    message: Optional[str] = None


# ==========================================
# Sistem Ayarları Şemaları
# ==========================================

class SystemSettingResponse(BaseSchema):
    """Sistem ayarı yanıtı"""
    id: int
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_sensitive: bool = False
    updated_at: datetime


class SystemSettingUpdate(BaseModel):
    """Sistem ayarı güncelleme"""
    value: Optional[str] = None
    description: Optional[str] = None


class BulkSettingUpdate(BaseModel):
    """Toplu ayar güncelleme"""
    settings: Dict[str, str]


# ==========================================
# Denetim Logu Şemaları
# ==========================================

class AuditLogResponse(BaseSchema):
    """Denetim logu yanıtı"""
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None


class AuditLogListResponse(BaseModel):
    """Denetim logu listesi"""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# Dashboard Şemaları
# ==========================================

class DashboardStats(BaseModel):
    """Dashboard istatistikleri"""
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    high_incidents: int
    medium_incidents: int
    low_incidents: int
    total_policies: int
    active_policies: int
    total_scans: int
    running_scans: int
    recent_incidents: List[IncidentResponse] = []
    incidents_by_severity: Dict[str, int] = {}
    incidents_by_status: Dict[str, int] = {}
    incidents_trend: List[Dict[str, Any]] = []
    top_patterns: List[Dict[str, Any]] = []
    scan_stats: Dict[str, Any] = {}


class SystemHealth(BaseModel):
    """Sistem sağlık durumu"""
    status: str
    database: str
    scheduler: str
    disk_usage: Optional[Dict[str, Any]] = None
    memory_usage: Optional[Dict[str, Any]] = None
    uptime: Optional[str] = None
    version: str


# ==========================================
# Rapor Şemaları
# ==========================================

class ReportRequest(BaseModel):
    """Rapor oluşturma isteği"""
    report_type: str  # incidents, scans, policies, patterns
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Dict[str, Any] = {}
    format: str = "json"  # json, csv


class PatternInfo(BaseModel):
    """Örüntü bilgisi"""
    key: str
    name: str
    category: str
    risk_score: int
    description: str
