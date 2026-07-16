"""
数据库模型 - 所有核心表
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, 
    DECIMAL, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    """项目表 - 数据隔离边界"""
    __tablename__ = "projects"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    project_name = Column(String(200), nullable=False)
    contract_no = Column(String(100))
    manager_id = Column(BigInteger, ForeignKey("users.id"))
    status = Column(String(20), default="active")  # active / archived
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    members = relationship("ProjectMember", back_populates="project")
    baseline = relationship("BaselineData", back_populates="project", uselist=False)
    forms = relationship("BusinessForm", back_populates="project")
    approvals = relationship("ApprovalInstance", back_populates="project")
    documents = relationship("ProjectDocument", back_populates="project")
    contracts = relationship("ConstructionContract", back_populates="project")
    alerts = relationship("Alert", back_populates="project")


class Department(Base):
    """部门表 - 8部门"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # 项目部/工程部/造价部等
    feishu_dept_id = Column(String(100))
    feishu_contacts = Column(JSON, default=list)  # 部门负责人联系人列表
    
    users = relationship("User", back_populates="department")


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    real_name = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    role = Column(String(50))  # 项目经理/施工员/造价员等
    password_hash = Column(String(255), nullable=False)
    feishu_user_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    department = relationship("Department", back_populates="users")
    projects = relationship("ProjectMember", back_populates="user")
    
    @property
    def department_name(self):
        return self.department.name if self.department else None


class ProjectMember(Base):
    """项目-用户关联"""
    __tablename__ = "project_members"
    
    project_id = Column(BigInteger, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    project_role = Column(String(50))
    
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="projects")


class BaselineData(Base):
    """基线数据表 - M1产出"""
    __tablename__ = "baseline_data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), unique=True, nullable=False)
    contract_price = Column(DECIMAL(18, 2))  # 中标合同价
    post_bid_cost = Column(JSON)  # 标后成本(18张附表)
    profit_retention_pct = Column(DECIMAL(5, 2))  # 利润留存点(≥8%)
    unbalanced_bidding_strategy = Column(Text)  # 不平衡报价策略
    key_contract_terms = Column(Text)  # 合同关键条款
    master_schedule = Column(Text)  # 总进度计划
    locked = Column(Boolean, default=False)  # 基线锁定状态
    locked_at = Column(DateTime)
    unlocked_reason = Column(Text)  # 解锁原因(留痕)
    unlocked_by = Column(BigInteger, ForeignKey("users.id"))
    unlocked_at = Column(DateTime)
    created_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="baseline")


class ApprovalStepTemplate(Base):
    """审批步骤定义模板 - 每个节点类型一套流程定义"""
    __tablename__ = "approval_step_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(20), nullable=False, index=True)  # M2/M4/M6...
    step_order = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    role = Column(String(50))  # 审批角色
    is_mandatory = Column(Boolean, default=False)  # 是否铁律节点(★)
    constraint_code = Column(String(10))  # T1/T2/T3/T5/T6
    is_parallel = Column(Boolean, default=False)  # 是否平行审核节点
    branch_condition = Column(JSON)  # 条件分支表达式
    timeout_days = Column(Integer)  # 超时天数(自然日)
    
    __table_args__ = (
        Index("ix_node_type_order", "node_type", "step_order"),
    )


class ApprovalInstance(Base):
    """审批实例 - 每个节点类型的一个具体发起实例"""
    __tablename__ = "approval_instances"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False, index=True)
    node_type = Column(String(20), nullable=False, index=True)  # M2/M4/M6...
    business_form_id = Column(BigInteger, ForeignKey("business_forms.id"))
    version = Column(Integer, default=1)  # 版本号(修订计数)
    status = Column(String(20), default="draft")  # draft/active/completed/rejected
    initiator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    current_step = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    project = relationship("Project", back_populates="approvals")
    steps = relationship("ApprovalStep", back_populates="instance", order_by="ApprovalStep.step_order")
    
    __table_args__ = (
        Index("ix_project_node_version", "project_id", "node_type", "business_form_id", "version", unique=True),
    )


class ApprovalStep(Base):
    """审批步骤执行记录 - 运行时实例"""
    __tablename__ = "approval_steps"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, ForeignKey("approval_instances.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("approval_step_templates.id"))
    step_order = Column(Integer, nullable=False)
    step_status = Column(String(20), default="pending")  # pending/approved/rejected/returned
    assignee_id = Column(BigInteger, ForeignKey("users.id"))  # 具体审批人
    opinion = Column(Text)  # 审批意见
    attached_files = Column(JSON, default=list)  # 审批时附加的文件
    completed_at = Column(DateTime)
    timeout_at = Column(DateTime)  # 预计超时时间
    
    instance = relationship("ApprovalInstance", back_populates="steps")


class ParallelReviewGroup(Base):
    """平行审核组 - M11专用"""
    __tablename__ = "parallel_review_groups"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, ForeignKey("approval_instances.id"), unique=True, nullable=False)
    group_status = Column(String(20), default="collecting")  # collecting/reviewed/revised
    reviewer_ids = Column(JSON, default=list)  # 参与平行审核的用户ID列表
    all_approved = Column(Boolean, default=False)  # 是否全部通过
    revision_count = Column(Integer, default=0)  # 修订次数
    max_revisions = Column(Integer, default=10)  # 最大修订次数保护


class BusinessForm(Base):
    """业务表单 - 通用"""
    __tablename__ = "business_forms"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False, index=True)
    node_type = Column(String(20), nullable=False, index=True)  # M2/M4/M6...
    form_data = Column(JSON, nullable=False)  # 表单字段数据
    attachments = Column(JSON, default=list)  # 附件列表
    template_type = Column(String(20))  # docx/xls/standard/online
    template_id = Column(Integer, ForeignKey("templates.id"))
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # draft/submitted/approved/rejected
    created_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="forms")


class Template(Base):
    """模板管理（DOCX/XLS模板）"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(20), nullable=False, index=True)
    template_type = Column(String(20), nullable=False)  # docx/xls/standard
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    version = Column(String(20), default="v1")
    is_active = Column(Boolean, default=True)
    fields_schema = Column(JSON)  # 模板字段定义(用于在线编辑)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectDocument(Base):
    """项目资料库 - M21 + 全流程附件统一归档"""
    __tablename__ = "project_documents"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False, index=True)
    category = Column(String(50))  # 合同/招投/施组/签证/变更等
    subcategory = Column(String(50))
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    file_type = Column(String(20))  # pdf/jpg/png/docx/xls
    uploaded_by = Column(BigInteger, ForeignKey("users.id"))
    related_node = Column(String(20))  # 来源节点(M6/M8等)
    related_form_id = Column(BigInteger, ForeignKey("business_forms.id"))
    auto_categorized = Column(Boolean, default=False)  # 是否M21自动分类
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="documents")


class ConstructionContract(Base):
    """建造合同3张表关联 - M24数据枢纽"""
    __tablename__ = "construction_contracts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)  # 年月如"2026-07"
    
    # 表1: 预计总收入调整
    original_contract_amount = Column(DECIMAL(18, 2))
    visa_amount = Column(DECIMAL(18, 2))  # M8签证累计
    claim_amount = Column(DECIMAL(18, 2))  # M9索赔累计
    change_amount = Column(DECIMAL(18, 2))  # M10变更累计
    total_revenue = Column(DECIMAL(18, 2))  # 表1合计
    
    # 表2: 总成本动态调整
    verified_amount = Column(DECIMAL(18, 2))  # M11验工累计
    consumption_amount = Column(DECIMAL(18, 2))  # M13消耗量累计
    material_settlement = Column(DECIMAL(18, 2))  # M12材料结算累计
    total_cost = Column(DECIMAL(18, 2))  # 表2合计
    
    # 表3: 总成本调整汇总
    cost_adjustment_summary = Column(DECIMAL(18, 2))
    
    # 利润分析
    profit_amount = Column(DECIMAL(18, 2))
    profit_ratio = Column(DECIMAL(5, 2))
    retention_target = Column(DECIMAL(5, 2))  # M1基线留存目标
    
    # 超概标识
    over_budget = Column(Boolean, default=False)
    over_budget_explanation = Column(Text)  # T6超概说明
    over_budget_deadline = Column(DateTime)
    over_budget_escalated = Column(Boolean, default=False)
    
    reviewed_by = Column(BigInteger, ForeignKey("users.id"))  # 造价部复核人
    reviewed_at = Column(DateTime)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="contracts")
    
    __table_args__ = (
        Index("ix_project_month", "project_id", "month", unique=True),
    )


class Alert(Base):
    """预警记录"""
    __tablename__ = "alerts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False, index=True)
    node_type = Column(String(20))  # 触发节点
    alert_type = Column(String(50), nullable=False)  # timeout/over_budget/over_contract/retention_due
    severity = Column(String(20), default="warning")  # info/warning/critical
    related_id = Column(BigInteger)  # 关联的实例/表单ID
    message = Column(Text, nullable=False)
    escalated = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(BigInteger, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="alerts")


class AlertRule(Base):
    """预警规则配置"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), unique=True, nullable=False)
    trigger_condition = Column(JSON, nullable=False)  # 触发条件的JSON表达
    notify_sequence = Column(JSON)  # 逐级通知的人员/部门序列
    escalation_interval_hours = Column(Integer)  # 升级间隔(小时)
    is_active = Column(Boolean, default=True)
