"""
基线数据API - M1一次经营交底数据录入
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Project, BaselineData
from app.schemas import BaselineCreate, BaselineLockRequest, BaselineUnlockRequest, BaselineResponse

router = APIRouter()


@router.get("/{project_id}", response_model=BaselineResponse)
async def get_baseline(project_id: int, db: Session = Depends(get_db)):
    """获取项目基线数据"""
    baseline = db.query(BaselineData).filter(BaselineData.project_id == project_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="该项目尚未录入基线数据")
    return BaselineResponse.model_validate(baseline)


@router.post("/{project_id}", response_model=BaselineResponse, status_code=201)
async def create_baseline(
    project_id: int,
    req: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建基线数据（M1录入）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否已有基线
    existing = db.query(BaselineData).filter(BaselineData.project_id == project_id).first()
    if existing:
        if existing.locked:
            raise HTTPException(status_code=400, detail="基线已锁定，不可修改。如需修改请申请解锁。")
        # 更新未锁定基线
        for field, value in req.model_dump().items():
            if value is not None:
                setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return BaselineResponse.model_validate(existing)
    
    baseline = BaselineData(
        project_id=project_id,
        contract_price=req.contract_price,
        post_bid_cost=req.post_bid_cost,
        profit_retention_pct=req.profit_retention_pct,
        unbalanced_bidding_strategy=req.unbalanced_bidding_strategy,
        key_contract_terms=req.key_contract_terms,
        master_schedule=req.master_schedule,
        created_by=current_user.id,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return BaselineResponse.model_validate(baseline)


@router.post("/{project_id}/lock", response_model=BaselineResponse)
async def lock_baseline(
    project_id: int,
    req: BaselineLockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """锁定基线数据（不可逆操作）"""
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="需要确认锁定")
    
    baseline = db.query(BaselineData).filter(BaselineData.project_id == project_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="基线数据不存在")
    
    baseline.locked = True
    baseline.locked_at = db.func.now()
    db.commit()
    db.refresh(baseline)
    return BaselineResponse.model_validate(baseline)


@router.post("/{project_id}/unlock", response_model=BaselineResponse)
async def unlock_baseline(
    project_id: int,
    req: BaselineUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解锁基线数据（需留痕）"""
    baseline = db.query(BaselineData).filter(BaselineData.project_id == project_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="基线数据不存在")
    if not baseline.locked:
        raise HTTPException(status_code=400, detail="基线未锁定，无需解锁")
    
    baseline.locked = False
    baseline.unlocked_reason = req.reason
    baseline.unlocked_by = req.approver_id
    baseline.unlocked_at = db.func.now()
    db.commit()
    db.refresh(baseline)
    return BaselineResponse.model_validate(baseline)
