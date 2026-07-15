"""
DLP Sistemi - Tarama İşleri Yönlendiricisi
Yerel dosya ve bulut taramaları için endpoint'ler
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, BackgroundTasks, Request
)
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
import models
import schemas
from auth import get_current_active_user, require_role, create_audit_log
from engines.scan_engine import ScanEngine
from engines.detection_patterns import get_all_pattern_info, PATTERNS
from engines.rule_engine import RuleEngine

router = APIRouter(prefix="/scans", tags=["Taramalar"])

scan_engine = ScanEngine()
rule_engine = RuleEngine()


# ==========================================
# Örüntü Bilgisi
# ==========================================

@router.get("/patterns")
async def list_patterns(
    current_user: models.User = Depends(get_current_active_user)
):
    """Kullanılabilir tüm tespit örüntülerini listele"""
    return {
        "patterns": get_all_pattern_info(),
        "total": len(PATTERNS),
        "categories": list(set(p.category for p in PATTERNS.values()))
    }


# ==========================================
# Tarama İşleri Listeleme
# ==========================================

@router.get("", response_model=schemas.ScanJobListResponse)
async def list_scan_jobs(
    page: int = 1,
    page_size: int = 20,
    scan_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Tarama işlerini listele"""
    query = db.query(models.ScanJob)

    if scan_type:
        query = query.filter(models.ScanJob.scan_type == scan_type)

    if status:
        query = query.filter(models.ScanJob.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    jobs = query.order_by(models.ScanJob.id.desc()).offset(offset).limit(page_size).all()

    job_responses = []
    for job in jobs:
        progress = 0.0
        if job.total_files > 0:
            progress = round((job.scanned_files / job.total_files) * 100, 1)

        job_responses.append(schemas.ScanJobResponse(
            id=job.id,
            name=job.name,
            scan_type=job.scan_type,
            target_path=job.target_path,
            status=job.status,
            total_files=job.total_files,
            scanned_files=job.scanned_files,
            incidents_found=job.incidents_found,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_by=job.created_by,
            error_message=job.error_message,
            policy_ids=job.policy_ids or [],
            pattern_keys=job.pattern_keys or [],
            progress_percent=progress,
        ))

    return schemas.ScanJobListResponse(
        items=job_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{scan_id}", response_model=schemas.ScanJobResponse)
async def get_scan_job(
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Belirli bir tarama işinin detayını döndür"""
    job = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"#{scan_id} ID'li tarama bulunamadı"
        )

    progress = 0.0
    if job.total_files > 0:
        progress = round((job.scanned_files / job.total_files) * 100, 1)

    return schemas.ScanJobResponse(
        id=job.id,
        name=job.name,
        scan_type=job.scan_type,
        target_path=job.target_path,
        status=job.status,
        total_files=job.total_files,
        scanned_files=job.scanned_files,
        incidents_found=job.incidents_found,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_by=job.created_by,
        error_message=job.error_message,
        policy_ids=job.policy_ids or [],
        pattern_keys=job.pattern_keys or [],
        progress_percent=progress,
    )


@router.delete("/{scan_id}")
async def delete_scan_job(
    scan_id: int,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Tarama işini sil"""
    job = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"#{scan_id} ID'li tarama bulunamadı"
        )

    if job.status == models.ScanStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Çalışan bir tarama silinemez. Önce iptal edin."
        )

    db.delete(job)
    db.commit()
    return {"message": f"Tarama #{scan_id} silindi"}


# ==========================================
# Yerel Dosya Tarama
# ==========================================

@router.post("/local", response_model=schemas.ScanJobResponse, status_code=201)
async def start_local_scan(
    scan_request: schemas.ScanRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Yerel dosya sistemi taraması başlat"""
    if not scan_request.target_path:
        raise HTTPException(
            status_code=400,
            detail="Yerel tarama için hedef yol gereklidir"
        )

    target = Path(scan_request.target_path)
    if not target.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Hedef yol bulunamadı: {scan_request.target_path}"
        )

    # Tarama işi oluştur
    job = models.ScanJob(
        name=scan_request.name,
        scan_type=models.ScanType.LOCAL,
        target_path=scan_request.target_path,
        status=models.ScanStatus.PENDING,
        policy_ids=scan_request.policy_ids,
        pattern_keys=scan_request.pattern_keys,
        created_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="scan.started",
        resource_type="scan_job",
        resource_id=job.id,
        details={"target": scan_request.target_path, "type": "local"},
        ip_address=request.client.host if request.client else None,
    )

    # Arka planda çalıştır
    background_tasks.add_task(
        _run_local_scan,
        job_id=job.id,
        target_path=scan_request.target_path,
        pattern_keys=scan_request.pattern_keys,
        policy_ids=scan_request.policy_ids,
        recursive=scan_request.recursive,
        created_by=current_user.id,
    )

    return schemas.ScanJobResponse(
        id=job.id,
        name=job.name,
        scan_type=job.scan_type,
        target_path=job.target_path,
        status=job.status,
        total_files=0,
        scanned_files=0,
        incidents_found=0,
        created_by=job.created_by,
        policy_ids=job.policy_ids or [],
        pattern_keys=job.pattern_keys or [],
        progress_percent=0.0,
    )


# ==========================================
# Dosya Yükleme ve Tarama
# ==========================================

@router.post("/upload", response_model=dict)
async def scan_uploaded_file(
    file: UploadFile = File(...),
    pattern_keys: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yüklenen dosyayı anında tara ve sonuçları döndür.
    Tarama işi oluşturmadan direkt sonuç döndürür.
    """
    # Dosya boyutu kontrolü
    content = await file.read()
    max_size = 50 * 1024 * 1024  # 50MB

    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Dosya çok büyük. Maksimum boyut: 50 MB"
        )

    # Örüntü anahtarları
    keys = None
    if pattern_keys:
        keys = [k.strip() for k in pattern_keys.split(",") if k.strip()]

    # Dosyayı tara
    result = scan_engine.scan_file_from_bytes(content, file.filename, keys)

    # Veritabanına tarama kaydı oluştur
    scan_job = models.ScanJob(
        name=f"Dosya Yükleme: {file.filename}",
        scan_type=models.ScanType.UPLOAD,
        status=models.ScanStatus.COMPLETED,
        total_files=1,
        scanned_files=1,
        incidents_found=1 if result["status"] == "threat" else 0,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        created_by=current_user.id,
        pattern_keys=keys or [],
    )
    db.add(scan_job)
    db.commit()
    db.refresh(scan_job)

    # Tarama sonucu kaydet
    scan_result = models.ScanResult(
        scan_job_id=scan_job.id,
        file_name=file.filename,
        file_size=len(content),
        file_type=result["file_type"],
        status=result["status"],
        detected_patterns=result["detected_patterns"],
        risk_score=result["risk_score"],
    )
    db.add(scan_result)
    db.commit()

    return {
        "scan_job_id": scan_job.id,
        "file_name": file.filename,
        "file_size": len(content),
        "file_type": result["file_type"],
        "status": result["status"],
        "classification": result["classification"],
        "risk_score": result["risk_score"],
        "detected_patterns": result["detected_patterns"],
        "pattern_count": len(result["detected_patterns"]),
        "scanned_at": result["scanned_at"],
    }


# ==========================================
# Tarama Sonuçları
# ==========================================

@router.get("/{scan_id}/results", response_model=schemas.ScanResultListResponse)
async def get_scan_results(
    scan_id: int,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bir taramanın dosya sonuçlarını listele"""
    job = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"#{scan_id} ID'li tarama bulunamadı"
        )

    query = db.query(models.ScanResult).filter(
        models.ScanResult.scan_job_id == scan_id
    )

    if status:
        query = query.filter(models.ScanResult.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    results = query.order_by(
        models.ScanResult.risk_score.desc()
    ).offset(offset).limit(page_size).all()

    return schemas.ScanResultListResponse(
        items=[schemas.ScanResultResponse(
            id=r.id,
            scan_job_id=r.scan_job_id,
            file_path=r.file_path,
            file_name=r.file_name,
            file_size=r.file_size,
            file_type=r.file_type,
            status=r.status,
            detected_patterns=r.detected_patterns or [],
            risk_score=r.risk_score,
            incident_id=r.incident_id,
            scanned_at=r.scanned_at,
            error_message=r.error_message,
        ) for r in results],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: int,
    current_user: models.User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Çalışan taramayı iptal et"""
    job = db.query(models.ScanJob).filter(models.ScanJob.id == scan_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"#{scan_id} ID'li tarama bulunamadı"
        )

    if job.status not in (models.ScanStatus.RUNNING, models.ScanStatus.PENDING):
        raise HTTPException(
            status_code=400,
            detail=f"Bu tarama iptal edilemez. Mevcut durum: {job.status}"
        )

    job.status = models.ScanStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    db.commit()

    return {"message": f"Tarama #{scan_id} iptal edildi"}


# ==========================================
# Arka Plan Tarama Fonksiyonları
# ==========================================

def _run_local_scan(
    job_id: int,
    target_path: str,
    pattern_keys: List[str],
    policy_ids: List[int],
    recursive: bool,
    created_by: int,
):
    """Yerel dizin taramasını arka planda çalıştır"""
    db = SessionLocal()

    try:
        job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
        if not job:
            return

        # İşi başlat
        job.status = models.ScanStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Dosya sayısını belirle
        engine = ScanEngine()
        total_files = engine.count_files(target_path, recursive=recursive)
        job.total_files = total_files
        db.commit()

        if total_files == 0:
            job.status = models.ScanStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        # Aktif politikaları yükle
        policies = []
        if policy_ids:
            policies = db.query(models.Policy).filter(
                models.Policy.id.in_(policy_ids),
                models.Policy.is_active == True
            ).all()
        else:
            policies = db.query(models.Policy).filter(
                models.Policy.is_active == True
            ).all()

        # Kullanılacak örüntü anahtarları
        all_pattern_keys = set(pattern_keys or [])
        for policy in policies:
            for dt in (policy.data_types or []):
                all_pattern_keys.add(dt)

        pattern_list = list(all_pattern_keys) if all_pattern_keys else None
        re_engine = RuleEngine()
        incidents_found = 0
        scanned_count = 0

        # Dosyaları tara
        for result in engine.scan_directory(target_path, pattern_list, recursive=recursive):
            scanned_count += 1
            job.scanned_files = scanned_count

            # Her 10 dosyada bir commit
            if scanned_count % 10 == 0:
                db.commit()

            # Tarama sonucu kaydet
            scan_result = models.ScanResult(
                scan_job_id=job_id,
                file_path=result.get("file_path"),
                file_name=result.get("file_name", ""),
                file_size=result.get("file_size"),
                file_type=result.get("file_type"),
                status=result.get("status", "clean"),
                detected_patterns=result.get("detected_patterns", []),
                risk_score=result.get("risk_score", 0),
                error_message=result.get("error_message"),
            )
            db.add(scan_result)

            # Tehdit tespit edildi mi?
            if result.get("status") == "threat" and result.get("detected_patterns"):
                # Politika değerlendirmesi
                from engines.detection_patterns import PatternMatch
                match_dicts = result.get("detected_patterns", [])

                # dict'leri PatternMatch'e dönüştür
                pattern_matches = []
                for m in match_dicts:
                    pattern_matches.append(PatternMatch(
                        pattern_key=m.get("pattern_key", ""),
                        pattern_name=m.get("pattern_name", ""),
                        matched_text=m.get("matched_text", ""),
                        risk_score=m.get("risk_score", 0),
                        category=m.get("category", ""),
                    ))

                if pattern_matches:
                    eval_results = re_engine.evaluate(
                        scan_matches=pattern_matches,
                        policies=policies,
                        file_type=result.get("file_type"),
                    )

                    for eval_result in eval_results:
                        if re_engine.should_create_incident(eval_result):
                            incident = models.Incident(
                                title=eval_result.incident_title or f"Hassas veri tespit edildi: {result.get('file_name', '')}",
                                description=eval_result.incident_description,
                                severity=eval_result.severity,
                                status=models.IncidentStatus.OPEN,
                                policy_id=eval_result.policy_id,
                                file_path=result.get("file_path"),
                                file_name=result.get("file_name"),
                                file_type=result.get("file_type"),
                                file_size=result.get("file_size"),
                                detected_patterns=result.get("detected_patterns", []),
                                risk_score=eval_result.risk_score,
                            )
                            db.add(incident)
                            db.flush()
                            scan_result.incident_id = incident.id
                            incidents_found += 1
                            break

        # Taramayı tamamla
        db.commit()
        job.status = models.ScanStatus.COMPLETED
        job.scanned_files = scanned_count
        job.incidents_found = incidents_found
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        try:
            job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
            if job:
                job.status = models.ScanStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
