"""
DLP Sistemi - Raporlama Yönlendiricisi
Kapsamlı DLP sistem raporları ve veri dışa aktarma
"""

import csv
import io
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import get_db
import models
from auth import get_current_active_user

router = APIRouter(prefix="/reports", tags=["Raporlar"])


@router.get("/summary")
async def get_summary_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kapsamlı özet raporu döndür.
    Olaylar, taramalar ve politika istatistiklerini içerir.
    """
    # Varsayılan tarih aralığı: son 30 gün
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Olay istatistikleri
    incident_query = db.query(models.Incident).filter(
        and_(
            models.Incident.created_at >= start_date,
            models.Incident.created_at <= end_date
        )
    )

    total_incidents = incident_query.count()

    # Önem derecesine göre dağılım
    severity_dist = {}
    for sev in ["critical", "high", "medium", "low"]:
        count = incident_query.filter(models.Incident.severity == sev).count()
        severity_dist[sev] = count

    # Duruma göre dağılım
    status_dist = {}
    for st in ["open", "investigating", "resolved", "false_positive", "closed"]:
        count = incident_query.filter(models.Incident.status == st).count()
        status_dist[st] = count

    # Ortalama çözüm süresi (saat)
    resolved_incidents = db.query(models.Incident).filter(
        and_(
            models.Incident.created_at >= start_date,
            models.Incident.created_at <= end_date,
            models.Incident.resolved_at != None
        )
    ).all()

    avg_resolution_hours = 0.0
    if resolved_incidents:
        total_hours = sum(
            (inc.resolved_at - inc.created_at).total_seconds() / 3600
            for inc in resolved_incidents
            if inc.resolved_at and inc.created_at
        )
        avg_resolution_hours = round(total_hours / len(resolved_incidents), 1)

    # Kaynak dağılımı (cloud_source)
    source_dist = db.query(
        models.Incident.cloud_source,
        func.count(models.Incident.id).label("count")
    ).filter(
        and_(
            models.Incident.created_at >= start_date,
            models.Incident.created_at <= end_date
        )
    ).group_by(models.Incident.cloud_source).all()

    source_breakdown = {}
    for row in source_dist:
        source_key = row.cloud_source or "yerel"
        source_breakdown[source_key] = row.count

    # Tarama istatistikleri
    scan_query = db.query(models.ScanJob).filter(
        and_(
            models.ScanJob.started_at >= start_date,
            models.ScanJob.started_at <= end_date
        )
    )

    total_scans = scan_query.count()
    completed_scans = scan_query.filter(
        models.ScanJob.status == models.ScanStatus.COMPLETED
    ).count()
    total_files_scanned = db.query(func.sum(models.ScanJob.scanned_files)).filter(
        and_(
            models.ScanJob.started_at >= start_date,
            models.ScanJob.started_at <= end_date
        )
    ).scalar() or 0

    # Politika ihlal sayıları
    policy_violations = db.query(
        models.Policy.name,
        func.count(models.Incident.id).label("count")
    ).join(
        models.Incident, models.Incident.policy_id == models.Policy.id
    ).filter(
        and_(
            models.Incident.created_at >= start_date,
            models.Incident.created_at <= end_date
        )
    ).group_by(models.Policy.name).order_by(
        func.count(models.Incident.id).desc()
    ).limit(10).all()

    # Günlük trend
    daily_trend = []
    days = (end_date - start_date).days + 1
    for i in range(min(days, 30)):
        day_start = (end_date - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        day_count = db.query(func.count(models.Incident.id)).filter(
            and_(
                models.Incident.created_at >= day_start,
                models.Incident.created_at < day_end
            )
        ).scalar() or 0

        daily_trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "incidents": day_count,
        })

    daily_trend.reverse()

    return {
        "report_type": "özet",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": (end_date - start_date).days + 1,
        },
        "incidents": {
            "total": total_incidents,
            "by_severity": severity_dist,
            "by_status": status_dist,
            "by_source": source_breakdown,
            "avg_resolution_hours": avg_resolution_hours,
            "resolved": len(resolved_incidents),
        },
        "scans": {
            "total": total_scans,
            "completed": completed_scans,
            "total_files_scanned": int(total_files_scanned),
        },
        "top_violated_policies": [
            {"policy_name": row.name, "violation_count": row.count}
            for row in policy_violations
        ],
        "daily_trend": daily_trend,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/incidents")
async def get_incidents_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    format: str = "json",
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Detaylı olay raporu.
    JSON veya CSV formatında dışa aktarılabilir.
    """
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    query = db.query(models.Incident).filter(
        and_(
            models.Incident.created_at >= start_date,
            models.Incident.created_at <= end_date
        )
    )

    if severity:
        query = query.filter(models.Incident.severity == severity)

    if status:
        query = query.filter(models.Incident.status == status)

    incidents = query.order_by(models.Incident.created_at.desc()).all()

    incident_data = []
    for inc in incidents:
        incident_data.append({
            "id": inc.id,
            "başlık": inc.title,
            "önem_derecesi": inc.severity,
            "durum": inc.status,
            "risk_skoru": inc.risk_score,
            "dosya_adı": inc.file_name or "",
            "dosya_türü": inc.file_type or "",
            "kaynak": inc.cloud_source or "yerel",
            "politika_id": inc.policy_id,
            "oluşturma_tarihi": inc.created_at.strftime("%d.%m.%Y %H:%M") if inc.created_at else "",
            "çözüm_tarihi": inc.resolved_at.strftime("%d.%m.%Y %H:%M") if inc.resolved_at else "",
            "tespit_sayısı": len(inc.detected_patterns or []),
        })

    if format.lower() == "csv":
        output = io.StringIO()
        if incident_data:
            writer = csv.DictWriter(output, fieldnames=incident_data[0].keys())
            writer.writeheader()
            writer.writerows(incident_data)

        return Response(
            content=output.getvalue().encode("utf-8-sig"),  # BOM for Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=dlp_olaylar_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

    return {
        "report_type": "olaylar",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "total": len(incident_data),
        "data": incident_data,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/scans")
async def get_scans_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "json",
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detaylı tarama raporu"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    scans = db.query(models.ScanJob).filter(
        and_(
            models.ScanJob.id > 0,  # tümü
        )
    ).order_by(models.ScanJob.id.desc()).all()

    scan_data = []
    for scan in scans:
        duration = None
        if scan.started_at and scan.completed_at:
            delta = scan.completed_at - scan.started_at
            duration = round(delta.total_seconds() / 60, 1)  # dakika

        scan_data.append({
            "id": scan.id,
            "ad": scan.name,
            "tür": scan.scan_type,
            "hedef": scan.target_path or "",
            "durum": scan.status,
            "toplam_dosya": scan.total_files,
            "taranan_dosya": scan.scanned_files,
            "bulunan_ihlal": scan.incidents_found,
            "başlangıç": scan.started_at.strftime("%d.%m.%Y %H:%M") if scan.started_at else "",
            "bitiş": scan.completed_at.strftime("%d.%m.%Y %H:%M") if scan.completed_at else "",
            "süre_dk": duration,
        })

    if format.lower() == "csv":
        output = io.StringIO()
        if scan_data:
            writer = csv.DictWriter(output, fieldnames=scan_data[0].keys())
            writer.writeheader()
            writer.writerows(scan_data)

        return Response(
            content=output.getvalue().encode("utf-8-sig"),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=dlp_taramalar_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

    return {
        "report_type": "taramalar",
        "total": len(scan_data),
        "data": scan_data,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/policies")
async def get_policies_report(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Politika etkinlik raporu"""
    policies = db.query(models.Policy).all()

    policy_data = []
    for policy in policies:
        incident_count = db.query(func.count(models.Incident.id)).filter(
            models.Incident.policy_id == policy.id
        ).scalar() or 0

        open_incidents = db.query(func.count(models.Incident.id)).filter(
            models.Incident.policy_id == policy.id,
            models.Incident.status == models.IncidentStatus.OPEN
        ).scalar() or 0

        critical_incidents = db.query(func.count(models.Incident.id)).filter(
            models.Incident.policy_id == policy.id,
            models.Incident.severity == models.IncidentSeverity.CRITICAL
        ).scalar() or 0

        policy_data.append({
            "id": policy.id,
            "ad": policy.name,
            "aktif": policy.is_active,
            "önem": policy.severity,
            "veri_türleri": policy.data_types or [],
            "toplam_ihlal": incident_count,
            "açık_ihlal": open_incidents,
            "kritik_ihlal": critical_incidents,
            "oluşturma_tarihi": policy.created_at.strftime("%d.%m.%Y") if policy.created_at else "",
        })

    return {
        "report_type": "politikalar",
        "total": len(policy_data),
        "data": policy_data,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/patterns")
async def get_patterns_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Veri tipi tespit frekans raporu"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # ScanResult'lardan örüntü istatistikleri
    results = db.query(models.ScanResult).filter(
        models.ScanResult.status == "threat",
        models.ScanResult.scanned_at >= start_date,
        models.ScanResult.scanned_at <= end_date,
    ).all()

    pattern_stats: Dict[str, Dict] = {}
    for result in results:
        for p in (result.detected_patterns or []):
            key = p.get("pattern_key", "unknown")
            if key not in pattern_stats:
                pattern_stats[key] = {
                    "pattern_key": key,
                    "pattern_name": p.get("pattern_name", key),
                    "category": p.get("category", ""),
                    "count": 0,
                    "avg_risk_score": 0,
                    "total_risk": 0,
                }
            pattern_stats[key]["count"] += 1
            pattern_stats[key]["total_risk"] += p.get("risk_score", 0)

    for key in pattern_stats:
        count = pattern_stats[key]["count"]
        total = pattern_stats[key]["total_risk"]
        pattern_stats[key]["avg_risk_score"] = round(total / count, 1) if count > 0 else 0
        del pattern_stats[key]["total_risk"]

    sorted_patterns = sorted(
        pattern_stats.values(),
        key=lambda x: x["count"],
        reverse=True
    )

    return {
        "report_type": "örüntüler",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "total_unique_patterns": len(sorted_patterns),
        "data": sorted_patterns,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/export/all")
async def export_all_data(
    format: str = "json",
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Tüm verileri dışa aktar (yönetici için tam yedek rapor).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Bu rapor sadece yöneticiler için erişilebilir"
        )

    incidents = db.query(models.Incident).all()
    policies = db.query(models.Policy).all()
    scans = db.query(models.ScanJob).all()

    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "system": "DLP Güvenlik Sistemi v1.0",
        "totals": {
            "incidents": len(incidents),
            "policies": len(policies),
            "scans": len(scans),
        },
        "incidents": [
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "risk_score": i.risk_score,
                "file_name": i.file_name,
                "cloud_source": i.cloud_source,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in incidents
        ],
        "policies": [
            {
                "id": p.id,
                "name": p.name,
                "is_active": p.is_active,
                "severity": p.severity,
                "data_types": p.data_types,
            }
            for p in policies
        ],
    }

    if format.lower() == "json":
        content = json.dumps(export_data, ensure_ascii=False, indent=2)
        return Response(
            content=content.encode("utf-8"),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=dlp_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )

    return export_data
