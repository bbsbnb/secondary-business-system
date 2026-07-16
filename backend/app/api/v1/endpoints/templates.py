"""
模板管理API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import Template
from app.schemas import TemplateCreate, TemplateResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "templates")


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    node_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """查询模板列表"""
    query = db.query(Template)
    if node_type:
        query = query.filter(Template.node_type == node_type)
    if active_only:
        query = query.filter(Template.is_active == True)
    
    templates = query.order_by(Template.node_type, Template.name).all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(
    req: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建模板"""
    template = Template(
        node_type=req.node_type,
        template_type=req.template_type,
        name=req.name,
        file_path=req.file_path,
        fields_schema=req.fields_schema,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.post("/upload", response_model=TemplateResponse, status_code=201)
async def upload_template_file(
    node_type: str,
    template_type: str,
    name: str,
    file: UploadFile = File(...),
    fields_schema: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """上传模板文件(.docx/.xls)"""
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    node_dir = os.path.join(UPLOAD_DIR, node_type)
    os.makedirs(node_dir, exist_ok=True)
    file_path = os.path.join(node_dir, unique_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    import json
    schema = None
    if fields_schema:
        try:
            schema = json.loads(fields_schema)
        except:
            pass
    
    template = Template(
        node_type=node_type,
        template_type=template_type,
        name=name,
        file_path=file_path,
        fields_schema=schema,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}/activate")
async def activate_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """激活模板（停用同类型其他模板）"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 停用同node_type的其他模板
    db.query(Template).filter(
        Template.node_type == template.node_type,
        Template.id != template_id
    ).update({"is_active": False})
    
    template.is_active = True
    db.commit()
    return {"message": "模板已激活"}
