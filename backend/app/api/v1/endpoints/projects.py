"""
项目管理API - 项目CRUD + 成员管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Project, ProjectMember
from app.schemas import ProjectCreate, ProjectResponse, ProjectMemberAdd, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    status_filter: str = "active"
):
    """获取当前用户参与的项目列表"""
    projects = db.query(Project).filter(
        Project.status == status_filter
    ).order_by(Project.created_at.desc()).all()
    
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ProjectResponse.model_validate(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新项目（创建者自动成为项目成员）"""
    # 检查编号唯一
    if db.query(Project).filter(Project.project_code == req.project_code).first():
        raise HTTPException(status_code=400, detail="项目编号已存在")
    
    project = Project(
        project_code=req.project_code,
        project_name=req.project_name,
        contract_no=req.contract_no,
        manager_id=req.manager_id or current_user.id,
    )
    db.add(project)
    db.flush()
    
    # 创建者自动加入
    member = ProjectMember(project_id=project.id, user_id=current_user.id, project_role="creator")
    db.add(member)
    
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/members", status_code=201)
async def add_member(
    project_id: int,
    req: ProjectMemberAdd,
    db: Session = Depends(get_db)
):
    """添加项目成员"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已存在
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == req.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是项目成员")
    
    member = ProjectMember(
        project_id=project_id,
        user_id=req.user_id,
        project_role=req.project_role
    )
    db.add(member)
    db.commit()
    return {"message": f"用户{user.real_name}已添加到项目"}


@router.delete("/{project_id}", status_code=204)
async def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a project without deleting related workflow data."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="无权操作此项目")

    project.status = "archived"
    db.commit()
    return None


@router.get("/{project_id}/members", response_model=List[dict])
async def list_members(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目成员列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append({
            "user_id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "department": user.department.name if user.department else None,
            "role": user.role,
            "project_role": m.project_role,
        })
    return result
