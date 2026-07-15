import json
from sqlalchemy.orm import Session
from models import User, Policy, SystemSetting, NotificationRule
from auth import get_password_hash
from datetime import datetime, timezone

def seed_db(db: Session):
    # Yönetici Kullanıcı kontrolü
    admin_email = "admin@dlp.local"
    if not db.query(User).filter(User.email == admin_email).first():
        admin_user = User(
            email=admin_email,
            full_name="Sistem Yöneticisi",
            hashed_password=get_password_hash("Admin123!"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        
    # Analist Kullanıcı kontrolü
    analyst_email = "analyst@dlp.local"
    if not db.query(User).filter(User.email == analyst_email).first():
        analyst_user = User(
            email=analyst_email,
            full_name="Güvenlik Analisti",
            hashed_password=get_password_hash("Analyst123!"),
            role="analyst",
            is_active=True
        )
        db.add(analyst_user)

    # Örnek Politikalar
    if db.query(Policy).count() == 0:
        policies = [
            Policy(
                name="Finansal Veri Koruması",
                description="Kredi kartı ve IBAN numarası içeren dökümanları engeller.",
                is_active=True,
                severity="Kritik",
                data_types=json.dumps(["kredi_karti", "iban_tr"]),
                actions=json.dumps(["Engelle", "Uyar"]),
                file_types=json.dumps([".pdf", ".xlsx", ".csv"]),
                cloud_sources=json.dumps(["Google Drive", "OneDrive"])
            ),
            Policy(
                name="Kişisel Veri (KVKK) Kontrolü",
                description="TC Kimlik, Pasaport ve Sağlık verilerini izler.",
                is_active=True,
                severity="Yüksek",
                data_types=json.dumps(["tc_kimlik_no", "passport_no", "saglik_bilgisi"]),
                actions=json.dumps(["Uyar", "Karantinaya Al"]),
                file_types=json.dumps([".pdf", ".docx", ".txt"]),
                cloud_sources=json.dumps(["Gmail", "Outlook"])
            ),
            Policy(
                name="Kaynak Kod Sızıntısı",
                description="API Anahtarları ve Şifre Hash'lerinin sızmasını önler.",
                is_active=True,
                severity="Kritik",
                data_types=json.dumps(["api_key", "sifre_hash"]),
                actions=json.dumps(["Engelle"]),
                file_types=json.dumps([".py", ".js", ".json", ".env"]),
                cloud_sources=json.dumps(["GitHub", "GitLab", "Local"])
            )
        ]
        db.add_all(policies)

    # Sistem Ayarları
    if db.query(SystemSetting).count() == 0:
        settings = [
            SystemSetting(key="system_name", value="DLP Güvenlik Sistemi", description="Sistem Adı"),
            SystemSetting(key="timezone", value="Europe/Istanbul", description="Zaman Dilimi"),
            SystemSetting(key="auto_scan_interval", value="60", description="Otomatik Tarama Aralığı (dk)"),
            SystemSetting(key="max_file_size", value="50", description="Maksimum Dosya Boyutu (MB)"),
            SystemSetting(key="data_retention_days", value="90", description="Veri Saklama Süresi (Gün)"),
            SystemSetting(key="log_level", value="INFO", description="Log Seviyesi")
        ]
        db.add_all(settings)

    # Bildirim Kuralları
    if db.query(NotificationRule).count() == 0:
        rules = [
            NotificationRule(
                name="Kritik Olay Bildirimi",
                events=json.dumps(["Kritik Olay"]),
                channels=json.dumps(["E-posta"]),
                recipients=json.dumps(["admin@dlp.local", "security@dlp.local"]),
                is_active=True
            ),
            NotificationRule(
                name="Günlük Tarama Raporu",
                events=json.dumps(["Tarama Tamamlandı"]),
                channels=json.dumps(["E-posta"]),
                recipients=json.dumps(["analyst@dlp.local"]),
                is_active=True
            )
        ]
        db.add_all(rules)

    db.commit()
