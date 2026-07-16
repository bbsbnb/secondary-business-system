"""
业务表单API - 通用表单CRUD
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
from app.models import BusinessForm, Template, Project
from app.schemas import BusinessFormCreate, BusinessFormUpdate, BusinessFormResponse, PaginatedResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")


@router.get("/", response_model=List[BusinessFormResponse])
async def list_forms(
    node_type: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """查询业务表单列表"""
    query = db.query(BusinessForm)
    if node_type:
        query = query.filter(BusinessForm.node_type == node_type)
    if project_id:
        query = query.filter(BusinessForm.project_id == project_id)
    if status:
        query = query.filter(BusinessForm.status == status)
    
    total = query.count()
    forms = query.order_by(BusinessForm.updated_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    
    return [BusinessFormResponse.model_validate(f) for f in forms]


@router.get("/{form_id}", response_model=BusinessFormResponse)
async def get_form(form_id: int, db: Session = Depends(get_db)):
    """获取表单详情"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    return BusinessFormResponse.model_validate(form)


@router.post("/", response_model=BusinessFormResponse, status_code=201)
async def create_form(
    req: BusinessFormCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建业务表单"""
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    form = BusinessForm(
        project_id=req.project_id,
        node_type=req.node_type,
        form_data=req.form_data,
        template_type=req.template_type,
        template_id=req.template_id,
        created_by=current_user.id,
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return BusinessFormResponse.model_validate(form)


@router.put("/{form_id}", response_model=BusinessFormResponse)
async def update_form(
    form_id: int,
    req: BusinessFormUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新业务表单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    
    form.form_data = req.form_data
    if req.attachments is not None:
        form.attachments = req.attachments
    form.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(form)
    return BusinessFormResponse.model_validate(form)


@router.post("/{form_id}/upload-attachment", status_code=201)
async def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    category: str = "document",
    related_node: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """上传附件到表单"""
    form = db.query(BusinessForm).filter(BusinessForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    
    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, form.node_type, str(form.project_id))
    os.makedirs(node_dir, exist_ok=True)
    file_path = os.path.join(node_dir, unique_name)
    
    # 保存文件
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    attachment = {
        "filename": file.filename,
        "file_path": file_path,
        "file_type": ext.lstrip("."),
        "category": category,
        "related_node": related_node,
        "size": len(content),
    }
    
    # 追加到attachments列表
    attachments = form.attachments or []
    attachments.append(attachment)
    form.attachments = attachments
    db.commit()
    
    return {"message": "附件上传成功", "attachment": attachment}
