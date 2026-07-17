"""
项目资料库API - M21 + 全流程附件统一归档
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import ProjectDocument, Project
from app.schemas import DocumentCreate, DocumentResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "documents")


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    project_id: Optional[int] = None,
    category: Optional[str] = None,
    related_node: Optional[str] = None,
    auto_categorized: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """查询资料库文档"""
    query = db.query(ProjectDocument)
    if project_id:
        query = query.filter(ProjectDocument.project_id == project_id)
    if category:
        query = query.filter(ProjectDocument.category == category)
    if related_node:
        query = query.filter(ProjectDocument.related_node == related_node)
    if auto_categorized is not None:
        query = query.filter(ProjectDocument.auto_categorized == auto_categorized)
    
    total = query.count()
    docs = query.order_by(ProjectDocument.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/", response_model=DocumentResponse, status_code=201)
async def create_document(
    req: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加文档到资料库 (project_id 需从调用方传入)"""
    raise HTTPException(status_code=501, detail="请使用 POST /documents/upload 接口上传文档")


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    title: str,
    category: str,
    project_id: int,
    subcategory: Optional[str] = None,
    related_node: Optional[str] = None,
    related_form_id: Optional[int] = None,
    file: UploadFile = File(...),
    auto_categorized: bool = False,
    db: Session = Depends(get_db)
):
    """上传文档到资料库"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    cat_dir = os.path.join(UPLOAD_DIR, category, str(project_id))
    os.makedirs(cat_dir, exist_ok=True)
    file_path = os.path.join(cat_dir, unique_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    doc = ProjectDocument(
        project_id=project_id,
        title=title,
        category=category,
        subcategory=subcategory,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=len(content),
        uploaded_by=None,
        related_node=related_node,
        related_form_id=related_form_id,
        auto_categorized=auto_categorized,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """删除文档"""
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除物理文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
