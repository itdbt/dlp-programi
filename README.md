# 🛡️ DLP Güvenlik Sistemi

**Kurumsal Veri Kaybı Önleme (Data Loss Prevention) Platformu**

Tam kapsamlı, Türkçe arayüzlü, kurumsal düzeyde DLP sistemi.

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```batch
install.bat
```

### 2. Başlatma
```batch
start.bat
```

### 3. Tarayıcıda Aç
- **Arayüz:** http://localhost:3000
- **API Dokümantasyonu:** http://localhost:8000/docs

### 4. Giriş
```
E-posta: admin@dlp.local
Şifre:   Admin123!
```

---

## ✨ Özellikler

### 🔍 Tarama Motoru
| Tür | Açıklama |
|-----|----------|
| Yerel Dosya | PDF, Word, Excel, TXT, CSV, JSON, Kod dosyaları |
| Google Drive | OAuth2 ile Google Drive klasör taraması |
| Gmail | E-posta içeriği ve ek taraması |
| OneDrive | Microsoft Graph API ile OneDrive taraması |
| SharePoint | SharePoint site taraması |
| Outlook | Office 365 e-posta taraması |

### 🎯 Tespit Edilen Veri Türleri
- 🪪 TC Kimlik Numarası (algoritma doğrulama ile)
- 💳 Kredi Kartı Numaraları (Luhn algoritması)
- 🏦 IBAN Numaraları (TR)
- 📧 E-posta Adresleri
- 📱 Türk Telefon Numaraları
- 🔑 API Anahtarları
- 🔒 Şifre / Hash Değerleri
- 🛂 Pasaport Numaraları
- 🏢 Vergi Numaraları
- 🏥 Sağlık Bilgileri
- 🔐 Gizli Etiketli İçerik

### 📋 Politika Yönetimi
- Özelleştirilebilir DLP politikaları
- Çoklu veri tipi seçimi
- Aksiyon tanımlama: Engelle / Uyar / İzin Ver / Karantina
- Dosya tipi filtreleme
- Bulut kaynak hedefleme

### 🚨 Olay Yönetimi
- Otomatik olay oluşturma
- Öncelik seviyeleri: Kritik / Yüksek / Orta / Düşük
- İş akışı: Açık → İnceleniyor → Çözüldü
- Kullanıcı atama
- Yorum sistemi
- Zaman çizelgesi

### 📊 Raporlama
- Olay trend grafikleri (son 30 gün)
- Uyumluluk raporları (KVKK, GDPR, PCI DSS, HIPAA)
- Risk matrisi görselleştirmesi
- Veri türü frekans analizleri
- CSV dışa aktarma

### 🔔 Bildirimler
- Türkçe HTML e-posta şablonları
- Webhook desteği
- Olay bazlı tetikleyiciler
- Günlük rapor e-postaları

---

## 🛠️ Teknoloji Yığını

### Backend
```
Python 3.11+     → Programlama dili
FastAPI          → REST API framework
SQLAlchemy       → ORM
SQLite           → Veritabanı
APScheduler      → Zamanlı görevler
PyPDF2           → PDF okuma
python-docx      → Word okuma
openpyxl         → Excel okuma
google-api-python-client → Google Workspace
msal             → Microsoft OAuth
aiosmtplib       → E-posta gönderimi
```

### Frontend
```
React 18         → UI framework
Vite             → Build tool
Recharts         → Grafikler
Lucide React     → İkonlar
React Router     → Yönlendirme
Axios            → HTTP istemcisi
react-hot-toast  → Bildirimler
```

---

## 📁 Proje Yapısı

```
DLP Programı/
├── 📁 backend/
│   ├── 📄 main.py              # FastAPI uygulaması
│   ├── 📄 database.py          # Veritabanı bağlantısı
│   ├── 📄 models.py            # SQLAlchemy modelleri
│   ├── 📄 schemas.py           # Pydantic şemaları
│   ├── 📄 auth.py              # JWT kimlik doğrulama
│   ├── 📄 seed.py              # Başlangıç verisi
│   ├── 📄 requirements.txt     # Python bağımlılıkları
│   ├── 📄 .env                 # Yapılandırma (gizli)
│   ├── 📁 engines/
│   │   ├── 📄 detection_patterns.py  # Veri desenleri
│   │   ├── 📄 scan_engine.py         # Tarama motoru
│   │   ├── 📄 cloud_scanner.py       # Bulut tarayıcısı
│   │   ├── 📄 rule_engine.py         # Kural motoru
│   │   └── 📄 email_notifier.py      # Bildirim sistemi
│   └── 📁 routers/
│       ├── 📄 auth_router.py    # Kimlik doğrulama
│       ├── 📄 dashboard.py      # Dashboard
│       ├── 📄 policies.py       # Politikalar
│       ├── 📄 incidents.py      # Olaylar
│       ├── 📄 scans.py          # Taramalar
│       ├── 📄 reports.py        # Raporlar
│       ├── 📄 integrations.py   # Entegrasyonlar
│       ├── 📄 notifications.py  # Bildirimler
│       └── 📄 settings.py       # Ayarlar
│
└── 📁 frontend/
    ├── 📄 package.json
    ├── 📄 vite.config.js
    ├── 📄 index.html
    └── 📁 src/
        ├── 📄 App.jsx
        ├── 📄 index.css
        ├── 📁 api/
        │   └── 📄 client.js
        ├── 📁 context/
        │   └── 📄 AuthContext.jsx
        ├── 📁 components/
        │   └── 📁 Layout/
        └── 📁 pages/
            ├── 📄 Login.jsx
            ├── 📄 Dashboard.jsx
            ├── 📄 Policies.jsx
            ├── 📄 Incidents.jsx
            ├── 📄 Scanner.jsx
            ├── 📄 Reports.jsx
            ├── 📄 Integrations.jsx
            └── 📄 Settings.jsx
```

---

## ⚙️ Yapılandırma

`backend/.env` dosyasını düzenleyin:

```env
# Güvenlik
SECRET_KEY=güçlü-rastgele-anahtar-buraya

# Veritabanı  
DATABASE_URL=sqlite:///./dlp.db

# E-posta (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sizin@gmail.com
SMTP_PASSWORD=uygulama-şifresi

# Google Workspace
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Microsoft 365
MS_TENANT_ID=...
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
```

---

## 🔐 Kullanıcı Rolleri

| Rol | Yetki |
|-----|-------|
| **Yönetici** | Tam erişim: politika, kullanıcı, sistem ayarları |
| **Analist** | Olay yönetimi, tarama, raporlar |
| **İzleme** | Sadece okuma: dashboard, raporlar |

---

## 📜 Lisans

Bu sistem kurumsal kullanım için geliştirilmiştir. Tüm haklar saklıdır.
