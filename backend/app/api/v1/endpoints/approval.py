"""
审批引擎API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import ApprovalInstance, ApprovalStep, ApprovalStepTemplate, ParallelReviewGroup, BusinessForm, Project
from app.services.workflow.engine import ApprovalEngine
from app.schemas import (
    ApprovalInstanceCreate, ApprovalAction,
    ApprovalInstanceResponse, ApprovalStepResponse,
    ParallelReviewAction, PaginatedResponse
)

router = APIRouter()


@router.post("/instances", response_model=dict, status_code=201)
async def create_approval_instance(
    req: ApprovalInstanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建审批实例"""
    engine = ApprovalEngine(db)
    
    # Validate node_type
    valid_nodes = ["M1","M2","M3","M4","M5","M6","M7","M8","M9","M10",
                   "M11","M12","M13","M14","M15","M16","M17","M18","M19",
                   "M20","M21","M22","M23","M24","M25"]
    if req.node_type not in valid_nodes:
        raise HTTPException(status_code=400, detail=f"无效的节点类型: {req.node_type}")
    
    # Get project_id from business form
    form = db.query(BusinessForm).filter(BusinessForm.id == req.business_form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="业务表单不存在")
    
    instance = engine.create_instance(
        node_type=req.node_type,
        business_form_id=req.business_form_id,
        initiator_id=current_user.id,
        project_id=form.project_id,
    )
    
    # Advance to first step
    engine.advance_to_next_step(instance)
    
    return {
        "id": instance.id,
        "node_type": instance.node_type,
        "status": instance.status,
        "current_step": instance.current_step,
        "version": instance.version,
        "created_at": instance.created_at.isoformat(),
    }


@router.get("/my-pending", response_model=List[dict])
async def my_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """我的待办审批"""
    engine = ApprovalEngine(db)
    instances = engine.get_user_pending_approvals(current_user.id)
    
    result = []
    for i in instances:
        steps = [
            {
                "step_order": s.step_order,
                "step_status": s.step_status,
                "opinion": s.opinion,
            } for s in i.steps
        ]
        result.append({
            "id": i.id,
            "node_type": i.node_type,
            "version": i.version,
            "status": i.status,
            "steps": steps,
            "created_at": i.created_at.isoformat(),
        })
    return result


@router.get("/my-history", response_model=List[dict])
async def my_history(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """我的已办历史"""
    engine = ApprovalEngine(db)
    instances = engine.get_user_history(current_user.id, limit)
    
    result = []
    for i in instances:
        steps = [
            {
                "step_order": s.step_order,
                "step_status": s.step_status,
                "opinion": s.opinion,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            } for s in i.steps
        ]
        result.append({
            "id": i.id,
            "node_type": i.node_type,
            "version": i.version,
            "status": i.status,
            "steps": steps,
            "created_at": i.created_at.isoformat(),
            "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        })
    return result


@router.get("/{instance_id}", response_model=dict)
async def get_approval_instance(
    instance_id: int,
    db: Session = Depends(get_db)
):
    """获取审批实例详情"""
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.id == instance_id
    ).first()
    if not instance:
        raise HTTPException(status_code=404, detail="审批实例不存在")
    
    steps = [
        {
            "id": s.id,
            "step_order": s.step_order,
            "step_status": s.step_status,
            "assignee_id": s.assignee_id,
            "opinion": s.opinion,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "timeout_at": s.timeout_at.isoformat() if s.timeout_at else None,
        } for s in instance.steps
    ]
    
    return {
        "id": instance.id,
        "project_id": instance.project_id,
        "node_type": instance.node_type,
        "version": instance.version,
        "status": instance.status,
        "current_step": instance.current_step,
        "steps": steps,
        "created_at": instance.created_at.isoformat(),
        "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
    }


@router.post("/{instance_id}/approve", response_model=dict)
async def approve_step(
    instance_id: int,
    req: ApprovalAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批通过"""
    engine = ApprovalEngine(db)
    
    step = db.query(ApprovalStep).filter(
        ApprovalStep.instance_id == instance_id,
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).first()
    
    if not step:
        raise HTTPException(status_code=403, detail="您没有待审批的步骤")
    
    try:
        instance = engine.submit_approval(
            step_id=step.id,
            user_id=current_user.id,
            decision="approve",
            opinion=req.opinion or "",
        )
        
        return {
            "success": True,
            "instance_id": instance.id,
            "status": instance.status,
            "message": "审批已通过" if instance.status == "active" else "审批已完成",
        }
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{instance_id}/reject", response_model=dict)
async def reject_step(
    instance_id: int,
    req: ApprovalAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批不通过（退回）"""
    engine = ApprovalEngine(db)
    
    step = db.query(ApprovalStep).filter(
        ApprovalStep.instance_id == instance_id,
        ApprovalStep.assignee_id == current_user.id,
        ApprovalStep.step_status == "pending"
    ).first()
    
    if not step:
        raise HTTPException(status_code=403, detail="您没有待审批的步骤")
    
    if not req.opinion:
        raise HTTPException(status_code=400, detail="驳回必须填写意见")
    
    try:
        instance = engine.submit_approval(
            step_id=step.id,
            user_id=current_user.id,
            decision="reject",
            opinion=req.opinion,
        )
        
        return {
            "success": True,
            "instance_id": instance.id,
            "status": instance.status,
            "message": "已退回",
        }
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{node_type}", response_model=List[dict])
async def get_node_template(
    node_type: str,
    db: Session = Depends(get_db)
):
    """查看某节点的审批模板定义"""
    templates = db.query(ApprovalStepTemplate).filter(
        ApprovalStepTemplate.node_type == node_type
    ).order_by(ApprovalStepTemplate.step_order).all()
    
    result = []
    for t in templates:
        result.append({
            "step_order": t.step_order,
            "department_id": t.department_id,
            "role": t.role,
            "is_mandatory": t.is_mandatory,
            "constraint_code": t.constraint_code,
            "is_parallel": t.is_parallel,
            "timeout_days": t.timeout_days,
        })
    return result


@router.post("/templates/init-defaults", status_code=201)
async def init_default_templates(db: Session = Depends(get_db)):
    """初始化所有节点的默认审批模板"""
    from app.models import ApprovalStepTemplate
    
    templates_to_init = {
        "M2": [
            {"step_order": 1, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 2, "role": "工程管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 7, "role": "生产副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
        ],
        "M4": [
            {"step_order": 1, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 2, "role": "工程管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 4, "department_id": 7, "role": "经营副总", "is_mandatory": True, "constraint_code": "T5", "is_parallel": False, "timeout_days": 2},
        ],
        "M6": [
            {"step_order": 1, "department_id": 1, "role": "施工员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 4, "role": "采购人员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 4, "department_id": 1, "role": "总工", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 5, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
        ],
        "M7": [
            {"step_order": 1, "department_id": 1, "role": "施工员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "总工", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 4, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
        ],
        "M8": [
            {"step_order": 1, "department_id": 1, "role": "施工员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "总工", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 4, "department_id": 2, "role": "工程管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 5, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 6, "department_id": 7, "role": "生产副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 7, "department_id": 7, "role": "总经理", "is_mandatory": True, "constraint_code": "T1", "is_parallel": False, "timeout_days": 2},
        ],
        "M9": [
            {"step_order": 1, "department_id": 1, "role": "施工员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 1, "role": "总工", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 4, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 5, "department_id": 2, "role": "工程管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 6, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 7, "department_id": 7, "role": "生产副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 8, "department_id": 7, "role": "总经理", "is_mandatory": True, "constraint_code": "T1", "is_parallel": False, "timeout_days": 2},
        ],
        "M10": [
            {"step_order": 1, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 4, "role": "采购人员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
        ],
        "M11": [
            {"step_order": 1, "department_id": 1, "role": "施工员", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "材料员", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 3, "department_id": 1, "role": "质量员", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 4, "department_id": 1, "role": "安全员", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 5, "department_id": 1, "role": "生产经理", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 6, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": True, "timeout_days": 2},
            {"step_order": 7, "department_id": 5, "role": "合同管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 8, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 9, "department_id": 7, "role": "分管副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 10, "department_id": 6, "role": "财务主管", "is_mandatory": True, "constraint_code": "T1", "is_parallel": False, "timeout_days": 2},
        ],
        "M12": [
            {"step_order": 1, "department_id": 4, "role": "采购人员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "材料员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 5, "role": "合同管理员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 4, "department_id": 3, "role": "造价工程师", "is_mandatory": True, "constraint_code": "T2", "is_parallel": False, "timeout_days": 3},
            {"step_order": 5, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 6, "department_id": 7, "role": "分管副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 7, "department_id": 6, "role": "财务主管", "is_mandatory": True, "constraint_code": "T1", "is_parallel": False, "timeout_days": 2},
        ],
        "M13": [
            {"step_order": 1, "department_id": 1, "role": "材料员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 1, "role": "生产经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 3, "department_id": 4, "role": "采购人员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 4, "department_id": 6, "role": "财务人员", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 5, "department_id": 3, "role": "造价工程师", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
        ],
        "M24": [
            {"step_order": 1, "department_id": 3, "role": "造价工程师", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 3},
        ],
        "M25": [
            {"step_order": 1, "department_id": 1, "role": "项目经理", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
            {"step_order": 2, "department_id": 7, "role": "经营副总", "is_mandatory": False, "constraint_code": None, "is_parallel": False, "timeout_days": 2},
        ],
    }
    
    created = 0
    for node_type, steps in templates_to_init.items():
        db.query(ApprovalStepTemplate).filter(
            ApprovalStepTemplate.node_type == node_type
        ).delete()
        
        for step in steps:
            t = ApprovalStepTemplate(node_type=node_type, **step)
            db.add(t)
            created += 1
    
    db.commit()
    return {"message": f"已初始化 {created} 个审批步骤模板", "nodes": list(templates_to_init.keys())}
