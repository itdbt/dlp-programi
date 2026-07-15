@echo off
chcp 65001 > nul
title DLP Sistemi - Kurulum

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║         🛡️  DLP GÜVENLİK SİSTEMİ - KURULUM              ║
echo  ║         Kurumsal Veri Kaybı Önleme Platformu             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM --- Python kontrolü ---
echo [1/5] Python kontrolü yapılıyor...
python --version > nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadı! Lütfen Python 3.11+ kurun: https://python.org
    pause
    exit /b 1
)
echo [OK] Python bulundu.

REM --- Node.js kontrolü ---
echo [2/5] Node.js kontrolü yapılıyor...
node --version > nul 2>&1
if errorlevel 1 (
    echo [HATA] Node.js bulunamadı! Lütfen Node.js 18+ kurun: https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js bulundu.

REM --- Backend .env oluştur ---
echo [3/5] Backend yapılandırması...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" > nul
    echo [OK] backend\.env dosyası oluşturuldu. Lütfen düzenleyin!
) else (
    echo [OK] backend\.env zaten mevcut.
)

REM --- Backend Python paketleri ---
echo [4/5] Python paketleri kuruluyor (bu işlem biraz sürebilir)...
cd backend
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [HATA] Python paketleri kurulumunda sorun oluştu!
    cd ..
    pause
    exit /b 1
)
echo [OK] Python paketleri kuruldu.
cd ..

REM --- Frontend Node paketleri ---
echo [5/5] Node.js paketleri kuruluyor...
cd frontend
npm install --silent
if errorlevel 1 (
    echo [HATA] Node.js paketleri kurulumunda sorun oluştu!
    cd ..
    pause
    exit /b 1
)
echo [OK] Node.js paketleri kuruldu.
cd ..

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✅ KURULUM TAMAMLANDI!                                   ║
echo  ║                                                           ║
echo  ║  Sistemi başlatmak için: start.bat                        ║
echo  ║                                                           ║
echo  ║  Varsayılan giriş:                                        ║
echo  ║    E-posta: admin@dlp.local                               ║
echo  ║    Şifre:   Admin123!                                     ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause
