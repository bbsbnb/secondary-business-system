"""
M9 索赔价差执行 - 完整CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import os
import uuid
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import BusinessForm, ApprovalInstance, ProjectDocument, Project
from app.schemas import PaginatedResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")


@router.get("/list", response_model=dict)
async def list_claim_sheets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询索赔单列表"""
    query = db.query(BusinessForm).filter(BusinessForm.node_type == "M9")
    
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
            ApprovalInstance.node_type == "M9"
        ).order_by(ApprovalInstance.version.desc()).first()
        
        amount = float(f.form_data.get("amount", 0))
        
        # Calculate dual 28-day countdowns
        created_at = f.created_at
        day1_deadline = created_at + timedelta(days=28)  # 意向书28天
        day2_deadline = day1_deadline + timedelta(days=28)  # 报审单28天
        
        days_left_1 = max(0, (day1_deadline - datetime.utcnow()).days)
        days_left_2 = max(0, (day2_deadline - datetime.utcnow()).days)
        
        result.append({
            "id": f.id,
            "form_data": f.form_data,
            "status": f.status,
            "approval_status": instance.status if instance else "draft",
            "version": instance.version if instance else 1,
            "amount": amount,
            "days_left_phase1": days_left_1,
            "days_left_phase2": days_left_2,
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
async def get_claim_sheet(
    form_id: int,
    db: Session = Depends(get_db)
):
    """获取索赔单详情"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="索赔单不存在")
    
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.business_form_id == form_id,
        ApprovalInstance.node_type == "M9"
    ).order_by(ApprovalInstance.version.desc()).first()
    
    steps = []
    if instance:
        steps = [
            {
                "step_order": s.step_order,
                "step_status": s.step_status,
                "opinion": s.opinion,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            } for s in instance.steps
        ]
    
    return {
        "id": form.id,
        "form_data": form.form_data,
        "status": form.status,
        "version": form.version,
        "approval": {
            "instance_id": instance.id if instance else None,
            "status": instance.status if instance else "draft",
            "steps": steps,
        },
        "attachments": form.attachments or [],
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat(),
    }


@router.post("/", response_model=dict, status_code=201)
async def create_claim_sheet(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建索赔单"""
    if not req.get("description"):
        raise HTTPException(status_code=400, detail="说明不能为空")
    
    project_id = req.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="项目ID不能为空")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    claim_no = f"SQ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    form_data = {
        **req,
        "claim_no": claim_no,
        "submit_date": datetime.now().strftime('%Y-%m-%d'),
    }
    
    amount = float(req.get("amount", 0))
    if amount < 0:
        raise HTTPException(status_code=400, detail="金额不能为负数")
    
    # Check if amount > 10万 (requires additional approval)
    requires_extra_approval = amount > 100000
    
    form = BusinessForm(
        project_id=project_id,
        node_type="M9",
        form_data=form_data,
        created_by=current_user.id,
        status="submitted",
    )
    db.add(form)
    db.flush()
    
    from app.services.workflow.engine import ApprovalEngine
    engine = ApprovalEngine(db)
    
    instance = engine.create_instance(
        node_type="M9",
        business_form_id=form.id,
        initiator_id=current_user.id,
        project_id=project_id,
    )
    engine.advance_to_next_step(instance)
    
    doc = ProjectDocument(
        project_id=project_id,
        category="claim",
        subcategory="索赔单",
        title=f"索赔单: {claim_no} - {req.get('description', '')[:50]}",
        file_path="",
        file_type="document",
        uploaded_by=current_user.id,
        related_node="M9",
        related_form_id=form.id,
    )
    db.add(doc)
    
    db.commit()
    db.refresh(form)
    
    return {
        "id": form.id,
        "claim_no": claim_no,
        "status": "submitted",
        "requires_extra_approval": requires_extra_approval,
        "message": "索赔单已创建并提交审批",
    }


@router.put("/{form_id}", response_model=dict)
async def update_claim_sheet(
    form_id: int,
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新索赔单（仅草稿状态可编辑）"""
    form = db.query(BusinessForm).filter(
        BusinessForm.id == form_id,
        BusinessForm.status == "draft"
    ).first()
    
    if not form:
        raise HTTPException(status_code=400, detail="只有草稿状态的索赔单可编辑")
    
    for key, value in req.items():
        if key not in ["project_id", "node_type"]:
            form.form_data[key] = value
    
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "form_data": form.form_data, "message": "索赔单已更新"}


@router.post("/{form_id}/upload-attachment", response_model=dict, status_code=201)
async def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    category: str = "evidence",
    db: Session = Depends(get_db)
):
    """上传附件到索赔单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="索赔单不存在")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, "M9", str(form.project_id))
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
