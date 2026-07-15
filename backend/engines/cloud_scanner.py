"""
DLP Sistemi - Bulut Depolama Tarama Motoru
Google Workspace ve Microsoft Office 365 entegrasyonları
"""

import io
import logging
import base64
from typing import List, Optional, Tuple, Dict
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


# ==========================================
# Google Workspace Tarayıcısı
# ==========================================

class GoogleWorkspaceScanner:
    """
    Google Workspace (Drive + Gmail) tarama motoru.
    Service Account veya OAuth2 kimlik bilgileri ile çalışır.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    # Google Docs MIME type -> export format eşlemesi
    GOOGLE_DOCS_EXPORT = {
        "application/vnd.google-apps.document": ("text/plain", ".txt"),
        "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
        "application/vnd.google-apps.presentation": ("text/plain", ".txt"),
        "application/vnd.google-apps.drawing": ("image/png", ".png"),
    }

    def __init__(self, credentials_info: dict):
        """
        Args:
            credentials_info: Service account JSON sözlüğü veya OAuth2 kimlik bilgileri
        """
        self.credentials_info = credentials_info
        self.credentials = None
        self.drive_service = None
        self.gmail_service = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        Google API'ye kimlik doğrula.
        Service account veya OAuth2 credential'ları kullanır.
        
        Returns:
            True: Başarılı, False: Başarısız
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            cred_type = self.credentials_info.get("type", "")

            if cred_type == "service_account":
                self.credentials = service_account.Credentials.from_service_account_info(
                    self.credentials_info,
                    scopes=self.SCOPES
                )
            else:
                from google.oauth2.credentials import Credentials
                self.credentials = Credentials(
                    token=self.credentials_info.get("token"),
                    refresh_token=self.credentials_info.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.credentials_info.get("client_id"),
                    client_secret=self.credentials_info.get("client_secret"),
                    scopes=self.SCOPES
                )

            self.drive_service = build("drive", "v3", credentials=self.credentials)
            self.gmail_service = build("gmail", "v1", credentials=self.credentials)
            self._authenticated = True
            logger.info("Google Workspace kimlik doğrulaması başarılı")
            return True

        except ImportError:
            logger.error("google-api-python-client kurulu değil. 'pip install google-api-python-client' çalıştırın.")
            return False
        except Exception as e:
            logger.error(f"Google kimlik doğrulama hatası: {e}")
            self._authenticated = False
            return False

    def list_drive_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        recursive: bool = False
    ) -> List[Dict]:
        """
        Google Drive dosyalarını listele.
        
        Args:
            folder_id: Belirli bir klasörün ID'si (None = root)
            page_size: Sayfa başına dosya sayısı
            recursive: Alt klasörleri de tara
        
        Returns:
            Dosya metadata listesi
        """
        if not self._authenticated:
            raise RuntimeError("Önce authenticate() çağrılmalıdır")

        files = []
        query_parts = ["trashed=false"]

        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        query = " and ".join(query_parts)

        try:
            page_token = None
            while True:
                response = self.drive_service.files().list(
                    q=query,
                    pageSize=min(page_size, 1000),
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, webViewLink)",
                    pageToken=page_token
                ).execute()

                batch = response.get("files", [])
                files.extend(batch)

                page_token = response.get("nextPageToken")
                if not page_token or len(files) >= page_size:
                    break

            # Alt klasörleri de tara
            if recursive:
                folders = [f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"]
                for folder in folders:
                    sub_files = self.list_drive_files(
                        folder_id=folder["id"],
                        page_size=page_size,
                        recursive=True
                    )
                    files.extend(sub_files)

            logger.info(f"Google Drive'da {len(files)} dosya bulundu")
            return files

        except Exception as e:
            logger.error(f"Drive dosya listeleme hatası: {e}")
            return []

    def download_drive_file(
        self,
        file_id: str,
        mime_type: str
    ) -> Tuple[str, str]:
        """
        Google Drive dosyasını indir ve içeriğini döndür.
        
        Args:
            file_id: Drive dosya ID'si
            mime_type: Dosyanın MIME tipi
        
        Returns:
            (içerik_metni, dosya_adı) tuple'ı
        """
        if not self._authenticated:
            raise RuntimeError("Önce authenticate() çağrılmalıdır")

        try:
            from googleapiclient.http import MediaIoBaseDownload

            # Google Docs formatları için export gerekli
            if mime_type in self.GOOGLE_DOCS_EXPORT:
                export_mime, _ = self.GOOGLE_DOCS_EXPORT[mime_type]
                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )
            else:
                request = self.drive_service.files().get_media(fileId=file_id)

            # Dosyayı belleğe indir
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            # Dosya adını al
            file_meta = self.drive_service.files().get(
                fileId=file_id, fields="name"
            ).execute()
            filename = file_meta.get("name", f"file_{file_id}")

            content_bytes = buffer.getvalue()

            # İçeriği string'e çevir
            try:
                content = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                content = content_bytes.decode("latin-1", errors="replace")

            return content, filename

        except Exception as e:
            logger.error(f"Drive dosya indirme hatası ({file_id}): {e}")
            return "", f"file_{file_id}"

    def list_gmail_messages(self, max_results: int = 100) -> List[Dict]:
        """
        Gmail mesajlarını listele.
        
        Args:
            max_results: Maksimum mesaj sayısı
        
        Returns:
            Mesaj metadata listesi
        """
        if not self._authenticated:
            raise RuntimeError("Önce authenticate() çağrılmalıdır")

        try:
            messages = []
            page_token = None

            while len(messages) < max_results:
                response = self.gmail_service.users().messages().list(
                    userId="me",
                    maxResults=min(100, max_results - len(messages)),
                    pageToken=page_token
                ).execute()

                batch = response.get("messages", [])
                messages.extend(batch)

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            logger.info(f"Gmail'de {len(messages)} mesaj bulundu")
            return messages[:max_results]

        except Exception as e:
            logger.error(f"Gmail mesaj listeleme hatası: {e}")
            return []

    def get_gmail_content(self, message_id: str) -> str:
        """
        Gmail mesajının içeriğini al.
        
        Args:
            message_id: Gmail mesaj ID'si
        
        Returns:
            Mesaj içeriği (konu + gövde)
        """
        if not self._authenticated:
            raise RuntimeError("Önce authenticate() çağrılmalıdır")

        try:
            message = self.gmail_service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            content_parts = []
            headers = message.get("payload", {}).get("headers", [])

            # Başlıkları ekle
            for header in headers:
                if header["name"] in ["Subject", "From", "To", "Date", "Cc"]:
                    content_parts.append(f"{header['name']}: {header['value']}")

            # Gövdeyi çıkar
            body = self._extract_gmail_body(message.get("payload", {}))
            if body:
                content_parts.append(f"\n{body}")

            return "\n".join(content_parts)

        except Exception as e:
            logger.error(f"Gmail içerik alma hatası ({message_id}): {e}")
            return ""

    def _extract_gmail_body(self, payload: dict) -> str:
        """Gmail mesaj gövdesini recursive olarak çıkar"""
        body = ""

        if payload.get("body", {}).get("data"):
            data = payload["body"]["data"]
            try:
                body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            except Exception:
                pass

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type in ("text/plain", "text/html"):
                    part_data = part.get("body", {}).get("data", "")
                    if part_data:
                        try:
                            part_body = base64.urlsafe_b64decode(
                                part_data + "=="
                            ).decode("utf-8", errors="replace")
                            body += part_body
                        except Exception:
                            pass
                elif "parts" in part:
                    body += self._extract_gmail_body(part)

        return body


# ==========================================
# Microsoft Office 365 Tarayıcısı
# ==========================================

class Office365Scanner:
    """
    Microsoft Office 365 tarama motoru.
    OneDrive, SharePoint ve Outlook içeriklerini tarar.
    MSAL ve Microsoft Graph API kullanır.
    """

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    AUTHORITY_BASE = "https://login.microsoftonline.com"

    GRAPH_SCOPES = [
        "https://graph.microsoft.com/.default"
    ]

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Args:
            tenant_id: Microsoft Azure tenant ID'si
            client_id: Azure uygulama (client) ID'si
            client_secret: Azure uygulama gizli anahtarı
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        self._token_expires_at = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        MSAL ile Microsoft'a kimlik doğrula.
        
        Returns:
            True: Başarılı, False: Başarısız
        """
        try:
            token = self.get_access_token()
            self._authenticated = bool(token)
            if self._authenticated:
                logger.info("Microsoft 365 kimlik doğrulaması başarılı")
            return self._authenticated
        except Exception as e:
            logger.error(f"Microsoft kimlik doğrulama hatası: {e}")
            return False

    def get_access_token(self) -> str:
        """
        Microsoft Graph API için access token al (önbellekle).
        
        Returns:
            Bearer token string'i
        """
        # Token geçerliyse önbellekten dön
        if (self._access_token and self._token_expires_at and
                datetime.utcnow().timestamp() < self._token_expires_at - 60):
            return self._access_token

        try:
            import msal

            authority = f"{self.AUTHORITY_BASE}/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority
            )

            result = app.acquire_token_for_client(scopes=self.GRAPH_SCOPES)

            if "access_token" in result:
                self._access_token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow().timestamp() + expires_in
                return self._access_token
            else:
                error = result.get("error_description", "Bilinmeyen hata")
                logger.error(f"Microsoft token alma hatası: {error}")
                raise RuntimeError(f"Token alınamadı: {error}")

        except ImportError:
            logger.error("msal kurulu değil. 'pip install msal' komutunu çalıştırın.")
            raise
        except Exception as e:
            logger.error(f"Token alma hatası: {e}")
            raise

    def _graph_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict = None,
        stream: bool = False
    ):
        """Graph API'ye kimlik doğrulamalı istek gönder"""
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.GRAPH_API_BASE}/{endpoint.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            timeout=30
        )
        response.raise_for_status()
        return response

    def list_onedrive_files(
        self,
        folder_path: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict]:
        """
        OneDrive dosyalarını listele.
        
        Args:
            folder_path: Klasör yolu (None = root)
            recursive: Alt klasörleri de tara
        
        Returns:
            Dosya metadata listesi
        """
        try:
            if folder_path:
                endpoint = f"me/drive/root:/{folder_path}:/children"
            else:
                endpoint = "me/drive/root/children"

            files = []
            url = f"{self.GRAPH_API_BASE}/{endpoint}"
            token = self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}

            while url:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                items = data.get("value", [])
                files.extend(items)

                # Sonraki sayfa
                url = data.get("@odata.nextLink")

            # Klasörleri recursive tara
            if recursive:
                folders = [f for f in files if "folder" in f]
                for folder in folders:
                    folder_name = folder.get("name", "")
                    sub_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                    sub_files = self.list_onedrive_files(sub_path, recursive=True)
                    files.extend(sub_files)

            logger.info(f"OneDrive'da {len(files)} öğe bulundu")
            return files

        except Exception as e:
            logger.error(f"OneDrive dosya listeleme hatası: {e}")
            return []

    def download_onedrive_file(self, item_id: str) -> Tuple[bytes, str]:
        """
        OneDrive dosyasını indir.
        
        Args:
            item_id: OneDrive öğe ID'si
        
        Returns:
            (içerik_bytes, dosya_adı) tuple'ı
        """
        try:
            # Dosya adını al
            meta_response = self._graph_request(f"me/drive/items/{item_id}")
            meta = meta_response.json()
            filename = meta.get("name", f"file_{item_id}")

            # İçeriği indir
            content_response = self._graph_request(
                f"me/drive/items/{item_id}/content",
                stream=True
            )
            content = content_response.content

            return content, filename

        except Exception as e:
            logger.error(f"OneDrive dosya indirme hatası ({item_id}): {e}")
            return b"", f"file_{item_id}"

    def list_sharepoint_files(self, site_url: str) -> List[Dict]:
        """
        SharePoint site dosyalarını listele.
        
        Args:
            site_url: SharePoint site URL'si (örn: contoso.sharepoint.com:/sites/MySite)
        
        Returns:
            Dosya metadata listesi
        """
        try:
            # Site ID'sini al
            site_endpoint = f"sites/{site_url}"
            site_response = self._graph_request(site_endpoint)
            site_id = site_response.json().get("id")

            if not site_id:
                logger.error(f"Site ID alınamadı: {site_url}")
                return []

            # Drive'ları listele
            drives_response = self._graph_request(f"sites/{site_id}/drives")
            drives = drives_response.json().get("value", [])

            all_files = []
            for drive in drives:
                drive_id = drive.get("id")
                # Drive root'undaki dosyaları listele
                files_response = self._graph_request(
                    f"sites/{site_id}/drives/{drive_id}/root/children"
                )
                files = files_response.json().get("value", [])
                all_files.extend(files)

            logger.info(f"SharePoint'te {len(all_files)} öğe bulundu")
            return all_files

        except Exception as e:
            logger.error(f"SharePoint dosya listeleme hatası: {e}")
            return []

    def list_outlook_emails(self, max_results: int = 100) -> List[Dict]:
        """
        Outlook/Exchange e-postalarını listele.
        
        Args:
            max_results: Maksimum e-posta sayısı
        
        Returns:
            E-posta metadata listesi
        """
        try:
            emails = []
            top = min(100, max_results)
            endpoint = f"me/messages?$top={top}&$select=id,subject,from,receivedDateTime,hasAttachments"

            token = self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.GRAPH_API_BASE}/{endpoint}"

            while url and len(emails) < max_results:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                emails.extend(data.get("value", []))
                url = data.get("@odata.nextLink")

            logger.info(f"Outlook'ta {len(emails)} e-posta bulundu")
            return emails[:max_results]

        except Exception as e:
            logger.error(f"Outlook e-posta listeleme hatası: {e}")
            return []

    def get_email_content(self, message_id: str) -> str:
        """
        Outlook e-posta içeriğini al.
        
        Args:
            message_id: Graph API mesaj ID'si
        
        Returns:
            E-posta içeriği (konu + gövde + ekler)
        """
        try:
            response = self._graph_request(
                f"me/messages/{message_id}?$select=subject,from,toRecipients,ccRecipients,body,receivedDateTime"
            )
            message = response.json()

            content_parts = []

            # Başlıklar
            content_parts.append(f"Konu: {message.get('subject', 'Yok')}")
            content_parts.append(f"Gönderen: {message.get('from', {}).get('emailAddress', {}).get('address', 'Bilinmiyor')}")

            to_recipients = [
                r.get("emailAddress", {}).get("address", "")
                for r in message.get("toRecipients", [])
            ]
            if to_recipients:
                content_parts.append(f"Alıcılar: {', '.join(to_recipients)}")

            content_parts.append(f"Tarih: {message.get('receivedDateTime', 'Bilinmiyor')}")

            # Gövde
            body = message.get("body", {})
            content_type = body.get("contentType", "text")
            body_content = body.get("content", "")

            if content_type == "html":
                # HTML etiketlerini temizle
                import re
                body_content = re.sub(r'<[^>]+>', ' ', body_content)
                body_content = re.sub(r'\s+', ' ', body_content).strip()

            content_parts.append(f"\n{body_content}")

            return "\n".join(content_parts)

        except Exception as e:
            logger.error(f"Outlook e-posta içerik alma hatası ({message_id}): {e}")
            return ""

    def get_user_info(self) -> Dict:
        """Kimlik doğrulanan kullanıcının bilgilerini al"""
        try:
            response = self._graph_request("me")
            return response.json()
        except Exception as e:
            logger.error(f"Kullanıcı bilgisi alma hatası: {e}")
            return {}
