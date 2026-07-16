"""
认证API - 登录/注册/Token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password, create_access_token, get_current_user
)
from app.models import User, Department
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from datetime import timedelta
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(req: UserCreate, db: Session = Depends(get_db)):
    """注册用户（需有管理员权限，这里简化为开放注册）"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 查找部门
    dept = db.query(Department).filter(Department.name == req.department).first()
    if not dept:
        raise HTTPException(status_code=400, detail=f"部门'{req.department}'不存在")
    
    user = User(
        username=req.username,
        real_name=req.real_name,
        department_id=dept.id,
        role=req.role,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新Token"""
    token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}
