"""
M11 月验工计价 - 完整CRUD API（含平行审核）
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os
import uuid
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import BusinessForm, ApprovalInstance, ProjectDocument, Project, ParallelReviewGroup
from app.schemas import PaginatedResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")


@router.get("/list", response_model=dict)
async def list_verification_sheets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询验工计价单列表"""
    query = db.query(BusinessForm).filter(BusinessForm.node_type == "M11")
    
    if project_id:
        query = query.filter(BusinessForm.project_id == project_id)
    if status:
        query = query.filter(BusinessForm.status == status)
    
    total = query.count()
    forms = query.order_by(BusinessForm.updated_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for f in forms:
        instance = db.query(ApprovalInstance).filter(
            ApprovalInstance.business_form_id == f.id,
            ApprovalInstance.node_type == "M11"
        ).order_by(ApprovalInstance.version.desc()).first()
        
        amount = float(f.form_data.get("amount", 0))
        cumulative_amount = float(f.form_data.get("cumulative_amount", 0))
        contract_amount = float(f.form_data.get("contract_amount", 0))
        
        # Check over-budget (100% trigger T6)
        is_over_budget = contract_amount > 0 and cumulative_amount >= contract_amount
        
        result.append({
            "id": f.id,
            "form_data": f.form_data,
            "status": f.status,
            "approval_status": instance.status if instance else "draft",
            "version": instance.version if instance else 1,
            "amount": amount,
            "cumulative_amount": cumulative_amount,
            "contract_amount": contract_amount,
            "over_budget_pct": round(cumulative_amount / contract_amount * 100, 2) if contract_amount > 0 else 0,
            "is_over_budget": is_over_budget,
            "created_at": f.created_at.isoformat(),
            "updated_at": f.updated_at.isoformat(),
            "attachments": f.attachments or [],
        })
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "has_more": (page * page_size) < total,
    }


@router.get("/{form_id}", response_model=dict)
async def get_verification_sheet(
    form_id: int,
    db: Session = Depends(get_db)
):
    """获取验工计价单详情"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="验工计价单不存在")
    
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.business_form_id == form_id,
        ApprovalInstance.node_type == "M11"
    ).order_by(ApprovalInstance.version.desc()).first()
    
    steps = []
    parallel_group = None
    
    if instance:
        steps = [
            {
                "step_order": s.step_order,
                "step_status": s.step_status,
                "opinion": s.opinion,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            } for s in instance.steps
        ]
        
        parallel_group = db.query(ParallelReviewGroup).filter(
            ParallelReviewGroup.instance_id == instance.id
        ).first()
    
    return {
        "id": form.id,
        "form_data": form.form_data,
        "status": form.status,
        "version": form.version,
        "approval": {
            "instance_id": instance.id if instance else None,
            "status": instance.status if instance else "draft",
            "steps": steps,
            "parallel_group": {
                "group_status": parallel_group.group_status if parallel_group else None,
                "reviewer_ids": parallel_group.reviewer_ids if parallel_group else [],
                "all_approved": parallel_group.all_approved if parallel_group else False,
                "revision_count": parallel_group.revision_count if parallel_group else 0,
            } if parallel_group else None,
        },
        "attachments": form.attachments or [],
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat(),
    }


@router.post("/", response_model=dict, status_code=201)
async def create_verification_sheet(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建验工计价单"""
    if not req.get("description"):
        raise HTTPException(status_code=400, detail="说明不能为空")
    
    project_id = req.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="项目ID不能为空")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    verification_no = f"YJ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    form_data = {
        **req,
        "verification_no": verification_no,
        "submit_date": datetime.now().strftime('%Y-%m-%d'),
    }
    
    # Calculate over-budget status
    cumulative = float(req.get("cumulative_amount", 0))
    contract = float(req.get("contract_amount", 0))
    is_over_budget = contract > 0 and cumulative >= contract
    
    form = BusinessForm(
        project_id=project_id,
        node_type="M11",
        form_data=form_data,
        created_by=current_user.id,
        status="submitted",
    )
    db.add(form)
    db.flush()
    
    from app.services.workflow.engine import ApprovalEngine
    engine = ApprovalEngine(db)
    
    instance = engine.create_instance(
        node_type="M11",
        business_form_id=form.id,
        initiator_id=current_user.id,
        project_id=project_id,
    )
    engine.advance_to_next_step(instance)
    
    doc = ProjectDocument(
        project_id=project_id,
        category="verification",
        subcategory="验工计价",
        title=f"验工计价: {verification_no} - {req.get('description', '')[:50]}",
        file_path="",
        file_type="document",
        uploaded_by=current_user.id,
        related_node="M11",
        related_form_id=form.id,
    )
    db.add(doc)
    
    db.commit()
    db.refresh(form)
    
    return {
        "id": form.id,
        "verification_no": verification_no,
        "status": "submitted",
        "is_over_budget": is_over_budget,
        "message": "验工计价单已创建并提交审批",
    }


@router.put("/{form_id}", response_model=dict)
async def update_verification_sheet(
    form_id: int,
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新验工计价单（仅草稿状态可编辑）"""
    form = db.query(BusinessForm).filter(
        BusinessForm.id == form_id,
        BusinessForm.status == "draft"
    ).first()
    
    if not form:
        raise HTTPException(status_code=400, detail="只有草稿状态的验工计价单可编辑")
    
    for key, value in req.items():
        if key not in ["project_id", "node_type"]:
            form.form_data[key] = value
    
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "form_data": form.form_data, "message": "验工计价单已更新"}


@router.post("/{form_id}/upload-attachment", response_model=dict, status_code=201)
async def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    category: str = "supporting",
    db: Session = Depends(get_db)
):
    """上传附件到验工计价单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="验工计价单不存在")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, "M11", str(form.project_id))
    os.makedirs(node_dir, exist_ok=True)
    file_path = os.path.join(node_dir, unique_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    attachment = {
        "filename": file.filename,
        "file_path": file_path,
        "file_type": ext.lstrip("."),
        "category": category,
        "size": len(content),
    }
    
    attachments = form.attachments or []
    attachments.append(attachment)
    form.attachments = attachments
    db.commit()
    
    return {"message": "附件上传成功", "attachment": attachment}
