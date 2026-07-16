"""
总经理驾驶舱 API - 全数据源汇总
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import (
    Project, BusinessForm, ApprovalInstance, ApprovalStep,
    Alert, ConstructionContract, ProjectDocument
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    总经理驾驶舱 — 全数据源汇总
    返回: KPI + 趋势 + 预警 + 审批统计
    """
    # 项目列表
    projects_query = db.query(Project)
    if project_id:
        projects_query = projects_query.filter(Project.id == project_id)
    projects = projects_query.all()
    
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status == "active")
    
    # 本月审批统计
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    all_instances = []
    for p in projects:
        instances = db.query(ApprovalInstance).filter(
            ApprovalInstance.project_id == p.id,
            ApprovalInstance.created_at >= month_start,
        ).all()
        all_instances.extend(instances)
    
    total_approvals = len(all_instances)
    completed_approvals = sum(1 for i in all_instances if i.status == "completed")
    pending_approvals = sum(1 for i in all_instances if i.status == "active")
    rejected_approvals = sum(1 for i in all_instances if i.status == "rejected")
    
    # 按节点类型统计
    approvals_by_node = {}
    for inst in all_instances:
        node = inst.node_type
        approvals_by_node[node] = approvals_by_node.get(node, 0) + 1
    
    # 本月业务表单创建统计
    all_forms = []
    for p in projects:
        forms = db.query(BusinessForm).filter(
            BusinessForm.project_id == p.id,
            BusinessForm.created_at >= month_start,
        ).all()
        all_forms.extend(forms)
    
    forms_by_node = {}
    for f in all_forms:
        node = f.node_type
        forms_by_node[node] = forms_by_node.get(node, 0) + 1
    
    # 预警统计
    all_alerts = []
    for p in projects:
        alerts = db.query(Alert).filter(
            Alert.project_id == p.id,
            Alert.resolved == False,
        ).all()
        all_alerts.extend(alerts)
    
    critical_alerts = sum(1 for a in all_alerts if a.severity == "critical")
    warning_alerts = sum(1 for a in all_alerts if a.severity == "warning")
    
    # 建造合同数据
    contracts = []
    for p in projects:
        contract = db.query(ConstructionContract).filter(
            ConstructionContract.project_id == p.id,
        ).order_by(ConstructionContract.month.desc()).first()
        if contract:
            contracts.append({
                "project_id": p.id,
                "project_name": p.project_name,
                "month": contract.month,
                "original_contract_amount": float(contract.original_contract_amount or 0),
                "total_revenue": float(contract.total_revenue or 0),
                "total_cost": float(contract.total_cost or 0),
                "profit_ratio": float(contract.profit_ratio or 0),
                "over_budget": bool(contract.over_budget or False),
            })
    
    # 资料库统计
    docs_count = 0
    for p in projects:
        count = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == p.id,
        ).count()
        docs_count += count
    
    # 超时审批统计
    overdue_steps = db.query(ApprovalStep).filter(
        ApprovalStep.step_status == "pending",
        ApprovalStep.timeout_at < datetime.utcnow(),
    ).count()
    
    return {
        "summary": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_approvals_month": total_approvals,
            "completed_approvals": completed_approvals,
            "pending_approvals": pending_approvals,
            "rejected_approvals": rejected_approvals,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "overdue_steps": overdue_steps,
            "documents_count": docs_count,
        },
        "approvals_by_node": approvals_by_node,
        "forms_by_node": forms_by_node,
        "contracts": contracts,
        "alerts_summary": {
            "unresolved": len(all_alerts),
            "by_severity": {
                "critical": critical_alerts,
                "warning": warning_alerts,
            },
        },
        "recent_alerts": [
            {
                "id": a.id,
                "node_type": a.node_type,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "created_at": a.created_at.isoformat(),
            } for a in sorted(all_alerts, key=lambda x: x.created_at, reverse=True)[:10]
        ],
    }


@router.get("/monthly-trend")
async def get_monthly_trend(
    project_id: Optional[int] = None,
    months: int = 6,
    db: Session = Depends(get_db)
):
    """获取月度趋势数据"""
    from dateutil.relativedelta import relativedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - relativedelta(months=months)
    
    trend_data = []
    for i in range(months):
        month_start = end_date - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        # Count approvals
        query = db.query(ApprovalInstance).filter(
            ApprovalInstance.created_at >= month_start,
            ApprovalInstance.created_at < month_end,
        )
        if project_id:
            query = query.filter(ApprovalInstance.project_id == project_id)
        
        count = query.count()
        
        trend_data.append({
            "month": month_start.strftime('%Y-%m'),
            "approvals": count,
        })
    
    return {"trend": trend_data[::-1]}
