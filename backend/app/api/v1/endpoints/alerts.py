"""
预警中心 API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import Alert, AlertRule, Project
from app.schemas import PaginatedResponse

router = APIRouter()


@router.get("/list", response_model=dict)
async def list_alerts(
    project_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询预警列表"""
    query = db.query(Alert)
    
    if project_id:
        query = query.filter(Alert.project_id == project_id)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for a in alerts:
        result.append({
            "id": a.id,
            "node_type": a.node_type,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "resolved": a.resolved,
            "related_id": a.related_id,
            "created_at": a.created_at.isoformat(),
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        })
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "has_more": (page * page_size) < total,
    }


@router.get("/stats")
async def get_alert_stats(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取预警统计"""
    query = db.query(Alert)
    if project_id:
        query = query.filter(Alert.project_id == project_id)
    
    total = query.count()
    unresolved = query.filter(Alert.resolved == False).count()
    critical = query.filter(Alert.severity == "critical").count()
    warning = query.filter(Alert.severity == "warning").count()
    
    # By type
    by_type = {}
    for a in query.all():
        by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
    
    return {
        "total": total,
        "unresolved": unresolved,
        "critical": critical,
        "warning": warning,
        "by_type": by_type,
    }


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记预警为已解决"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")
    
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    db.commit()
    
    return {"message": "预警已标记为已解决"}


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记所有预警为已读"""
    from app.models import UserAlertRead
    
    reads = [
        UserAlertRead(user_id=current_user.id, alert_id=a.id)
        for a in db.query(Alert).filter(Alert.resolved == False).all()
    ]
    if reads:
        db.add_all(reads)
        db.commit()
    
    return {"message": "所有预警已标记为已读"}


@router.post("/create-manual", status_code=201)
async def create_manual_alert(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动创建预警"""
    alert = Alert(
        project_id=req.get("project_id"),
        node_type=req.get("node_type", ""),
        alert_type=req.get("alert_type", "manual"),
        severity=req.get("severity", "warning"),
        message=req.get("message", ""),
        related_id=req.get("related_id"),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return {
        "id": alert.id,
        "message": "预警已创建",
    }
