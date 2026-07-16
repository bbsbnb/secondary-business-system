"""
Pydantic Schema定义 - API请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


# ========== 用户相关 ==========
class UserBase(BaseModel):
    username: str
    real_name: str
    role: Optional[str] = None
    feishu_user_id: Optional[str] = None


class UserCreate(UserBase):
    password: str
    department: str  # 部门名称
    project_ids: Optional[List[int]] = []


class UserResponse(UserBase):
    id: int
    department_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== 项目相关 ==========
class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    contract_no: Optional[str] = None
    manager_id: Optional[int] = None


class ProjectResponse(BaseModel):
    id: int
    project_code: str
    project_name: str
    contract_no: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_id: int
    project_role: Optional[str] = None


# ========== 部门相关 ==========
class DepartmentResponse(BaseModel):
    id: int
    name: str
    feishu_dept_id: Optional[str] = None
    feishu_contacts: Optional[list] = None
    
    class Config:
        from_attributes = True


# ========== 基线数据(M1) ==========
class BaselineCreate(BaseModel):
    contract_price: Optional[Decimal] = None
    post_bid_cost: Optional[dict] = None  # 18张附表
    profit_retention_pct: Optional[Decimal] = None
    unbalanced_bidding_strategy: Optional[str] = None
    key_contract_terms: Optional[str] = None
    master_schedule: Optional[str] = None


class BaselineLockRequest(BaseModel):
    confirmed: bool = True


class BaselineUnlockRequest(BaseModel):
    reason: str
    approver_id: int


class BaselineResponse(BaseModel):
    id: int
    project_id: int
    contract_price: Optional[Decimal] = None
    profit_retention_pct: Optional[Decimal] = None
    locked: bool
    locked_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 审批引擎 ==========
class ApprovalInstanceCreate(BaseModel):
    node_type: str  # M2/M4/M6...
    business_form_id: int
    initiator_id: int


class ApprovalStepResponse(BaseModel):
    id: int
    step_order: int
    step_status: str
    assignee_id: Optional[int] = None
    opinion: Optional[str] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApprovalInstanceResponse(BaseModel):
    id: int
    project_id: int
    node_type: str
    version: int
    status: str
    current_step: int
    steps: List[ApprovalStepResponse] = []
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    decision: str  # approve / reject
    opinion: Optional[str] = ""


class ParallelReviewAction(BaseModel):
    """平行审核提交意见"""
    decision: str  # approved / rejected
    opinion: str


# ========== 业务表单 ==========
class BusinessFormCreate(BaseModel):
    project_id: int
    node_type: str
    form_data: dict
    template_type: Optional[str] = None
    template_id: Optional[int] = None


class BusinessFormUpdate(BaseModel):
    form_data: dict
    attachments: Optional[list] = None


class BusinessFormResponse(BaseModel):
    id: int
    project_id: int
    node_type: str
    form_data: dict
    attachments: list
    template_type: Optional[str] = None
    version: int
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========== 附件 ==========
class AttachmentUpload(BaseModel):
    file_path: str
    file_type: str  # docx/xls/pdf/jpg/png
    category: str  # contract/binding_photo/photo/document/template/evidence
    related_node: Optional[str] = None


class AttachmentResponse(BaseModel):
    id: int
    file_path: str
    file_type: str
    category: str
    file_size: Optional[int] = None
    uploaded_by: Optional[int] = None
    related_node: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 建造合同(M24) ==========
class ConstructionContractUpdate(BaseModel):
    """手动调整建造合同数据"""
    visa_amount: Optional[Decimal] = None
    claim_amount: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None
    verified_amount: Optional[Decimal] = None
    consumption_amount: Optional[Decimal] = None
    material_settlement: Optional[Decimal] = None
    over_budget_explanation: Optional[str] = None


class ConstructionContractResponse(BaseModel):
    id: int
    project_id: int
    month: str
    total_revenue: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    profit_ratio: Optional[Decimal] = None
    over_budget: bool
    over_budget_escalated: bool
    reviewed_at: Optional[datetime] = None
    archived: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 预警 ==========
class AlertResponse(BaseModel):
    id: int
    project_id: int
    node_type: Optional[str] = None
    alert_type: str
    severity: str
    message: str
    escalated: bool
    resolved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 资料库 ==========
class DocumentCreate(BaseModel):
    title: str
    category: str
    subcategory: Optional[str] = None
    file_path: str
    file_type: str
    related_node: Optional[str] = None
    related_form_id: Optional[int] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    subcategory: Optional[str] = None
    file_path: str
    file_type: str
    file_size: Optional[int] = None
    related_node: Optional[str] = None
    auto_categorized: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 模板 ==========
class TemplateCreate(BaseModel):
    node_type: str
    template_type: str  # docx/xls/standard
    name: str
    file_path: str
    fields_schema: Optional[dict] = None


class TemplateResponse(BaseModel):
    id: int
    node_type: str
    template_type: str
    name: str
    version: str
    is_active: bool
    fields_schema: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 通用分页 ==========
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    has_more: bool
