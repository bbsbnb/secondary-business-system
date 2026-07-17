"""
建造合同API - M24数据枢纽
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models import ConstructionContract, Project, BaselineData
from app.schemas import ConstructionContractResponse, ConstructionContractUpdate

router = APIRouter()


def recalculate_contract(contract: ConstructionContract) -> None:
    revenue = (
        (contract.original_contract_amount or Decimal('0'))
        + (contract.visa_amount or Decimal('0'))
        + (contract.claim_amount or Decimal('0'))
        + (contract.change_amount or Decimal('0'))
    )
    cost = (
        (contract.verified_amount or Decimal('0'))
        + (contract.consumption_amount or Decimal('0'))
        + (contract.material_settlement or Decimal('0'))
        + (contract.cost_adjustment_summary or Decimal('0'))
    )
    profit = revenue - cost
    ratio = float(profit / revenue * 100) if revenue > 0 else 0

    contract.total_revenue = revenue
    contract.total_cost = cost
    contract.profit_amount = profit
    contract.profit_ratio = round(ratio, 2)
    contract.over_budget = cost > revenue if revenue > 0 else False


@router.get("/{project_id}/{month}", response_model=ConstructionContractResponse)
async def get_contract(
    project_id: int,
    month: str,
    db: Session = Depends(get_db)
):
    """获取某项目某月的建造合同数据"""
    contract = db.query(ConstructionContract).filter(
        ConstructionContract.project_id == project_id,
        ConstructionContract.month == month
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="该月建造合同数据不存在")
    return ConstructionContractResponse.model_validate(contract)


@router.post("/{project_id}/{month}", response_model=ConstructionContractResponse, status_code=201)
async def create_or_update_contract(
    project_id: int,
    month: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建/更新建造合同数据（系统自动聚合+人工复核）"""
    # 获取基线数据
    baseline = db.query(BaselineData).filter(
        BaselineData.project_id == project_id
    ).first()
    
    retention_target = float(baseline.profit_retention_pct) if baseline else 8.0
    
    contract = db.query(ConstructionContract).filter(
        ConstructionContract.project_id == project_id,
        ConstructionContract.month == month
    ).first()
    
    if not contract:
        contract = ConstructionContract(
            project_id=project_id,
            month=month,
            retention_target=retention_target,
        )
        db.add(contract)
    
    # 计算利润
    was_over_budget = bool(contract.over_budget)
    recalculate_contract(contract)
    
    # 超概检测
    if contract.over_budget:
        if not was_over_budget:
            contract.over_budget_deadline = datetime.utcnow() + timedelta(days=3)
    
    db.commit()
    db.refresh(contract)
    return ConstructionContractResponse.model_validate(contract)


@router.put("/{project_id}/{month}", response_model=ConstructionContractResponse)
async def update_contract(
    project_id: int,
    month: str,
    req: ConstructionContractUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动调整建造合同数据"""
    contract = db.query(ConstructionContract).filter(
        ConstructionContract.project_id == project_id,
        ConstructionContract.month == month
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="建造合同数据不存在")
    
    for field, value in req.model_dump().items():
        if value is not None:
            setattr(contract, field, value)
    was_over_budget = bool(contract.over_budget)
    recalculate_contract(contract)
    if contract.over_budget and not was_over_budget:
        contract.over_budget_deadline = datetime.utcnow() + timedelta(days=3)
    
    db.commit()
    db.refresh(contract)
    return ConstructionContractResponse.model_validate(contract)


@router.get("/list/{project_id}", response_model=list[ConstructionContractResponse])
async def list_contracts(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目所有月份的建造合同数据"""
    contracts = db.query(ConstructionContract).filter(
        ConstructionContract.project_id == project_id
    ).order_by(ConstructionContract.month.desc()).all()
    return [ConstructionContractResponse.model_validate(c) for c in contracts]
