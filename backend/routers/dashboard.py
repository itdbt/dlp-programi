"""
DLP Sistemi - Dashboard İstatistikleri Yönlendiricisi
Özet istatistikler, trend verileri ve sistem sağlık durumu
"""

import os
import platform
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import get_db
import models
import schemas
from auth import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kapsamlı dashboard istatistikleri döndür.
    Son 30 günlük trend verileri dahildir.
    """
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    # ---- Olay İstatistikleri ----
    total_incidents = db.query(func.count(models.Incident.id)).scalar() or 0

    open_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.status == models.IncidentStatus.OPEN
    ).scalar() or 0

    # Önem derecesine göre
    critical_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.severity == models.IncidentSeverity.CRITICAL
    ).scalar() or 0

    high_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.severity == models.IncidentSeverity.HIGH
    ).scalar() or 0

    medium_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.severity == models.IncidentSeverity.MEDIUM
    ).scalar() or 0

    low_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.severity == models.IncidentSeverity.LOW
    ).scalar() or 0

    # ---- Politika İstatistikleri ----
    total_policies = db.query(func.count(models.Policy.id)).scalar() or 0
    active_policies = db.query(func.count(models.Policy.id)).filter(
        models.Policy.is_active == True
    ).scalar() or 0

    # ---- Tarama İstatistikleri ----
    total_scans = db.query(func.count(models.ScanJob.id)).scalar() or 0
    running_scans = db.query(func.count(models.ScanJob.id)).filter(
        models.ScanJob.status == models.ScanStatus.RUNNING
    ).scalar() or 0

    # ---- Son Olaylar ----
    recent_incidents_query = db.query(models.Incident).order_by(
        models.Incident.created_at.desc()
    ).limit(10).all()

    # ---- Durum Dağılımı ----
    status_counts = db.query(
        models.Incident.status,
        func.count(models.Incident.id).label("count")
    ).group_by(models.Incident.status).all()

    incidents_by_status = {str(row.status): row.count for row in status_counts}

    incidents_by_severity = {
        "critical": critical_incidents,
        "high": high_incidents,
        "medium": medium_incidents,
        "low": low_incidents,
    }

    # ---- Trend Verisi (Son 30 gün, günlük) ----
    incidents_trend = []
    for i in range(29, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_count = db.query(func.count(models.Incident.id)).filter(
            and_(
                models.Incident.created_at >= day_start,
                models.Incident.created_at < day_end
            )
        ).scalar() or 0

        incidents_trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": day_count,
        })

    # ---- En Sık Tespit Edilen Örüntüler ----
    # ScanResult'lardan örüntü istatistikleri
    pattern_counts: Dict[str, int] = {}
    recent_results = db.query(models.ScanResult).filter(
        models.ScanResult.status == "threat",
        models.ScanResult.scanned_at >= thirty_days_ago
    ).all()

    for result in recent_results:
        patterns = result.detected_patterns or []
        for p in patterns:
            key = p.get("pattern_name", "Bilinmiyor")
            pattern_counts[key] = pattern_counts.get(key, 0) + 1

    top_patterns = [
        {"name": name, "count": count}
        for name, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:10]
    ]

    # ---- Tarama İstatistikleri ----
    completed_scans = db.query(func.count(models.ScanJob.id)).filter(
        models.ScanJob.status == models.ScanStatus.COMPLETED
    ).scalar() or 0

    failed_scans = db.query(func.count(models.ScanJob.id)).filter(
        models.ScanJob.status == models.ScanStatus.FAILED
    ).scalar() or 0

    total_files_scanned = db.query(func.sum(models.ScanJob.scanned_files)).scalar() or 0
    total_incidents_from_scans = db.query(func.sum(models.ScanJob.incidents_found)).scalar() or 0

    scan_stats = {
        "total": total_scans,
        "completed": completed_scans,
        "running": running_scans,
        "failed": failed_scans,
        "total_files_scanned": int(total_files_scanned),
        "total_incidents_found": int(total_incidents_from_scans or 0),
    }

    # Response için incident objeleri hazırla
    recent_incidents_data = []
    for inc in recent_incidents_query:
        inc_dict = {
            "id": inc.id,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity,
            "status": inc.status,
            "policy_id": inc.policy_id,
            "file_path": inc.file_path,
            "file_name": inc.file_name,
            "file_type": inc.file_type,
            "file_size": inc.file_size,
            "cloud_source": inc.cloud_source,
            "source_url": inc.source_url,
            "detected_patterns": inc.detected_patterns or [],
            "risk_score": inc.risk_score,
            "assignee_id": inc.assignee_id,
            "created_at": inc.created_at,
            "updated_at": inc.updated_at,
            "resolved_at": inc.resolved_at,
        }
        recent_incidents_data.append(schemas.IncidentResponse(**inc_dict))

    return schemas.DashboardStats(
        total_incidents=total_incidents,
        open_incidents=open_incidents,
        critical_incidents=critical_incidents,
        high_incidents=high_incidents,
        medium_incidents=medium_incidents,
        low_incidents=low_incidents,
        total_policies=total_policies,
        active_policies=active_policies,
        total_scans=total_scans,
        running_scans=running_scans,
        recent_incidents=recent_incidents_data,
        incidents_by_severity=incidents_by_severity,
        incidents_by_status=incidents_by_status,
        incidents_trend=incidents_trend,
        top_patterns=top_patterns,
        scan_stats=scan_stats,
    )


@router.get("/health", response_model=schemas.SystemHealth)
async def get_system_health(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sistem sağlık durumu kontrolü"""

    # Veritabanı bağlantısını test et
    db_status = "healthy"
    try:
        db.execute(models.User.__table__.select().limit(1))
    except Exception:
        db_status = "unhealthy"

    # Disk kullanımı
    disk_usage = None
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        disk_usage = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent": round((used / total) * 100, 1),
        }
    except Exception:
        pass

    # Bellek kullanımı
    memory_usage = None
    try:
        import psutil
        mem = psutil.virtual_memory()
        memory_usage = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
        }
    except ImportError:
        pass

    # Genel durum
    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return schemas.SystemHealth(
        status=overall_status,
        database=db_status,
        scheduler="active",
        disk_usage=disk_usage,
        memory_usage=memory_usage,
        version="1.0.0",
        uptime=_get_uptime(),
    )


def _get_uptime() -> str:
    """Sistem çalışma süresini döndür"""
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        hours = int(uptime.total_seconds() / 3600)
        minutes = int((uptime.total_seconds() % 3600) / 60)
        return f"{hours} saat {minutes} dakika"
    except ImportError:
        return "Bilinmiyor"


@router.get("/summary")
async def get_quick_summary(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Hızlı özet - minimal veri ile performanslı endpoint"""
    total_incidents = db.query(func.count(models.Incident.id)).scalar() or 0
    open_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.status == models.IncidentStatus.OPEN
    ).scalar() or 0
    critical = db.query(func.count(models.Incident.id)).filter(
        models.Incident.severity == models.IncidentSeverity.CRITICAL,
        models.Incident.status == models.IncidentStatus.OPEN
    ).scalar() or 0
    active_scans = db.query(func.count(models.ScanJob.id)).filter(
        models.ScanJob.status == models.ScanStatus.RUNNING
    ).scalar() or 0

    return {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "critical_open": critical,
        "active_scans": active_scans,
        "timestamp": datetime.utcnow().isoformat(),
    }
