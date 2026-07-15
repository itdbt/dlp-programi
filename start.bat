@echo off
chcp 65001 > nul
title DLP Güvenlik Sistemi

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║         🛡️  DLP GÜVENLİK SİSTEMİ BAŞLATILIYOR           ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM --- Backend başlat ---
echo [1/2] Backend API sunucusu başlatılıyor (port 8000)...
start "DLP Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Kısa bekleme
timeout /t 3 /nobreak > nul

REM --- Frontend başlat ---
echo [2/2] Frontend geliştirme sunucusu başlatılıyor (port 3000)...
start "DLP Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Tarayıcı için bekle
timeout /t 5 /nobreak > nul

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✅ SİSTEM ÇALIŞIYOR!                                     ║
echo  ║                                                           ║
echo  ║  🌐 Arayüz:  http://localhost:3000                        ║
echo  ║  🔌 API:     http://localhost:8000                        ║
echo  ║  📚 API Dok: http://localhost:8000/docs                   ║
echo  ║                                                           ║
echo  ║  Varsayılan giriş:                                        ║
echo  ║    E-posta: admin@dlp.local                               ║
echo  ║    Şifre:   Admin123!                                     ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM Tarayıcıyı otomatik aç
start http://localhost:3000

echo Çıkmak için herhangi bir tuşa basın (sunucular arka planda çalışmaya devam eder)...
pause > nul
