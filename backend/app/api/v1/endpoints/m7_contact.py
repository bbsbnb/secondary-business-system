"""
M7 工作联系单 - 完整CRUD API
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
from app.schemas import BusinessFormCreate, BusinessFormResponse, AttachmentUpload, PaginatedResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")


@router.get("/list", response_model=List[dict])
async def list_contact_sheets(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询工作联系单列表"""
    query = db.query(BusinessForm).filter(BusinessForm.node_type == "M7")
    
    if project_id:
        query = query.filter(BusinessForm.project_id == project_id)
    if status:
        query = query.filter(BusinessForm.status == status)
    
    total = query.count()
    forms = query.order_by(BusinessForm.updated_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for f in forms:
        # Get approval instance status
        instance = db.query(ApprovalInstance).filter(
            ApprovalInstance.business_form_id == f.id,
            ApprovalInstance.node_type == "M7"
        ).order_by(ApprovalInstance.version.desc()).first()
        
        result.append({
            "id": f.id,
            "form_data": f.form_data,
            "status": f.status,
            "approval_status": instance.status if instance else "draft",
            "version": instance.version if instance else 1,
            "created_by": f.created_by,
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
async def get_contact_sheet(
    form_id: int,
    db: Session = Depends(get_db)
):
    """获取工作联系单详情"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="联系单不存在")
    
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.business_form_id == form_id,
        ApprovalInstance.node_type == "M7"
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
async def create_contact_sheet(
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建工作联系单"""
    # Validate required fields
    if not req.get("reason"):
        raise HTTPException(status_code=400, detail="事由不能为空")
    
    project_id = req.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="项目ID不能为空")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # Auto-generate contact number
    contact_no = f"LXD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    form_data = {
        **req,
        "contact_no": contact_no,
        "submit_date": datetime.now().strftime('%Y-%m-%d'),
    }
    
    form = BusinessForm(
        project_id=project_id,
        node_type="M7",
        form_data=form_data,
        created_by=current_user.id,
        status="submitted",
    )
    db.add(form)
    db.flush()
    
    # Create approval instance
    from app.services.workflow.engine import ApprovalEngine
    engine = ApprovalEngine(db)
    
    instance = engine.create_instance(
        node_type="M7",
        business_form_id=form.id,
        initiator_id=current_user.id,
        project_id=project_id,
    )
    engine.advance_to_next_step(instance)
    
    # Add to document library
    doc = ProjectDocument(
        project_id=project_id,
        category="contact",
        subcategory="联系单",
        title=f"联系单: {contact_no} - {req.get('reason', '')[:50]}",
        file_path="",
        file_type="document",
        uploaded_by=current_user.id,
        related_node="M7",
        related_form_id=form.id,
    )
    db.add(doc)
    
    db.commit()
    db.refresh(form)
    
    return {
        "id": form.id,
        "contact_no": contact_no,
        "status": "submitted",
        "message": "联系单已创建并提交审批",
    }


@router.put("/{form_id}", response_model=dict)
async def update_contact_sheet(
    form_id: int,
    req: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新工作联系单（仅草稿状态可编辑）"""
    form = db.query(BusinessForm).filter(
        BusinessForm.id == form_id,
        BusinessForm.status == "draft"
    ).first()
    
    if not form:
        raise HTTPException(status_code=400, detail="只有草稿状态的联系单可编辑")
    
    for key, value in req.items():
        if key not in ["project_id", "node_type"]:
            form.form_data[key] = value
    
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    
    return {
        "id": form.id,
        "form_data": form.form_data,
        "status": form.status,
        "message": "联系单已更新",
    }


@router.post("/{form_id}/upload-attachment", response_model=dict, status_code=201)
async def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    category: str = "supporting",
    db: Session = Depends(get_db)
):
    """上传附件到联系单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="联系单不存在")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, "M7", str(form.project_id))
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


@router.post("/{form_id}/submit", response_model=dict)
async def submit_contact_sheet(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交联系单审批"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="联系单不存在")
    
    if form.status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿状态可提交")
    
    # Check required fields
    data = form.form_data
    if not data.get("reason"):
        raise HTTPException(status_code=400, detail="事由不能为空")
    
    from app.services.workflow.engine import ApprovalEngine
    engine = ApprovalEngine(db)
    
    instance = engine.create_instance(
        node_type="M7",
        business_form_id=form_id,
        initiator_id=current_user.id,
        project_id=form.project_id,
    )
    engine.advance_to_next_step(instance)
    
    form.status = "submitted"
    db.commit()
    
    return {
        "success": True,
        "instance_id": instance.id,
        "message": "联系单已提交审批",
    }
