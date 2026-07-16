"""
部门管理API - 8部门初始化与查询
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Department
from app.schemas import DepartmentResponse
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=list[DepartmentResponse])
async def list_departments(db: Session = Depends(get_db)):
    """获取所有部门列表"""
    depts = db.query(Department).order_by(Department.id).all()
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.post("/init-defaults", status_code=201)
async def init_default_departments(db: Session = Depends(get_db)):
    """初始化8个默认部门（幂等操作）"""
    created = []
    for name in settings.DEPARTMENTS:
        existing = db.query(Department).filter(Department.name == name).first()
        if not existing:
            dept = Department(name=name)
            db.add(dept)
            created.append(name)
    
    if created:
        db.commit()
    
    depts = db.query(Department).order_by(Department.id).all()
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(dept_id: int, db: Session = Depends(get_db)):
    """获取单个部门详情"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    return DepartmentResponse.model_validate(dept)
