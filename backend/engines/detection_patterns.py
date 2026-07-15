"""
DLP Sistemi - Hassas Veri Tespit Örüntüleri
Türk ve uluslararası hassas veri türleri için regex ve doğrulama kuralları
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict
import logging

logger = logging.getLogger(__name__)


# ==========================================
# Veri Sınıfları
# ==========================================

@dataclass
class PatternMatch:
    """Tespit edilen bir örüntüyü temsil eder"""
    pattern_key: str
    pattern_name: str
    matched_text: str
    risk_score: int
    category: str
    line_number: Optional[int] = None
    context: Optional[str] = None  # Eşleşme etrafındaki metin

    def to_dict(self) -> dict:
        return {
            "pattern_key": self.pattern_key,
            "pattern_name": self.pattern_name,
            "matched_text": self.mask_sensitive(self.matched_text),
            "risk_score": self.risk_score,
            "category": self.category,
            "line_number": self.line_number,
        }

    def mask_sensitive(self, text: str) -> str:
        """Hassas verinin ortasını maskele"""
        if len(text) <= 4:
            return "*" * len(text)
        visible = 2
        return text[:visible] + "*" * (len(text) - visible * 2) + text[-visible:]


@dataclass
class DetectionPattern:
    """Bir tespit örüntüsünü tanımlar"""
    key: str
    name: str
    category: str
    risk_score: int
    pattern: Optional[str] = None  # Regex örüntüsü
    keywords: List[str] = field(default_factory=list)
    validator: Optional[Callable] = None  # Ek doğrulama fonksiyonu
    description: str = ""
    compiled_regex: Optional[re.Pattern] = None

    def __post_init__(self):
        """Regex'i önceden derle"""
        if self.pattern:
            try:
                self.compiled_regex = re.compile(
                    self.pattern,
                    re.IGNORECASE | re.UNICODE
                )
            except re.error as e:
                logger.error(f"Regex derleme hatası ({self.key}): {e}")
                self.compiled_regex = None


# ==========================================
# Doğrulama Fonksiyonları
# ==========================================

def validate_tc(tc: str) -> bool:
    """
    TC Kimlik Numarası doğrulama algoritması.
    
    Kurallar:
    1. 11 haneli sayı olmalı
    2. İlk hane 0 olamaz
    3. Checksum doğrulaması geçmeli
    """
    # Sadece rakamları al
    tc = re.sub(r'\D', '', tc)
    
    if len(tc) != 11:
        return False
    
    if tc[0] == '0':
        return False
    
    # Tüm aynı rakamlardan oluşamaz
    if len(set(tc)) == 1:
        return False
    
    digits = [int(d) for d in tc]
    
    # 10. hane doğrulaması
    # (1,3,5,7,9. hanelerin toplamı * 7 - 2,4,6,8. hanelerin toplamı) mod 10
    tek_toplam = sum(digits[i] for i in range(0, 9, 2))   # 1,3,5,7,9. haneler
    cift_toplam = sum(digits[i] for i in range(1, 8, 2))  # 2,4,6,8. haneler
    
    expected_10th = (tek_toplam * 7 - cift_toplam) % 10
    if digits[9] != expected_10th:
        return False
    
    # 11. hane doğrulaması
    # İlk 10 hanenin toplamının mod 10'u
    expected_11th = sum(digits[:10]) % 10
    if digits[10] != expected_11th:
        return False
    
    return True


def luhn_check(card_number: str) -> bool:
    """
    Luhn algoritması ile kredi kartı doğrulama.
    Çoğu kredi/banka kartı bu algoritmayı kullanır.
    """
    # Sadece rakamları al
    card = re.sub(r'\D', '', card_number)
    
    if len(card) < 13 or len(card) > 19:
        return False
    
    digits = [int(d) for d in card]
    
    # Luhn algoritması
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            doubled = digit * 2
            if doubled > 9:
                doubled -= 9
            checksum += doubled
        else:
            checksum += digit
    
    return checksum % 10 == 0


def validate_iban_tr(iban: str) -> bool:
    """Türkiye IBAN doğrulama (TR ile başlayan 26 karakter)"""
    iban = iban.replace(" ", "").upper()
    
    if not iban.startswith("TR"):
        return False
    
    if len(iban) != 26:
        return False
    
    # Mod 97 doğrulaması
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        elif char.isalpha():
            numeric += str(ord(char) - ord('A') + 10)
        else:
            return False
    
    return int(numeric) % 97 == 1


def validate_vergi_no(vergi_no: str) -> bool:
    """
    Türkiye Vergi Numarası doğrulama (10 hane).
    """
    vergi_no = re.sub(r'\D', '', vergi_no)
    
    if len(vergi_no) != 10:
        return False
    
    # Basit checksum doğrulaması
    digits = [int(d) for d in vergi_no]
    
    checksum = 0
    for i in range(9):
        tmp = (digits[i] + (9 - i)) % 10
        if tmp != 0:
            tmp = (tmp * (2 ** (9 - i))) % 9
            if tmp == 0:
                tmp = 9
        checksum += tmp
    
    expected = (10 - (checksum % 10)) % 10
    return digits[9] == expected


def validate_password_hash(text: str) -> bool:
    """Çeşitli hash formatlarını kontrol et"""
    # bcrypt, MD5, SHA hash formatları
    patterns = [
        r'^\$2[ayb]\$\d+\$',  # bcrypt
        r'^[a-f0-9]{32}$',    # MD5
        r'^[a-f0-9]{40}$',    # SHA1
        r'^[a-f0-9]{64}$',    # SHA256
    ]
    return any(re.match(p, text, re.IGNORECASE) for p in patterns)


# ==========================================
# Örüntü Tanımları
# ==========================================

PATTERNS: Dict[str, DetectionPattern] = {
    # ----------------------------------------
    # Türkiye Kimlik Bilgileri
    # ----------------------------------------
    "tc_kimlik_no": DetectionPattern(
        key="tc_kimlik_no",
        name="TC Kimlik Numarası",
        category="kimlik",
        risk_score=90,
        pattern=r'\b([1-9][0-9]{10})\b',
        keywords=["tc kimlik", "tcno", "t.c. kimlik", "nüfus cüzdanı", "kimlik no"],
        validator=lambda x: validate_tc(re.sub(r'\D', '', x)),
        description="11 haneli Türkiye Cumhuriyeti Kimlik Numarası"
    ),

    "vergi_no": DetectionPattern(
        key="vergi_no",
        name="Vergi Kimlik Numarası",
        category="kimlik",
        risk_score=75,
        pattern=r'\b(\d{10})\b',
        keywords=["vergi no", "vkn", "vergi kimlik", "vergi numarası", "tax id"],
        validator=lambda x: validate_vergi_no(re.sub(r'\D', '', x)),
        description="10 haneli Türkiye Vergi Kimlik Numarası"
    ),

    "passport_no": DetectionPattern(
        key="passport_no",
        name="Pasaport Numarası",
        category="kimlik",
        risk_score=85,
        pattern=r'\b([A-Z]{1,2}[0-9]{6,9})\b',
        keywords=["pasaport", "passport", "seyahat belgesi"],
        description="Uluslararası pasaport numarası formatı"
    ),

    # ----------------------------------------
    # Finansal Bilgiler
    # ----------------------------------------
    "kredi_karti": DetectionPattern(
        key="kredi_karti",
        name="Kredi/Banka Kartı Numarası",
        category="finansal",
        risk_score=95,
        pattern=r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        keywords=["kredi kartı", "banka kartı", "kart numarası", "card number", "cvv", "cvc"],
        validator=lambda x: luhn_check(re.sub(r'\D', '', x)),
        description="Visa, Mastercard, Amex vb. kart numaraları (Luhn doğrulamalı)"
    ),

    "iban_tr": DetectionPattern(
        key="iban_tr",
        name="Türkiye IBAN",
        category="finansal",
        risk_score=80,
        pattern=r'\bTR\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}\b',
        keywords=["iban", "banka hesap", "hesap numarası", "swift"],
        validator=lambda x: validate_iban_tr(x),
        description="TR ile başlayan 26 haneli IBAN numarası"
    ),

    "banka_hesap": DetectionPattern(
        key="banka_hesap",
        name="Banka Hesap Numarası",
        category="finansal",
        risk_score=70,
        pattern=r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}(?:[\s-]?\d{2})?\b',
        keywords=["hesap no", "hesap numarası", "account number", "account no", "iban"],
        description="Genel banka hesap numarası formatları"
    ),

    # ----------------------------------------
    # İletişim Bilgileri
    # ----------------------------------------
    "email": DetectionPattern(
        key="email",
        name="E-posta Adresi",
        category="iletisim",
        risk_score=40,
        pattern=r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        keywords=["e-posta", "email", "mail", "@"],
        description="Geçerli e-posta adresi formatı"
    ),

    "telefon_tr": DetectionPattern(
        key="telefon_tr",
        name="Türkiye Telefon Numarası",
        category="iletisim",
        risk_score=50,
        pattern=r'\b(?:\+90|0090|0)[\s.-]?(?:5[0-9]{2}|[2-4][0-9]{2})[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b',
        keywords=["telefon", "gsm", "cep", "telefon no", "phone", "mobile"],
        description="Türkiye telefon ve cep telefonu numaraları"
    ),

    # ----------------------------------------
    # Teknik/Sistem Bilgileri
    # ----------------------------------------
    "ip_adresi": DetectionPattern(
        key="ip_adresi",
        name="IP Adresi",
        category="teknik",
        risk_score=35,
        pattern=r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        keywords=["ip adresi", "ip address", "subnet", "network"],
        description="IPv4 adresi (özel IP aralıkları dahil)"
    ),

    "api_key": DetectionPattern(
        key="api_key",
        name="API Anahtarı",
        category="teknik",
        risk_score=85,
        pattern=r'(?i)(?:api[_\-]?key|access[_\-]?token|auth[_\-]?token|secret[_\-]?key|private[_\-]?key|bearer)\s*[=:]\s*[\'"]?([a-zA-Z0-9+/\-_]{20,})[\'"]?',
        keywords=["api key", "api_key", "access_token", "secret_key", "bearer token", "auth_token"],
        description="API anahtarları ve erişim token'ları"
    ),

    "sifre_hash": DetectionPattern(
        key="sifre_hash",
        name="Şifre/Hash Değeri",
        category="teknik",
        risk_score=80,
        pattern=r'(?i)(?:password|passwd|pwd|sifre|şifre|parola)\s*[=:]\s*[\'"]?([^\s\'"]{8,})[\'"]?',
        keywords=["password", "passwd", "pwd", "şifre", "parola", "secret"],
        description="Düz metin veya hashlenmiş şifre değerleri"
    ),

    # ----------------------------------------
    # Sağlık Bilgileri
    # ----------------------------------------
    "saglik_bilgisi": DetectionPattern(
        key="saglik_bilgisi",
        name="Sağlık Bilgisi",
        category="saglik",
        risk_score=85,
        pattern=None,
        keywords=[
            "tanı", "diagnosis", "ilaç", "medication", "reçete", "prescription",
            "hasta", "patient", "klinik", "clinic", "hastane", "hospital",
            "kan grubu", "blood type", "alerji", "allergy", "ameliyat",
            "psikiyatri", "psychiatry", "psikoloji", "psychology", "tıbbi rapor",
            "sağlık raporu", "medical report", "tcno", "doğum tarihi"
        ],
        description="Tıbbi kayıt ve sağlık bilgileri (KVKK kapsamında özel veri)"
    ),

    # ----------------------------------------
    # Gizlilik İşaretleri
    # ----------------------------------------
    "gizli_kelimeler": DetectionPattern(
        key="gizli_kelimeler",
        name="Gizlilik Etiketi",
        category="gizlilik",
        risk_score=60,
        pattern=r'\b(gizli|confidential|secret|private|internal only|dahili|strictly confidential|top secret|restricted|sınırlı erişim)\b',
        keywords=["gizli", "confidential", "secret", "private", "internal", "dahili"],
        description="Gizlilik etiketleri ve işaretleri"
    ),

    # ----------------------------------------
    # Kimlik Bilgileri (Genel)
    # ----------------------------------------
    "dogum_tarihi": DetectionPattern(
        key="dogum_tarihi",
        name="Doğum Tarihi",
        category="kimlik",
        risk_score=50,
        pattern=r'\b(?:0?[1-9]|[12][0-9]|3[01])[/\.\-](?:0?[1-9]|1[0-2])[/\.\-](?:19|20)\d{2}\b',
        keywords=["doğum tarihi", "d.o.b", "date of birth", "birthday", "d.t."],
        description="DD/MM/YYYY formatında doğum tarihi"
    ),

    "adres_bilgisi": DetectionPattern(
        key="adres_bilgisi",
        name="Adres Bilgisi",
        category="kimlik",
        risk_score=45,
        pattern=None,
        keywords=[
            "sokak", "cadde", "bulvar", "mahalle", "posta kodu", "zip code",
            "ilçe", "il", "semt", "apt.", "daire", "kat", "no:", "kapı no"
        ],
        description="Fiziksel adres bilgileri"
    ),

    # ----------------------------------------
    # Şirket Bilgileri
    # ----------------------------------------
    "ticaret_sicil": DetectionPattern(
        key="ticaret_sicil",
        name="Ticaret Sicil Numarası",
        category="sirket",
        risk_score=55,
        pattern=r'\b(?:ticaret\s*sicil|sicil\s*no)[:\s]*(\d{4,8})\b',
        keywords=["ticaret sicil", "sicil numarası", "mersis", "trade registry"],
        description="Ticaret sicil ve MERSIS numaraları"
    ),
}


# ==========================================
# Ana Tespit Fonksiyonları
# ==========================================

def detect_patterns(
    text: str,
    pattern_keys: Optional[List[str]] = None
) -> List[PatternMatch]:
    """
    Metin içinde hassas veri örüntülerini tespit et.
    
    Args:
        text: Taranacak metin
        pattern_keys: Kontrol edilecek örüntü anahtarları (None = tümü)
    
    Returns:
        Tespit edilen örüntülerin listesi
    """
    matches = []
    
    if not text or not text.strip():
        return matches
    
    # Taranacak örüntüleri seç
    patterns_to_check = {}
    if pattern_keys:
        for key in pattern_keys:
            if key in PATTERNS:
                patterns_to_check[key] = PATTERNS[key]
            else:
                logger.warning(f"Bilinmeyen örüntü anahtarı: {key}")
    else:
        patterns_to_check = PATTERNS
    
    # Metin satırlarına böl (satır numarası için)
    lines = text.split('\n')
    
    for pattern_key, pattern_def in patterns_to_check.items():
        # Regex tabanlı tespit
        if pattern_def.compiled_regex:
            for line_num, line in enumerate(lines, start=1):
                for match in pattern_def.compiled_regex.finditer(line):
                    matched_text = match.group(0)
                    
                    # Ek doğrulama varsa uygula
                    if pattern_def.validator:
                        try:
                            if not pattern_def.validator(matched_text):
                                continue
                        except Exception:
                            continue
                    
                    pm = PatternMatch(
                        pattern_key=pattern_key,
                        pattern_name=pattern_def.name,
                        matched_text=matched_text,
                        risk_score=pattern_def.risk_score,
                        category=pattern_def.category,
                        line_number=line_num,
                        context=_get_context(line, match.start(), match.end())
                    )
                    matches.append(pm)
        
        # Anahtar kelime tabanlı tespit
        if pattern_def.keywords:
            text_lower = text.lower()
            for keyword in pattern_def.keywords:
                if keyword.lower() in text_lower:
                    # Anahtar kelime konumunu bul
                    idx = text_lower.find(keyword.lower())
                    line_num = text[:idx].count('\n') + 1
                    
                    # Aynı örüntü için regex eşleşmesi yoksa ekle
                    already_found = any(
                        m.pattern_key == pattern_key for m in matches
                    )
                    
                    if not already_found:
                        pm = PatternMatch(
                            pattern_key=pattern_key,
                            pattern_name=pattern_def.name,
                            matched_text=keyword,
                            risk_score=max(pattern_def.risk_score - 20, 10),  # Anahtar kelime skoru daha düşük
                            category=pattern_def.category,
                            line_number=line_num,
                            context=text[max(0, idx-30):idx+len(keyword)+30]
                        )
                        matches.append(pm)
                        break  # Her örüntü için bir kez ekle
    
    # Tekrarlı eşleşmeleri filtrele (aynı metin, aynı örüntü)
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m.pattern_key, m.matched_text, m.line_number)
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)
    
    return unique_matches


def _get_context(line: str, start: int, end: int, context_chars: int = 40) -> str:
    """Eşleşme etrafındaki bağlam metnini döndür"""
    ctx_start = max(0, start - context_chars)
    ctx_end = min(len(line), end + context_chars)
    context = line[ctx_start:ctx_end]
    if ctx_start > 0:
        context = "..." + context
    if ctx_end < len(line):
        context = context + "..."
    return context


def calculate_risk_score(matches: List[PatternMatch]) -> int:
    """
    Eşleşme listesinden toplam risk skoru hesapla.
    Birden fazla eşleşme olduğunda logaritmik artış uygular.
    
    Returns:
        0-100 arası risk skoru
    """
    if not matches:
        return 0
    
    # En yüksek bireysel skoru al
    max_score = max(m.risk_score for m in matches)
    
    # Birden fazla farklı örüntü varsa bonus
    unique_patterns = len(set(m.pattern_key for m in matches))
    if unique_patterns > 1:
        bonus = min(unique_patterns * 5, 20)
        max_score = min(max_score + bonus, 100)
    
    # Çok sayıda eşleşme varsa küçük bonus
    if len(matches) > 5:
        max_score = min(max_score + 5, 100)
    
    return int(max_score)


def get_data_classification(risk_score: int) -> str:
    """
    Risk skoruna göre veri sınıflandırma kategorisi döndür.
    
    Returns:
        "Kritik", "Yüksek", "Orta", "Düşük", veya "Temiz"
    """
    if risk_score >= 85:
        return "Kritik"
    elif risk_score >= 70:
        return "Yüksek"
    elif risk_score >= 40:
        return "Orta"
    elif risk_score > 0:
        return "Düşük"
    else:
        return "Temiz"


def get_all_pattern_info() -> List[dict]:
    """Tüm örüntülerin bilgilerini listele"""
    return [
        {
            "key": p.key,
            "name": p.name,
            "category": p.category,
            "risk_score": p.risk_score,
            "description": p.description,
            "has_regex": p.pattern is not None,
            "has_keywords": len(p.keywords) > 0,
            "has_validator": p.validator is not None,
        }
        for p in PATTERNS.values()
    ]


def get_categories() -> List[str]:
    """Mevcut kategorilerin listesini döndür"""
    return list(set(p.category for p in PATTERNS.values()))
