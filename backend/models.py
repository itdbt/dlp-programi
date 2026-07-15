"""
DLP Sistemi - SQLAlchemy Veritabanı Modelleri
Tüm tablo yapıları ve ilişkileri tanımlar
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base
import enum


# ==========================================
# Enum Tanımları
# ==========================================

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class PolicySeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class ScanType(str, enum.Enum):
    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"
    GMAIL = "gmail"
    ONEDRIVE = "onedrive"
    SHAREPOINT = "sharepoint"
    OUTLOOK = "outlook"
    UPLOAD = "upload"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntegrationType(str, enum.Enum):
    GOOGLE_WORKSPACE = "google_workspace"
    OFFICE365 = "office365"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    SMTP = "smtp"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


# ==========================================
# Kullanıcı Modeli
# ==========================================

class User(Base):
    """Sistem kullanıcıları"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # İlişkiler
    incidents_assigned = relationship("Incident", foreign_keys="Incident.assignee_id", back_populates="assignee")
    comments = relationship("IncidentComment", back_populates="user")
    scan_jobs_created = relationship("ScanJob", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<Kullanıcı {self.email} ({self.role})>"


# ==========================================
# Politika Modeli
# ==========================================

class Policy(Base):
    """DLP politikaları - hangi verilerin korunacağını tanımlar"""
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    severity = Column(SAEnum(PolicySeverity), default=PolicySeverity.MEDIUM, nullable=False)
    # Tespit edilecek veri türleri (örn: ["tc_kimlik_no", "kredi_karti"])
    data_types = Column(JSON, default=list)
    # Politika eylemleri (örn: ["alert", "block", "quarantine"])
    actions = Column(JSON, default=list)
    # Taranacak dosya türleri (örn: [".pdf", ".docx", ".xlsx"])
    file_types = Column(JSON, default=list)
    # Taranacak bulut kaynakları (örn: ["google_drive", "gmail"])
    cloud_sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # İlişkiler
    incidents = relationship("Incident", back_populates="policy")

    def __repr__(self):
        return f"<Politika: {self.name}>"


# ==========================================
# Olay (İhlal) Modeli
# ==========================================

class Incident(Base):
    """Tespit edilen güvenlik ihlalleri"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SAEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False)
    status = Column(SAEnum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    # Dosya bilgileri
    file_path = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    # Kaynak bilgisi
    cloud_source = Column(String(100), nullable=True)
    source_url = Column(String(1000), nullable=True)
    # Tespit detayları
    detected_patterns = Column(JSON, default=list)  # PatternMatch listesi
    risk_score = Column(Integer, default=0, nullable=False)
    # Atama
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # İlişkiler
    policy = relationship("Policy", back_populates="incidents")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="incidents_assigned")
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Olay #{self.id}: {self.title}>"


# ==========================================
# Olay Yorumu Modeli
# ==========================================

class IncidentComment(Base):
    """Olaylara eklenen yorumlar"""
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler
    incident = relationship("Incident", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Yorum: Olay #{self.incident_id} - Kullanıcı #{self.user_id}>"


# ==========================================
# Tarama İşi Modeli
# ==========================================

class ScanJob(Base):
    """Dosya/bulut tarama işleri"""
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scan_type = Column(SAEnum(ScanType), nullable=False)
    target_path = Column(String(1000), nullable=True)  # Yerel yol veya bulut klasör ID'si
    status = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    # İstatistikler
    total_files = Column(Integer, default=0)
    scanned_files = Column(Integer, default=0)
    incidents_found = Column(Integer, default=0)
    # Zaman bilgileri
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    # Oluşturan kullanıcı
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Hata mesajı (başarısız taramalar için)
    error_message = Column(Text, nullable=True)
    # Politika yapılandırması
    policy_ids = Column(JSON, default=list)
    pattern_keys = Column(JSON, default=list)

    # İlişkiler
    creator = relationship("User", back_populates="scan_jobs_created")
    results = relationship("ScanResult", back_populates="scan_job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tarama İşi #{self.id}: {self.name} ({self.status})>"


# ==========================================
# Tarama Sonucu Modeli
# ==========================================

class ScanResult(Base):
    """Her dosya için tarama sonuçları"""
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    file_type = Column(String(50), nullable=True)
    # Tarama durumu: clean, threat, error
    status = Column(String(50), default="clean", nullable=False)
    # Tespit edilen örüntüler
    detected_patterns = Column(JSON, default=list)
    risk_score = Column(Integer, default=0)
    # Oluşturulan olay
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    error_message = Column(Text, nullable=True)

    # İlişkiler
    scan_job = relationship("ScanJob", back_populates="results")

    def __repr__(self):
        return f"<Tarama Sonucu: {self.file_name} ({self.status})>"


# ==========================================
# Entegrasyon Modeli
# ==========================================

class Integration(Base):
    """Dış sistem entegrasyonları (Google, Microsoft, vb.)"""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SAEnum(IntegrationType), nullable=False)
    # Entegrasyon yapılandırması (kimlik bilgileri, endpoint'ler vb.)
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Entegrasyon: {self.name} ({self.type})>"


# ==========================================
# Bildirim Kuralı Modeli
# ==========================================

class NotificationRule(Base):
    """Bildirim tetikleme kuralları"""
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Tetikleme olayları: ["incident_created", "scan_completed", "policy_violation"]
    events = Column(JSON, default=list)
    # Bildirim kanalları: ["email", "webhook", "slack"]
    channels = Column(JSON, default=list)
    # Alıcılar (e-posta adresleri veya webhook URL'leri)
    recipients = Column(JSON, default=dict)
    # Filtreler (örn: sadece critical olaylar)
    filters = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler
    logs = relationship("NotificationLog", back_populates="rule")

    def __repr__(self):
        return f"<Bildirim Kuralı: {self.name}>"


# ==========================================
# Bildirim Logu Modeli
# ==========================================

class NotificationLog(Base):
    """Gönderilen bildirimlerin kayıtları"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    recipient = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    # Başarılı/Başarısız
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    error_detail = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler
    rule = relationship("NotificationRule", back_populates="logs")

    def __repr__(self):
        return f"<Bildirim Logu: {self.event_type} -> {self.recipient} ({self.status})>"


# ==========================================
# Denetim Logu Modeli
# ==========================================

class AuditLog(Base):
    """Kullanıcı eylemlerinin denetim kaydı"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # Örn: "incident.created", "policy.updated"
    resource_type = Column(String(100), nullable=True)  # Örn: "incident", "policy"
    resource_id = Column(Integer, nullable=True)
    # Eylem detayları (önceki/sonraki değerler vb.)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<Denetim Logu: {self.action} - {self.created_at}>"


# ==========================================
# Sistem Ayarı Modeli
# ==========================================

class SystemSetting(Base):
    """Sistem geneli ayarlar (anahtar-değer çiftleri)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, default="genel")
    is_sensitive = Column(Boolean, default=False)  # Şifre vb. hassas değerler
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Sistem Ayarı: {self.key}>"
