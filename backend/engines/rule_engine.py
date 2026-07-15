"""
DLP Sistemi - Politika Kural Değerlendirme Motoru
Tarama sonuçlarını politikalarla karşılaştırır ve aksiyon belirler
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from engines.detection_patterns import PatternMatch, calculate_risk_score

logger = logging.getLogger(__name__)


# ==========================================
# Veri Sınıfları
# ==========================================

@dataclass
class PolicyEvalResult:
    """Politika değerlendirmesi sonucu"""
    policy_id: int
    policy_name: str
    matched: bool
    action: str  # "alert", "block", "quarantine", "notify", "log"
    risk_score: int
    matched_patterns: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = "medium"
    incident_title: str = ""
    incident_description: str = ""

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "matched": self.matched,
            "action": self.action,
            "risk_score": self.risk_score,
            "matched_patterns": self.matched_patterns,
            "severity": self.severity,
            "incident_title": self.incident_title,
            "incident_description": self.incident_description,
        }


# ==========================================
# Kural Değerlendirme Motoru
# ==========================================

class RuleEngine:
    """
    Politika Kural Değerlendirme Motoru.
    Tarama sonuçlarını aktif politikalarla karşılaştırır.
    """

    # Risk skoru -> Önem derecesi eşleştirmesi
    SEVERITY_THRESHOLDS = {
        "critical": 85,
        "high": 70,
        "medium": 40,
        "low": 0,
    }

    # Varsayılan aksiyon önceliği
    ACTION_PRIORITY = {
        "quarantine": 4,
        "block": 3,
        "notify": 2,
        "alert": 1,
        "log": 0,
    }

    def evaluate(
        self,
        scan_matches: List[PatternMatch],
        policies: List[Any],  # List[models.Policy]
        file_type: Optional[str] = None,
        cloud_source: Optional[str] = None,
    ) -> List[PolicyEvalResult]:
        """
        Tespit edilen örüntüleri politikalarla değerlendir.
        
        Args:
            scan_matches: Taramada bulunan PatternMatch listesi
            policies: Aktif politika listesi (SQLAlchemy Policy nesneleri)
            file_type: Taranan dosyanın uzantısı (örn: ".pdf")
            cloud_source: Bulut kaynak tipi (örn: "google_drive")
        
        Returns:
            PolicyEvalResult listesi
        """
        results = []

        if not scan_matches or not policies:
            return results

        # Tespit edilen örüntü anahtarlarını set'e al
        detected_pattern_keys = {m.pattern_key for m in scan_matches}

        for policy in policies:
            if not policy.is_active:
                continue

            result = self._evaluate_single_policy(
                policy=policy,
                scan_matches=scan_matches,
                detected_pattern_keys=detected_pattern_keys,
                file_type=file_type,
                cloud_source=cloud_source,
            )

            if result:
                results.append(result)

        # Risk skoruna göre sırala (yüksekten düşüğe)
        results.sort(key=lambda r: r.risk_score, reverse=True)
        return results

    def _evaluate_single_policy(
        self,
        policy: Any,
        scan_matches: List[PatternMatch],
        detected_pattern_keys: set,
        file_type: Optional[str],
        cloud_source: Optional[str],
    ) -> Optional[PolicyEvalResult]:
        """Tek bir politikayı değerlendir"""

        policy_data_types = set(policy.data_types or [])
        policy_file_types = set(policy.file_types or [])
        policy_cloud_sources = set(policy.cloud_sources or [])
        policy_actions = policy.actions or ["alert"]

        # Dosya tipi filtresi (politikada belirtildiyse kontrol et)
        if policy_file_types and file_type:
            if file_type.lower() not in policy_file_types:
                return None

        # Bulut kaynak filtresi
        if policy_cloud_sources and cloud_source:
            if cloud_source not in policy_cloud_sources:
                return None

        # Veri tipi eşleşmesi
        if policy_data_types:
            matched_keys = detected_pattern_keys & policy_data_types
        else:
            # Politikada veri tipi belirtilmemişse tüm eşleşmeleri al
            matched_keys = detected_pattern_keys

        if not matched_keys:
            return None

        # Eşleşen örüntüleri filtrele
        matched_matches = [m for m in scan_matches if m.pattern_key in matched_keys]

        if not matched_matches:
            return None

        # Risk skoru hesapla
        risk_score = calculate_risk_score(matched_matches)

        # En yüksek öncelikli aksiyonu belirle
        best_action = self._get_best_action(policy_actions)

        # Önem derecesi
        severity = self.get_incident_severity(risk_score)

        # Olay başlığı oluştur
        pattern_names = list(set(m.pattern_name for m in matched_matches))
        incident_title = (
            f"[{policy.name}] Hassas veri tespiti: {', '.join(pattern_names[:3])}"
            + (" ve diğerleri" if len(pattern_names) > 3 else "")
        )

        # Olay açıklaması
        incident_description = self._build_incident_description(
            policy=policy,
            matched_matches=matched_matches,
            risk_score=risk_score,
            file_type=file_type,
            cloud_source=cloud_source,
        )

        return PolicyEvalResult(
            policy_id=policy.id,
            policy_name=policy.name,
            matched=True,
            action=best_action,
            risk_score=risk_score,
            matched_patterns=[m.to_dict() for m in matched_matches],
            severity=severity,
            incident_title=incident_title,
            incident_description=incident_description,
        )

    def _get_best_action(self, actions: List[str]) -> str:
        """Aksiyon listesinden en yüksek öncelikli aksiyonu seç"""
        if not actions:
            return "alert"

        best = max(
            actions,
            key=lambda a: self.ACTION_PRIORITY.get(a, 0)
        )
        return best

    def _build_incident_description(
        self,
        policy: Any,
        matched_matches: List[PatternMatch],
        risk_score: int,
        file_type: Optional[str],
        cloud_source: Optional[str],
    ) -> str:
        """Olay açıklaması metni oluştur"""
        lines = [
            f"Politika '{policy.name}' ihlali tespit edildi.",
            f"Risk Skoru: {risk_score}/100",
            f"Tespit Edilen Veri Türleri:",
        ]

        # Her örüntü için özet
        pattern_summary: Dict[str, int] = {}
        for m in matched_matches:
            pattern_summary[m.pattern_name] = pattern_summary.get(m.pattern_name, 0) + 1

        for pattern_name, count in pattern_summary.items():
            lines.append(f"  - {pattern_name}: {count} eşleşme")

        if file_type:
            lines.append(f"Dosya Türü: {file_type}")
        if cloud_source:
            lines.append(f"Kaynak: {cloud_source}")

        return "\n".join(lines)

    def should_create_incident(self, eval_result: PolicyEvalResult) -> bool:
        """
        Değerlendirme sonucuna göre olay oluşturulmalı mı?
        
        Kurallar:
        - Risk skoru 30'dan düşükse olay oluşturma
        - Sadece "log" aksiyonunda olay oluşturma
        """
        if not eval_result.matched:
            return False

        if eval_result.risk_score < 30:
            return False

        if eval_result.action == "log":
            return False

        return True

    def get_incident_severity(self, risk_score: int) -> str:
        """
        Risk skoruna göre olay önem derecesi belirle.
        
        Returns:
            "critical", "high", "medium", veya "low"
        """
        if risk_score >= self.SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif risk_score >= self.SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif risk_score >= self.SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def get_recommended_actions(self, risk_score: int) -> List[str]:
        """Risk skoruna göre önerilen aksiyonları döndür"""
        if risk_score >= 85:
            return ["quarantine", "block", "notify", "alert"]
        elif risk_score >= 70:
            return ["block", "notify", "alert"]
        elif risk_score >= 40:
            return ["notify", "alert"]
        else:
            return ["alert", "log"]

    def merge_results(self, results: List[PolicyEvalResult]) -> PolicyEvalResult:
        """
        Birden fazla politika sonucunu birleştir (en yüksek risk kazanır).
        """
        if not results:
            return PolicyEvalResult(
                policy_id=0,
                policy_name="Genel",
                matched=False,
                action="log",
                risk_score=0,
            )

        # En yüksek riskli sonucu seç
        best = max(results, key=lambda r: r.risk_score)
        return best


# Singleton instance
rule_engine = RuleEngine()
