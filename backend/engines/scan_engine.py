"""
DLP Sistemi - Dosya Tarama Motoru
Yerel dosya sistemi ve yüklenen dosyalar için içerik tarama motoru
"""

import os
import io
import logging
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Generator
from datetime import datetime

import chardet

from engines.detection_patterns import PatternMatch, detect_patterns, calculate_risk_score, get_data_classification

logger = logging.getLogger(__name__)

# Maksimum dosya boyutu (50 MB)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

# Desteklenen dosya uzantıları
SUPPORTED_TEXT_EXTENSIONS = {
    ".txt", ".csv", ".json", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".htm", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf",
    ".log", ".sql", ".sh", ".bat", ".ps1", ".rb", ".php", ".java",
    ".c", ".cpp", ".h", ".css", ".scss", ".less", ".env", ".toml",
    ".rst", ".tex", ".rtf"
}

SUPPORTED_OFFICE_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"
}

ALL_SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_OFFICE_EXTENSIONS


# ==========================================
# Dosya Okuma Fonksiyonları
# ==========================================

def _read_pdf(file_path: str) -> str:
    """PDF dosyasından metin çıkar"""
    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"[Sayfa {page_num + 1}]\n{text}")
                except Exception as e:
                    logger.warning(f"PDF sayfa {page_num + 1} okunamadı: {e}")
        return "\n\n".join(text_parts)
    except ImportError:
        logger.error("PyPDF2 kurulu değil. 'pip install PyPDF2' komutunu çalıştırın.")
        return ""
    except Exception as e:
        logger.error(f"PDF okuma hatası ({file_path}): {e}")
        return ""


def _read_docx(file_path: str) -> str:
    """Word belgesi (.docx) metnini çıkar"""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []

        # Paragraflar
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Tablolar
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if row_text:
                    text_parts.append(row_text)

        return "\n".join(text_parts)
    except ImportError:
        logger.error("python-docx kurulu değil. 'pip install python-docx' komutunu çalıştırın.")
        return ""
    except Exception as e:
        logger.error(f"DOCX okuma hatası ({file_path}): {e}")
        return ""


def _read_xlsx(file_path: str) -> str:
    """Excel dosyası (.xlsx) metnini çıkar"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        text_parts = []

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            text_parts.append(f"[Sayfa: {sheet_name}]")
            for row in sheet.iter_rows(values_only=True):
                row_text = " | ".join(
                    str(cell) for cell in row if cell is not None
                )
                if row_text.strip():
                    text_parts.append(row_text)

        wb.close()
        return "\n".join(text_parts)
    except ImportError:
        logger.error("openpyxl kurulu değil. 'pip install openpyxl' komutunu çalıştırın.")
        return ""
    except Exception as e:
        logger.error(f"XLSX okuma hatası ({file_path}): {e}")
        return ""


def _read_text_file(file_path: str) -> str:
    """Metin dosyasını oku, encoding'i otomatik tespit et"""
    try:
        # Önce encoding'i tespit et
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        if not raw_bytes:
            return ""

        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding") or "utf-8"
        confidence = detected.get("confidence", 0)

        # Düşük güven durumunda UTF-8 dene
        if confidence < 0.7:
            encoding = "utf-8"

        try:
            return raw_bytes.decode(encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return raw_bytes.decode("utf-8", errors="replace")

    except Exception as e:
        logger.error(f"Metin dosyası okuma hatası ({file_path}): {e}")
        return ""


def _read_pdf_from_bytes(content: bytes) -> str:
    """Bytes'tan PDF içeriği oku"""
    try:
        import PyPDF2
        text_parts = []
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Sayfa {page_num + 1}]\n{text}")
            except Exception as e:
                logger.warning(f"PDF sayfa {page_num + 1} okunamadı: {e}")
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF bytes okuma hatası: {e}")
        return ""


def _read_docx_from_bytes(content: bytes) -> str:
    """Bytes'tan DOCX içeriği oku"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if row_text:
                    text_parts.append(row_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"DOCX bytes okuma hatası: {e}")
        return ""


def _read_xlsx_from_bytes(content: bytes) -> str:
    """Bytes'tan XLSX içeriği oku"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        text_parts = []
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            text_parts.append(f"[Sayfa: {sheet_name}]")
            for row in sheet.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) for cell in row if cell is not None)
                if row_text.strip():
                    text_parts.append(row_text)
        wb.close()
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"XLSX bytes okuma hatası: {e}")
        return ""


# ==========================================
# Ana Tarama Motoru Sınıfı
# ==========================================

class ScanEngine:
    """
    DLP Dosya Tarama Motoru.
    Yerel dosya sistemi taraması, metin analizi ve örüntü tespiti sağlar.
    """

    def __init__(self, max_file_size: int = MAX_FILE_SIZE_BYTES):
        self.max_file_size = max_file_size
        logger.info(f"Tarama Motoru başlatıldı. Maks dosya boyutu: {max_file_size // (1024*1024)} MB")

    def get_file_info(self, file_path: str) -> Dict:
        """
        Dosya hakkında temel bilgileri döndür.
        
        Returns:
            size, type, encoding, extension, mime_type içeren dict
        """
        path = Path(file_path)
        info = {
            "path": str(path.absolute()),
            "name": path.name,
            "extension": path.suffix.lower(),
            "size": 0,
            "size_human": "0 B",
            "mime_type": "unknown",
            "encoding": "unknown",
            "exists": path.exists(),
            "is_supported": False,
        }

        if not path.exists():
            return info

        stat = path.stat()
        size = stat.st_size
        info["size"] = size
        info["size_human"] = _format_size(size)

        # MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        info["mime_type"] = mime_type or "application/octet-stream"

        # Desteklenip desteklenmediği
        info["is_supported"] = path.suffix.lower() in ALL_SUPPORTED_EXTENSIONS

        # Metin dosyaları için encoding tespiti
        if path.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS:
            try:
                with open(file_path, "rb") as f:
                    sample = f.read(min(8192, size))
                detected = chardet.detect(sample)
                info["encoding"] = detected.get("encoding", "utf-8") or "utf-8"
                info["encoding_confidence"] = detected.get("confidence", 0)
            except Exception:
                info["encoding"] = "utf-8"

        return info

    def read_file(self, file_path: str) -> str:
        """
        Bir dosyayı okuyup içeriğini string olarak döndür.
        Dosya tipine göre uygun okuyucu kullanır.
        
        Args:
            file_path: Okunacak dosyanın yolu
        
        Returns:
            Dosya içeriği (string)
        
        Raises:
            FileNotFoundError: Dosya bulunamadıysa
            ValueError: Dosya çok büyük veya desteklenmiyor ise
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

        # Boyut kontrolü
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(
                f"Dosya çok büyük: {_format_size(file_size)} "
                f"(Maks: {_format_size(self.max_file_size)})"
            )

        if file_size == 0:
            return ""

        ext = path.suffix.lower()

        if ext == ".pdf":
            return _read_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return _read_docx(file_path)
        elif ext in (".xlsx", ".xls"):
            return _read_xlsx(file_path)
        elif ext in SUPPORTED_TEXT_EXTENSIONS:
            return _read_text_file(file_path)
        else:
            # Bilinmeyen uzantı - metin olarak okumayı dene
            try:
                return _read_text_file(file_path)
            except Exception:
                raise ValueError(f"Desteklenmeyen dosya tipi: {ext}")

    def read_from_bytes(self, content: bytes, filename: str) -> str:
        """
        Bytes içeriğini okuyup string döndür (yüklenen dosyalar için).
        
        Args:
            content: Dosya içeriği (bytes)
            filename: Dosya adı (uzantı tespiti için)
        
        Returns:
            Dosya içeriği (string)
        """
        if len(content) > self.max_file_size:
            raise ValueError(
                f"Dosya çok büyük: {_format_size(len(content))} "
                f"(Maks: {_format_size(self.max_file_size)})"
            )

        if not content:
            return ""

        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            return _read_pdf_from_bytes(content)
        elif ext in (".docx", ".doc"):
            return _read_docx_from_bytes(content)
        elif ext in (".xlsx", ".xls"):
            return _read_xlsx_from_bytes(content)
        else:
            # Metin olarak oku
            detected = chardet.detect(content[:8192])
            encoding = detected.get("encoding") or "utf-8"
            try:
                return content.decode(encoding, errors="replace")
            except (LookupError, UnicodeDecodeError):
                return content.decode("utf-8", errors="replace")

    def scan_text(
        self,
        text: str,
        pattern_keys: Optional[List[str]] = None
    ) -> List[PatternMatch]:
        """
        Metin içeriğini örüntüler için tara.
        
        Args:
            text: Taranacak metin
            pattern_keys: Kontrol edilecek örüntü anahtarları (None = tümü)
        
        Returns:
            PatternMatch listesi
        """
        if not text:
            return []
        return detect_patterns(text, pattern_keys)

    def scan_file(
        self,
        file_path: str,
        pattern_keys: Optional[List[str]] = None
    ) -> Dict:
        """
        Bir dosyayı tara ve sonuçları döndür.
        
        Args:
            file_path: Taranacak dosyanın yolu
            pattern_keys: Kontrol edilecek örüntü anahtarları
        
        Returns:
            Tarama sonuçlarını içeren dict:
            {
                file_path, file_name, file_size, file_type, status,
                detected_patterns, risk_score, classification,
                error_message, scanned_at
            }
        """
        path = Path(file_path)
        result = {
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size": 0,
            "file_type": path.suffix.lower(),
            "status": "clean",
            "detected_patterns": [],
            "risk_score": 0,
            "classification": "Temiz",
            "error_message": None,
            "scanned_at": datetime.utcnow().isoformat(),
        }

        try:
            file_info = self.get_file_info(file_path)
            result["file_size"] = file_info["size"]

            if not file_info["exists"]:
                result["status"] = "error"
                result["error_message"] = "Dosya bulunamadı"
                return result

            if not file_info["is_supported"]:
                result["status"] = "skipped"
                result["error_message"] = f"Desteklenmeyen dosya tipi: {file_info['extension']}"
                return result

            # Dosyayı oku
            text = self.read_file(file_path)

            if not text:
                result["status"] = "clean"
                result["error_message"] = "Dosya boş veya okunamadı"
                return result

            # Örüntüleri tara
            matches = self.scan_text(text, pattern_keys)

            result["detected_patterns"] = [m.to_dict() for m in matches]
            result["risk_score"] = calculate_risk_score(matches)
            result["classification"] = get_data_classification(result["risk_score"])
            result["status"] = "threat" if matches else "clean"

        except ValueError as e:
            result["status"] = "error"
            result["error_message"] = str(e)
        except Exception as e:
            logger.exception(f"Dosya tarama hatası ({file_path}): {e}")
            result["status"] = "error"
            result["error_message"] = f"Beklenmeyen hata: {str(e)}"

        return result

    def scan_file_from_bytes(
        self,
        content: bytes,
        filename: str,
        pattern_keys: Optional[List[str]] = None
    ) -> Dict:
        """
        Bytes içeriğini tara (API üzerinden yüklenen dosyalar için).
        
        Args:
            content: Dosya içeriği
            filename: Dosya adı
            pattern_keys: Kontrol edilecek örüntü anahtarları
        
        Returns:
            Tarama sonuçları dict
        """
        result = {
            "file_path": None,
            "file_name": filename,
            "file_size": len(content),
            "file_type": Path(filename).suffix.lower(),
            "status": "clean",
            "detected_patterns": [],
            "risk_score": 0,
            "classification": "Temiz",
            "error_message": None,
            "scanned_at": datetime.utcnow().isoformat(),
        }

        try:
            text = self.read_from_bytes(content, filename)

            if not text:
                result["status"] = "clean"
                result["error_message"] = "Dosya boş veya okunamadı"
                return result

            matches = self.scan_text(text, pattern_keys)

            result["detected_patterns"] = [m.to_dict() for m in matches]
            result["risk_score"] = calculate_risk_score(matches)
            result["classification"] = get_data_classification(result["risk_score"])
            result["status"] = "threat" if matches else "clean"

        except ValueError as e:
            result["status"] = "error"
            result["error_message"] = str(e)
        except Exception as e:
            logger.exception(f"Bytes tarama hatası ({filename}): {e}")
            result["status"] = "error"
            result["error_message"] = f"Beklenmeyen hata: {str(e)}"

        return result

    def scan_directory(
        self,
        dir_path: str,
        pattern_keys: Optional[List[str]] = None,
        recursive: bool = True,
        excluded_dirs: Optional[List[str]] = None
    ) -> Generator[Dict, None, None]:
        """
        Bir dizindeki tüm dosyaları tara (generator).
        
        Args:
            dir_path: Taranacak dizin yolu
            pattern_keys: Kontrol edilecek örüntü anahtarları
            recursive: Alt dizinleri de tara
            excluded_dirs: Hariç tutulacak dizin adları
        
        Yields:
            Her dosya için tarama sonuçları
        """
        dir_path_obj = Path(dir_path)

        if not dir_path_obj.exists():
            logger.error(f"Dizin bulunamadı: {dir_path}")
            return

        if not dir_path_obj.is_dir():
            logger.error(f"Geçerli bir dizin değil: {dir_path}")
            return

        excluded = set(excluded_dirs or [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".env", "dist", "build", ".idea", ".vscode"
        ])

        # Dosya listesini oluştur
        if recursive:
            file_iter = dir_path_obj.rglob("*")
        else:
            file_iter = dir_path_obj.glob("*")

        for file_path in file_iter:
            # Hariç tutulan dizinleri atla
            if any(exc in file_path.parts for exc in excluded):
                continue

            if not file_path.is_file():
                continue

            # Desteklenmeyen uzantıları atla
            if file_path.suffix.lower() not in ALL_SUPPORTED_EXTENSIONS:
                continue

            yield self.scan_file(str(file_path), pattern_keys)

    def count_files(
        self,
        dir_path: str,
        recursive: bool = True,
        excluded_dirs: Optional[List[str]] = None
    ) -> int:
        """Bir dizindeki taranabilir dosya sayısını say"""
        dir_path_obj = Path(dir_path)

        if not dir_path_obj.exists() or not dir_path_obj.is_dir():
            return 0

        excluded = set(excluded_dirs or [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".env", "dist", "build", ".idea", ".vscode"
        ])

        count = 0
        if recursive:
            file_iter = dir_path_obj.rglob("*")
        else:
            file_iter = dir_path_obj.glob("*")

        for file_path in file_iter:
            if any(exc in file_path.parts for exc in excluded):
                continue
            if file_path.is_file() and file_path.suffix.lower() in ALL_SUPPORTED_EXTENSIONS:
                count += 1

        return count


# ==========================================
# Yardımcı Fonksiyonlar
# ==========================================

def _format_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevir"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# Singleton instance
scan_engine = ScanEngine()
