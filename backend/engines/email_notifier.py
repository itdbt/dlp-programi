"""
DLP Sistemi - E-posta ve Webhook Bildirim Sistemi
Türkçe HTML şablonlarıyla olay ve tarama bildirimleri gönderir
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


# ==========================================
# E-posta Bildirim Sınıfı
# ==========================================

class EmailNotifier:
    """
    SMTP üzerinden e-posta bildirimleri gönderir.
    Türkçe HTML şablonlarıyla olay ve tarama bildirimlerini destekler.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from: str,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.use_tls = use_tls

    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        HTML e-posta gönder.
        
        Args:
            to: Alıcı e-posta adresleri listesi
            subject: E-posta konusu
            html_body: HTML formatında e-posta gövdesi
            text_body: Düz metin alternatifi (opsiyonel)
        
        Returns:
            True: Başarılı, False: Başarısız
        """
        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            # E-posta mesajı oluştur
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from
            message["To"] = ", ".join(to)

            # Düz metin ekle
            plain_text = text_body or self._html_to_plain(html_body)
            message.attach(MIMEText(plain_text, "plain", "utf-8"))

            # HTML içerik ekle
            message.attach(MIMEText(html_body, "html", "utf-8"))

            # SMTP ile gönder
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.use_tls,
            )

            logger.info(f"E-posta gönderildi: {subject} -> {to}")
            return True

        except ImportError:
            logger.error("aiosmtplib kurulu değil. 'pip install aiosmtplib' çalıştırın.")
            return False
        except Exception as e:
            logger.error(f"E-posta gönderme hatası: {e}")
            return False

    async def send_incident_alert(
        self,
        incident_data: Dict[str, Any],
        recipients: List[str]
    ) -> bool:
        """
        Güvenlik olayı için uyarı e-postası gönder.
        
        Args:
            incident_data: Olay bilgileri sözlüğü
            recipients: Alıcı listesi
        
        Returns:
            True: Başarılı
        """
        severity = incident_data.get("severity", "medium")
        severity_tr = {
            "critical": "KRİTİK",
            "high": "YÜKSEK",
            "medium": "ORTA",
            "low": "DÜŞÜK"
        }.get(severity, "ORTA")

        subject = (
            f"[DLP UYARI] {severity_tr} Seviye Güvenlik İhlali: "
            f"{incident_data.get('title', 'Bilinmeyen İhlal')}"
        )

        html_body = self._build_incident_html(incident_data)
        return await self.send_email(recipients, subject, html_body)

    async def send_scan_complete(
        self,
        scan_data: Dict[str, Any],
        recipients: List[str]
    ) -> bool:
        """
        Tarama tamamlama bildirimi gönder.
        
        Args:
            scan_data: Tarama sonuç bilgileri
            recipients: Alıcı listesi
        
        Returns:
            True: Başarılı
        """
        incidents_found = scan_data.get("incidents_found", 0)
        status_emoji = "🚨" if incidents_found > 0 else "✅"
        subject = (
            f"{status_emoji} [DLP] Tarama Tamamlandı: "
            f"{scan_data.get('name', 'Bilinmeyen Tarama')}"
        )

        html_body = self._build_scan_html(scan_data)
        return await self.send_email(recipients, subject, html_body)

    async def send_test_email(self, recipient: str) -> bool:
        """Test e-postası gönder"""
        subject = "✅ [DLP Sistemi] E-posta Bağlantı Testi"
        html_body = f"""
        {self._get_email_header()}
        <div style="padding: 30px; background: #f8f9fa;">
            <div style="background: white; border-radius: 8px; padding: 30px; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #28a745; margin-top: 0;">✅ Bağlantı Testi Başarılı</h2>
                <p style="color: #333; font-size: 16px; line-height: 1.6;">
                    DLP Sistemi e-posta entegrasyonu başarıyla yapılandırıldı.
                    Bu, bir test mesajıdır.
                </p>
                <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #666;">
                        <strong>Gönderim Zamanı:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}<br>
                        <strong>Alıcı:</strong> {recipient}<br>
                        <strong>Sunucu:</strong> {self.smtp_host}:{self.smtp_port}
                    </p>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Bu e-postayı almak zorunda değilsiniz. Sistem tarafından otomatik gönderilmiştir.
                </p>
            </div>
        </div>
        {self._get_email_footer()}
        """
        return await self.send_email([recipient], subject, html_body)

    def _build_incident_html(self, incident_data: Dict[str, Any]) -> str:
        """Türkçe olay bildirim HTML şablonu oluştur"""
        severity = incident_data.get("severity", "medium")
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        }
        severity_tr = {
            "critical": "KRİTİK",
            "high": "YÜKSEK",
            "medium": "ORTA",
            "low": "DÜŞÜK"
        }

        color = severity_colors.get(severity, "#6c757d")
        severity_text = severity_tr.get(severity, "ORTA")

        # Tespit edilen örüntüler
        patterns = incident_data.get("detected_patterns", [])
        patterns_html = ""
        for p in patterns[:10]:
            patterns_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{p.get('pattern_name', 'Bilinmiyor')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{p.get('category', '-')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{p.get('risk_score', 0)}/100</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; font-family: monospace;">{p.get('matched_text', '***')}</td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            {self._get_email_header()}
            
            <div style="padding: 30px 20px; background: #f0f2f5;">
            <div style="max-width: 650px; margin: 0 auto;">
            
            <!-- Uyarı Bandı -->
            <div style="background: {color}; color: white; padding: 15px 25px; border-radius: 8px 8px 0 0; display: flex; align-items: center;">
                <span style="font-size: 28px; margin-right: 10px;">🚨</span>
                <div>
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Güvenlik İhlali Tespit Edildi</div>
                    <div style="font-size: 20px; font-weight: bold;">{severity_text} SEVİYE UYARI</div>
                </div>
            </div>
            
            <!-- Ana İçerik -->
            <div style="background: white; padding: 30px; border-left: 4px solid {color}; border-right: 1px solid #e0e0e0; border-bottom: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
                
                <h2 style="color: #1a1a2e; margin-top: 0; font-size: 18px;">
                    {incident_data.get('title', 'Güvenlik İhlali')}
                </h2>
                
                <!-- Temel Bilgiler -->
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8f9fa; border-radius: 6px;">
                    <tr>
                        <td style="padding: 10px 15px; color: #666; font-size: 13px; width: 35%;">Olay ID</td>
                        <td style="padding: 10px 15px; color: #333; font-weight: 600;">#{incident_data.get('id', 'N/A')}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 10px 15px; color: #666; font-size: 13px;">Önem Derecesi</td>
                        <td style="padding: 10px 15px;">
                            <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">{severity_text}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; color: #666; font-size: 13px;">Risk Skoru</td>
                        <td style="padding: 10px 15px; color: {color}; font-weight: bold; font-size: 16px;">{incident_data.get('risk_score', 0)}/100</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 10px 15px; color: #666; font-size: 13px;">Dosya</td>
                        <td style="padding: 10px 15px; color: #333; font-family: monospace; font-size: 13px;">{incident_data.get('file_name', 'Bilinmiyor')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; color: #666; font-size: 13px;">Kaynak</td>
                        <td style="padding: 10px 15px; color: #333;">{incident_data.get('cloud_source', 'Yerel Sistem')}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 10px 15px; color: #666; font-size: 13px;">Tespit Zamanı</td>
                        <td style="padding: 10px 15px; color: #333;">{incident_data.get('created_at', datetime.now().strftime('%d.%m.%Y %H:%M'))}</td>
                    </tr>
                </table>
                
                <!-- Tespit Edilen Örüntüler -->
                {"" if not patterns else f"""
                <h3 style="color: #1a1a2e; font-size: 15px; margin-top: 25px;">🔍 Tespit Edilen Hassas Veriler</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background: #1a1a2e; color: white;">
                            <th style="padding: 10px; text-align: left;">Veri Türü</th>
                            <th style="padding: 10px; text-align: left;">Kategori</th>
                            <th style="padding: 10px; text-align: left;">Risk</th>
                            <th style="padding: 10px; text-align: left;">Örnek</th>
                        </tr>
                    </thead>
                    <tbody>
                        {patterns_html}
                    </tbody>
                </table>
                """}
                
                <!-- Açıklama -->
                {f'<div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;"><p style="margin: 0; color: #856404; font-size: 14px;">{incident_data.get("description", "")}</p></div>' if incident_data.get("description") else ""}
                
                <!-- Aksiyon Butonu -->
                <div style="text-align: center; margin-top: 30px;">
                    <a href="http://localhost:3000/incidents/{incident_data.get('id', '')}" 
                       style="background: #1a1a2e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
                        🔍 Olayı İncele
                    </a>
                </div>
                
            </div>
            </div>
            </div>
            
            {self._get_email_footer()}
        </body>
        </html>
        """

    def _build_scan_html(self, scan_data: Dict[str, Any]) -> str:
        """Türkçe tarama tamamlama HTML şablonu oluştur"""
        incidents_found = scan_data.get("incidents_found", 0)
        status_color = "#dc3545" if incidents_found > 0 else "#28a745"
        status_icon = "🚨" if incidents_found > 0 else "✅"
        status_text = "Sorun Tespit Edildi" if incidents_found > 0 else "Temiz"

        # Süre hesapla
        duration = "N/A"
        if scan_data.get("started_at") and scan_data.get("completed_at"):
            try:
                start = datetime.fromisoformat(str(scan_data["started_at"]))
                end = datetime.fromisoformat(str(scan_data["completed_at"]))
                delta = end - start
                minutes = int(delta.total_seconds() / 60)
                seconds = int(delta.total_seconds() % 60)
                duration = f"{minutes} dk {seconds} sn"
            except Exception:
                duration = "N/A"

        return f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            {self._get_email_header()}
            
            <div style="padding: 30px 20px; background: #f0f2f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
            
            <!-- Başlık -->
            <div style="background: {status_color}; color: white; padding: 20px 30px;">
                <div style="font-size: 28px;">{status_icon}</div>
                <h2 style="margin: 5px 0 0 0; font-size: 20px;">Tarama Tamamlandı: {status_text}</h2>
            </div>
            
            <!-- İçerik -->
            <div style="padding: 30px;">
                <h3 style="color: #1a1a2e; margin-top: 0;">{scan_data.get('name', 'Bilinmeyen Tarama')}</h3>
                
                <!-- İstatistikler -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;">
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #1a1a2e;">{scan_data.get('total_files', 0)}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">Toplam Dosya</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #28a745;">{scan_data.get('scanned_files', 0)}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">Taranan</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: {status_color};">{incidents_found}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">İhlal</div>
                    </div>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin: 15px 0;">
                    <tr>
                        <td style="padding: 8px 0; color: #666; border-bottom: 1px solid #f0f0f0;">Tarama Türü</td>
                        <td style="padding: 8px 0; color: #333; font-weight: 500; border-bottom: 1px solid #f0f0f0;">{scan_data.get('scan_type', 'Bilinmiyor')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666; border-bottom: 1px solid #f0f0f0;">Hedef</td>
                        <td style="padding: 8px 0; color: #333; border-bottom: 1px solid #f0f0f0; font-family: monospace; font-size: 12px;">{scan_data.get('target_path', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666; border-bottom: 1px solid #f0f0f0;">Süre</td>
                        <td style="padding: 8px 0; color: #333; border-bottom: 1px solid #f0f0f0;">{duration}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Tamamlanma</td>
                        <td style="padding: 8px 0; color: #333;">{scan_data.get('completed_at', datetime.now().strftime('%d.%m.%Y %H:%M'))}</td>
                    </tr>
                </table>
                
                <!-- Hata mesajı -->
                {f'<div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 12px; border-radius: 4px; margin: 15px 0; font-size: 13px; color: #721c24;">{scan_data.get("error_message", "")}</div>' if scan_data.get("error_message") else ""}
                
                <!-- Aksiyon -->
                <div style="text-align: center; margin-top: 25px;">
                    <a href="http://localhost:3000/scans/{scan_data.get('id', '')}" 
                       style="background: #1a1a2e; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold; display: inline-block;">
                        📊 Detayları Görüntüle
                    </a>
                </div>
            </div>
            </div>
            </div>
            
            {self._get_email_footer()}
        </body>
        </html>
        """

    def _get_email_header(self) -> str:
        """E-posta üst bölümü"""
        return """
        <div style="background: #1a1a2e; padding: 20px; text-align: center;">
            <div style="display: inline-flex; align-items: center; gap: 10px;">
                <span style="font-size: 28px;">🛡️</span>
                <span style="color: white; font-size: 22px; font-weight: bold; letter-spacing: 2px;">DLP GÜVENLİK SİSTEMİ</span>
            </div>
            <div style="color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 5px;">Data Loss Prevention</div>
        </div>
        """

    def _get_email_footer(self) -> str:
        """E-posta alt bölümü"""
        year = datetime.now().year
        return f"""
        <div style="background: #1a1a2e; padding: 15px; text-align: center; margin-top: 20px;">
            <p style="color: rgba(255,255,255,0.5); font-size: 11px; margin: 0;">
                Bu e-posta DLP Güvenlik Sistemi tarafından otomatik olarak gönderilmiştir.
                Lütfen bu e-postayı yanıtlamayın.
            </p>
            <p style="color: rgba(255,255,255,0.3); font-size: 10px; margin: 5px 0 0 0;">
                © {year} DLP Güvenlik Sistemi. Tüm hakları saklıdır.
            </p>
        </div>
        """

    def _html_to_plain(self, html: str) -> str:
        """HTML'yi basit düz metne çevir"""
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()


# ==========================================
# Webhook Bildirim Sınıfı
# ==========================================

class WebhookNotifier:
    """HTTP webhook ile bildirim gönderir"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def send(self, url: str, payload: dict, headers: dict = None) -> bool:
        """
        Webhook URL'sine POST isteği gönder.
        
        Args:
            url: Webhook URL'si
            payload: Gönderilecek veri
            headers: İsteğe özel HTTP başlıkları
        
        Returns:
            True: Başarılı (2xx yanıt), False: Başarısız
        """
        try:
            request_headers = {
                "Content-Type": "application/json",
                "User-Agent": "DLP-Security-System/1.0"
            }
            if headers:
                request_headers.update(headers)

            response = requests.post(
                url=url,
                json=payload,
                headers=request_headers,
                timeout=self.timeout
            )

            if response.ok:
                logger.info(f"Webhook gönderildi: {url} ({response.status_code})")
                return True
            else:
                logger.warning(f"Webhook başarısız: {url} - HTTP {response.status_code}")
                return False

        except requests.Timeout:
            logger.error(f"Webhook zaman aşımı: {url}")
            return False
        except Exception as e:
            logger.error(f"Webhook gönderme hatası ({url}): {e}")
            return False

    def send_slack(self, webhook_url: str, message: str, color: str = "#1a1a2e") -> bool:
        """Slack uyumlu webhook mesajı gönder"""
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message,
                    "footer": "DLP Güvenlik Sistemi",
                    "footer_icon": "https://img.icons8.com/color/48/shield.png",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        return self.send(webhook_url, payload)

    def send_teams(self, webhook_url: str, title: str, message: str, color: str = "0076D7") -> bool:
        """Microsoft Teams uyumlu webhook mesajı gönder"""
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": f"🛡️ DLP Güvenlik Sistemi",
                    "activitySubtitle": title,
                    "text": message
                }
            ]
        }
        return self.send(webhook_url, payload)


# ==========================================
# Bildirim Yönetici Sınıfı
# ==========================================

class NotificationManager:
    """
    Bildirim kurallarını değerlendirir ve uygun bildirimleri gönderir.
    """

    def __init__(self, db):
        self.db = db
        self.webhook_notifier = WebhookNotifier()

    async def process_event(
        self,
        event_type: str,
        event_data: dict,
        email_notifier: Optional[EmailNotifier] = None
    ):
        """
        Bir olayı bildirim kurallarıyla eşleştir ve bildirimleri gönder.
        
        Args:
            event_type: Olay tipi (örn: "incident_created", "scan_completed")
            event_data: Olay verisi
            email_notifier: E-posta gönderici (opsiyonel)
        """
        import models

        try:
            # Aktif kuralları al
            rules = self.db.query(models.NotificationRule).filter(
                models.NotificationRule.is_active == True
            ).all()

            for rule in rules:
                # Kural bu olayı kapsıyor mu?
                if event_type not in (rule.events or []):
                    continue

                # Filtreler uyuşuyor mu?
                if not self._check_filters(rule.filters or {}, event_data):
                    continue

                # Her kanalda bildirim gönder
                recipients = rule.recipients or {}
                channels = rule.channels or []

                for channel in channels:
                    success = False
                    message = None
                    error_detail = None

                    try:
                        if channel == "email" and email_notifier:
                            email_list = recipients.get("email", [])
                            if isinstance(email_list, str):
                                email_list = [email_list]

                            if email_list:
                                if event_type in ("incident_created", "incident_updated"):
                                    success = await email_notifier.send_incident_alert(
                                        event_data, email_list
                                    )
                                elif event_type == "scan_completed":
                                    success = await email_notifier.send_scan_complete(
                                        event_data, email_list
                                    )
                                message = f"E-posta gönderildi: {', '.join(email_list)}"

                        elif channel == "webhook":
                            webhook_url = recipients.get("webhook_url")
                            if webhook_url:
                                payload = {
                                    "event_type": event_type,
                                    "data": event_data,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "source": "DLP Güvenlik Sistemi"
                                }
                                success = self.webhook_notifier.send(webhook_url, payload)
                                message = f"Webhook gönderildi: {webhook_url}"

                        elif channel == "slack":
                            slack_url = recipients.get("slack_webhook_url")
                            if slack_url:
                                slack_message = self._format_slack_message(event_type, event_data)
                                color = self._get_severity_color(event_data)
                                success = self.webhook_notifier.send_slack(slack_url, slack_message, color)
                                message = "Slack bildirimi gönderildi"

                        elif channel == "teams":
                            teams_url = recipients.get("teams_webhook_url")
                            if teams_url:
                                title, text = self._format_teams_message(event_type, event_data)
                                success = self.webhook_notifier.send_teams(teams_url, title, text)
                                message = "Teams bildirimi gönderildi"

                    except Exception as e:
                        error_detail = str(e)
                        logger.error(f"Bildirim gönderme hatası ({channel}): {e}")

                    # Log kaydet
                    self._log_notification(
                        rule_id=rule.id,
                        event_type=event_type,
                        recipient=str(recipients.get(channel, channel)),
                        channel=channel,
                        status="success" if success else "failed",
                        message=message,
                        error_detail=error_detail
                    )

        except Exception as e:
            logger.error(f"Olay işleme hatası: {e}")

    def _check_filters(self, filters: dict, event_data: dict) -> bool:
        """Bildirim kuralı filtrelerini kontrol et"""
        if not filters:
            return True

        # Önem derecesi filtresi
        severity_filter = filters.get("severity")
        if severity_filter:
            event_severity = event_data.get("severity", "low")
            severity_levels = ["low", "medium", "high", "critical"]
            min_level = severity_levels.index(severity_filter) if severity_filter in severity_levels else 0
            event_level = severity_levels.index(event_severity) if event_severity in severity_levels else 0
            if event_level < min_level:
                return False

        # Kaynak filtresi
        source_filter = filters.get("cloud_source")
        if source_filter and event_data.get("cloud_source") != source_filter:
            return False

        return True

    def _format_slack_message(self, event_type: str, event_data: dict) -> str:
        """Slack mesaj formatı oluştur"""
        if event_type in ("incident_created", "incident_updated"):
            severity = event_data.get("severity", "medium")
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            return (
                f"{severity_emoji} *Güvenlik İhlali Tespit Edildi*\n"
                f"*Başlık:* {event_data.get('title', 'N/A')}\n"
                f"*Önem:* {severity.upper()}\n"
                f"*Risk Skoru:* {event_data.get('risk_score', 0)}/100\n"
                f"*Dosya:* {event_data.get('file_name', 'N/A')}"
            )
        elif event_type == "scan_completed":
            incidents = event_data.get("incidents_found", 0)
            icon = "✅" if incidents == 0 else "🚨"
            return (
                f"{icon} *Tarama Tamamlandı*\n"
                f"*Tarama:* {event_data.get('name', 'N/A')}\n"
                f"*Taranan:* {event_data.get('scanned_files', 0)} dosya\n"
                f"*İhlal:* {incidents} adet"
            )
        return f"Olay: {event_type}"

    def _format_teams_message(self, event_type: str, event_data: dict) -> tuple:
        """Teams mesaj formatı oluştur"""
        if event_type in ("incident_created", "incident_updated"):
            title = f"🚨 Güvenlik İhlali: {event_data.get('title', 'N/A')}"
            text = (
                f"**Önem:** {event_data.get('severity', 'N/A').upper()}  \n"
                f"**Risk Skoru:** {event_data.get('risk_score', 0)}/100  \n"
                f"**Dosya:** {event_data.get('file_name', 'N/A')}"
            )
        elif event_type == "scan_completed":
            title = f"Tarama Tamamlandı: {event_data.get('name', 'N/A')}"
            text = (
                f"**Durum:** {'Temiz' if event_data.get('incidents_found', 0) == 0 else 'İhlal Var'}  \n"
                f"**Taranan:** {event_data.get('scanned_files', 0)} dosya  \n"
                f"**İhlal:** {event_data.get('incidents_found', 0)} adet"
            )
        else:
            title = f"DLP Olayı: {event_type}"
            text = str(event_data)
        return title, text

    def _get_severity_color(self, event_data: dict) -> str:
        """Önem derecesine göre renk döndür"""
        colors = {
            "critical": "#FF0000",
            "high": "#FF8C00",
            "medium": "#FFD700",
            "low": "#28A745"
        }
        return colors.get(event_data.get("severity", "medium"), "#6C757D")

    def _log_notification(
        self,
        rule_id: int,
        event_type: str,
        recipient: str,
        channel: str,
        status: str,
        message: Optional[str],
        error_detail: Optional[str]
    ):
        """Bildirim logunu veritabanına kaydet"""
        import models
        try:
            log = models.NotificationLog(
                rule_id=rule_id,
                event_type=event_type,
                recipient=recipient[:255],
                channel=channel,
                status=status,
                message=message,
                error_detail=error_detail
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Bildirim logu kaydetme hatası: {e}")
