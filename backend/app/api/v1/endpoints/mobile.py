"""
移动端API接口 - 简化版数据格式
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas import PaginatedResponse

router = APIRouter()


@router.get("/quick-stats")
async def quick_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[int] = None
):
    """
    移动端快捷统计接口
    返回: 待办数、预警数、项目列表摘要
    """
    from app.models import ApprovalStep, Alert, ProjectMember, Project
    
    # 待办数量
    pending = db.query(ApprovalStep).filter(
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).count()
    
    # 未解决预警
    alert_query = db.query(Alert).filter(Alert.resolved == False)
    if project_id:
        alert_query = alert_query.filter(Alert.project_id == project_id)
    unresolved_alerts = alert_query.count()
    
    # 项目列表摘要
    user_projects = db.query(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    ).all()
    
    projects = []
    for pm in user_projects:
        project = db.query(Project).filter(Project.id == pm.project_id).first()
        if project:
            projects.append({
                "id": project.id,
                "code": project.project_code,
                "name": project.project_name,
                "status": project.status,
            })
    
    return {
        "pending_count": pending,
        "unresolved_alerts": unresolved_alerts,
        "projects": projects,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "real_name": current_user.real_name,
            "department": current_user.department_name,
            "role": current_user.role,
        },
    }


@router.get("/mobile/approvals")
async def mobile_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """移动端待办审批列表（精简版）"""
    from app.models import ApprovalInstance, ApprovalStep
    
    steps = db.query(ApprovalStep).filter(
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    instances = []
    for step in steps:
        instance = step.instance
        instances.append({
            "instance_id": instance.id,
            "node_type": instance.node_type,
            "version": instance.version,
            "status": instance.status,
            "created_at": instance.created_at.isoformat(),
            "current_step_order": step.step_order,
            "step_opinion": step.opinion,
        })
    
    total = db.query(ApprovalStep).filter(
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).count()
    
    return {
        "items": instances,
        "total": total,
        "page": page,
        "has_more": (page * page_size) < total,
    }


@router.post("/mobile/approval/{instance_id}/action")
async def mobile_approval_action(
    instance_id: int,
    action: str,  # approve / reject
    opinion: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """移动端审批操作"""
    from app.services.workflow.engine import ApprovalEngine
    
    engine = ApprovalEngine(db)
    
    step = db.query(ApprovalStep).filter(
        ApprovalStep.instance_id == instance_id,
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).first()
    
    if not step:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="没有待审批的步骤")
    
    instance = engine.submit_approval(
        step_id=step.id,
        user_id=current_user.id,
        decision=action,
        opinion=opinion,
    )
    
    return {
        "success": True,
        "instance_id": instance.id,
        "status": instance.status,
    }
