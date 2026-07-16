"""
M10 设计变更执行 - 完整CRUD API
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
from app.models import BusinessForm, ApprovalInstance, ProjectDocument, Project
from app.schemas import PaginatedResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")


@router.get("/list", response_model=dict)
async def list_change_sheets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询设计变更列表"""
    query = db.query(BusinessForm).filter(BusinessForm.node_type == "M10")
    
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
            ApprovalInstance.node_type == "M10"
        ).order_by(ApprovalInstance.version.desc()).first()
        
        amount = float(f.form_data.get("amount", 0))
        
        result.append({
            "id": f.id,
            "form_data": f.form_data,
            "status": f.status,
            "approval_status": instance.status if instance else "draft",
            "version": instance.version if instance else 1,
            "amount": amount,
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
async def get_change_sheet(
    form_id: int,
    db: Session = Depends(get_db)
):
    """获取设计变更详情"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="设计变更不存在")
    
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.business_form_id == form_id,
        ApprovalInstance.node_type == "M10"
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
async def create_change_sheet(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建设计变更单"""
    if not req.get("description"):
        raise HTTPException(status_code=400, detail="说明不能为空")
    
    project_id = req.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="项目ID不能为空")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    change_no = f"BGR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    form_data = {
        **req,
        "change_no": change_no,
        "submit_date": datetime.now().strftime('%Y-%m-%d'),
    }
    
    form = BusinessForm(
        project_id=project_id,
        node_type="M10",
        form_data=form_data,
        created_by=current_user.id,
        status="submitted",
    )
    db.add(form)
    db.flush()
    
    from app.services.workflow.engine import ApprovalEngine
    engine = ApprovalEngine(db)
    
    instance = engine.create_instance(
        node_type="M10",
        business_form_id=form.id,
        initiator_id=current_user.id,
        project_id=project_id,
    )
    engine.advance_to_next_step(instance)
    
    doc = ProjectDocument(
        project_id=project_id,
        category="change",
        subcategory="设计变更",
        title=f"设计变更: {change_no} - {req.get('description', '')[:50]}",
        file_path="",
        file_type="document",
        uploaded_by=current_user.id,
        related_node="M10",
        related_form_id=form.id,
    )
    db.add(doc)
    
    db.commit()
    db.refresh(form)
    
    return {
        "id": form.id,
        "change_no": change_no,
        "status": "submitted",
        "message": "设计变更已创建并提交审批",
    }


@router.put("/{form_id}", response_model=dict)
async def update_change_sheet(
    form_id: int,
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新设计变更单（仅草稿状态可编辑）"""
    form = db.query(BusinessForm).filter(
        BusinessForm.id == form_id,
        BusinessForm.status == "draft"
    ).first()
    
    if not form:
        raise HTTPException(status_code=400, detail="只有草稿状态的设计变更可编辑")
    
    for key, value in req.items():
        if key not in ["project_id", "node_type"]:
            form.form_data[key] = value
    
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    
    return {"id": form.id, "form_data": form.form_data, "message": "设计变更已更新"}


@router.post("/{form_id}/upload-attachment", response_model=dict, status_code=201)
async def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    category: str = "supporting",
    db: Session = Depends(get_db)
):
    """上传附件到设计变更单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="设计变更不存在")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, "M10", str(form.project_id))
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
