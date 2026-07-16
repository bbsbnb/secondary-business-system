"""
审批引擎核心服务 - 六层引擎实现
支持: 串行/并行/条件分支/退回重提
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import (
    ApprovalInstance, ApprovalStep, ApprovalStepTemplate,
    ParallelReviewGroup, BusinessForm, User, Project, Alert, Department
)


class ApprovalEngine:
    """审批流引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 1. 流程定义层 ====================
    
    def get_node_template(self, node_type: str) -> List[ApprovalStepTemplate]:
        """获取某节点类型的审批步骤模板定义"""
        templates = self.db.query(ApprovalStepTemplate).filter(
            ApprovalStepTemplate.node_type == node_type
        ).order_by(ApprovalStepTemplate.step_order).all()
        return templates
    
    def register_node_template(self, node_type: str, steps: list):
        """
        注册节点审批模板
        steps格式: [{"step_order": 1, "department_id": 1, "role": "项目经理", 
                      "is_mandatory": False, "constraint_code": None, 
                      "is_parallel": False, "timeout_days": 3}]
        """
        # 先删除旧模板
        self.db.query(ApprovalStepTemplate).filter(
            ApprovalStepTemplate.node_type == node_type
        ).delete()
        
        for step in steps:
            t = ApprovalStepTemplate(
                node_type=node_type,
                **step
            )
            self.db.add(t)
        self.db.commit()
    
    # ==================== 2. 节点执行层 ====================
    
    def create_instance(self, node_type: str, business_form_id: int, 
                        initiator_id: int, project_id: int) -> ApprovalInstance:
        """创建审批实例"""
        instance = ApprovalInstance(
            project_id=project_id,
            node_type=node_type,
            business_form_id=business_form_id,
            initiator_id=initiator_id,
            status="active",
            current_step=0,
        )
        self.db.add(instance)
        self.db.flush()
        
        # 加载模板，生成步骤
        templates = self.get_node_template(node_type)
        for tmpl in templates:
            step = ApprovalStep(
                instance_id=instance.id,
                template_id=tmpl.id,
                step_order=tmpl.step_order,
                timeout_at=datetime.utcnow() + timedelta(days=tmpl.timeout_days or 3),
            )
            self.db.add(step)
        
        # 如果是平行审核，创建审核组
        parallel_tmpl = [t for t in templates if t.is_parallel]
        if parallel_tmpl:
            group = ParallelReviewGroup(instance_id=instance.id)
            self.db.add(group)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def advance_to_next_step(self, instance: ApprovalInstance):
        """推进到下一个待处理步骤"""
        pending_steps = self.db.query(ApprovalStep).filter(
            ApprovalStep.instance_id == instance.id,
            ApprovalStep.step_status == "pending"
        ).order_by(ApprovalStep.step_order).all()
        
        if not pending_steps:
            # 所有步骤完成
            instance.status = "completed"
            instance.completed_at = datetime.utcnow()
            self.db.commit()
            return
        
        # 检查是否为平行审核组
        first_pending = pending_steps[0]
        tmpl = self.db.query(ApprovalStepTemplate).filter(
            ApprovalStepTemplate.id == first_pending.template_id
        ).first()
        
        if tmpl and tmpl.is_parallel:
            # 平行审核：收集所有parallel reviewer的待办
            self._assign_parallel_reviewers(instance, pending_steps)
        else:
            # 串行：分配给第一个pending步骤的审批人
            self._assign_step_approver(first_pending, tmpl)
        
        self.db.commit()
    
    def _assign_parallel_reviewers(self, instance: ApprovalInstance, pending_steps: List[ApprovalStep]):
        """分配平行审核人员"""
        group = self.db.query(ParallelReviewGroup).filter(
            ParallelReviewGroup.instance_id == instance.id
        ).first()
        
        reviewer_ids = []
        for step in pending_steps:
            tmpl = self.db.query(ApprovalStepTemplate).filter(
                ApprovalStepTemplate.id == step.template_id
            ).first()
            if tmpl:
                # 按部门+角色查找用户
                users = self.db.query(User).filter(
                    User.department_id == tmpl.department_id,
                    User.role == tmpl.role,
                    User.is_active == True
                ).all()
                for u in users:
                    step.assignee_id = u.id
                    reviewer_ids.append(u.id)
        
        if group:
            group.reviewer_ids = list(set(reviewer_ids))
            group.group_status = "collecting"
    
    def _assign_step_approver(self, step: ApprovalStep, tmpl: ApprovalStepTemplate):
        """分配单个审批步骤给具体人员"""
        if tmpl and tmpl.department_id:
            user = self.db.query(User).filter(
                User.department_id == tmpl.department_id,
                User.role == tmpl.role,
                User.is_active == True
            ).first()
            if user:
                step.assignee_id = user.id
    
    # ==================== 3. 权限校验层 ====================
    
    def can_approve(self, step: ApprovalStep, user_id: int) -> bool:
        """检查用户是否有权审批此步骤"""
        return step.assignee_id == user_id and step.step_status == "pending"
    
    # ==================== 4. 数据校验层 ====================
    
    def validate_step_completion(self, instance: ApprovalInstance) -> dict:
        """
        校验步骤完成情况
        返回: {"all_passed": bool, "opinions": list, "rejected_count": int}
        """
        steps = self.db.query(ApprovalStep).filter(
            ApprovalStep.instance_id == instance.id
        ).all()
        
        opinions = []
        rejected_count = 0
        
        for s in steps:
            if s.step_status == "approved":
                opinions.append({
                    "step_order": s.step_order,
                    "status": "approved",
                    "opinion": s.opinion,
                })
            elif s.step_status == "rejected":
                opinions.append({
                    "step_order": s.step_order,
                    "status": "rejected",
                    "opinion": s.opinion,
                })
                rejected_count += 1
        
        all_approved = all(s.step_status == "approved" for s in steps)
        
        return {
            "all_passed": all_approved,
            "opinions": opinions,
            "rejected_count": rejected_count,
        }
    
    # ==================== 5. 通知触发层 ====================
    
    def check_timeout(self, step: ApprovalStep) -> bool:
        """检查步骤是否超时"""
        if step.timeout_at and datetime.utcnow() > step.timeout_at:
            return True
        return False
    
    def create_timeout_alert(self, step: ApprovalStep, instance: ApprovalInstance):
        """创建超时预警"""
        alert = Alert(
            project_id=instance.project_id,
            node_type=instance.node_type,
            alert_type="timeout",
            severity="critical",
            related_id=step.id,
            message=f"审批步骤超时: {instance.node_type} 第{step.step_order}步已超时",
        )
        self.db.add(alert)
        self.db.commit()
    
    # ==================== 6. 审计追踪层 ====================
    
    def record_action(self, step: ApprovalStep, user_id: int, decision: str, opinion: str):
        """记录操作日志（审计追踪）"""
        step.step_status = "approved" if decision == "approve" else "rejected"
        step.opinion = opinion
        step.completed_at = datetime.utcnow()
        
        # 触发下一步或退回
        if decision == "approve":
            self._handle_approval_success(step)
        else:
            self._handle_rejection(step)
    
    def _handle_approval_success(self, step: ApprovalStep):
        """处理审批通过 - 推进到下一步"""
        instance = step.instance
        
        # 检查是否还有pending步骤
        remaining = self.db.query(ApprovalStep).filter(
            ApprovalStep.instance_id == instance.id,
            ApprovalStep.step_status == "pending"
        ).count()
        
        if remaining == 0:
            # 全部完成
            instance.status = "completed"
            instance.completed_at = datetime.utcnow()
        else:
            # 推进到下一个
            next_step = self.db.query(ApprovalStep).filter(
                ApprovalStep.instance_id == instance.id,
                ApprovalStep.step_status == "pending"
            ).order_by(ApprovalStep.step_order).first()
            
            if next_step:
                tmpl = self.db.query(ApprovalStepTemplate).filter(
                    ApprovalStepTemplate.id == next_step.template_id
                ).first()
                
                # 处理条件分支
                if tmpl and tmpl.branch_condition:
                    self._handle_branch(next_step, instance, tmpl.branch_condition)
                else:
                    self._assign_step_approver(next_step, tmpl)
    
    def _handle_rejection(self, step: ApprovalStep):
        """处理审批拒绝 - 打回发起人"""
        instance = step.instance
        instance.status = "returned"
        
        # 版本+1
        instance.version += 1
        instance.current_step = 0
        
        # 重置所有步骤为pending
        self.db.query(ApprovalStep).filter(
            ApprovalStep.instance_id == instance.id
        ).update({"step_status": "pending"})
        
        # 清除审批意见和assignee
        self.db.query(ApprovalStep).filter(
            ApprovalStep.instance_id == instance.id
        ).update({
            "opinion": None,
            "assignee_id": None,
            "completed_at": None,
        })
    
    def _handle_branch(self, step: ApprovalStep, instance: ApprovalInstance, condition: dict):
        """处理条件分支"""
        # 从business_form中读取金额等判断数据
        form = self.db.query(BusinessForm).filter(
            BusinessForm.id == instance.business_form_id
        ).first()
        
        if not form or not form.form_data:
            return
        
        amount = form.form_data.get("amount", 0)
        branch_type = condition.get("type", "amount")
        
        if branch_type == "amount":
            thresholds = condition.get("thresholds", {})
            if amount <= thresholds.get("low", 10000):
                step.step_order = thresholds.get("low_route", step.step_order + 1)
            elif amount <= thresholds.get("medium", 100000):
                step.step_order = thresholds.get("medium_route", step.step_order + 1)
            elif amount <= thresholds.get("high", 500000):
                step.step_order = thresholds.get("high_route", step.step_order + 1)
            else:
                step.step_order = thresholds.get("max_route", step.step_order + 1)
    
    # ==================== 公共API方法 ====================
    
    def submit_approval(self, step_id: int, user_id: int, decision: str, opinion: str = ""):
        """
        提交审批操作（核心入口）
        step_id: 审批步骤ID
        user_id: 操作人ID
        decision: "approve" 或 "reject"
        opinion: 审批意见
        """
        step = self.db.query(ApprovalStep).filter(ApprovalStep.id == step_id).first()
        if not step:
            raise ValueError("审批步骤不存在")
        
        # 权限校验
        if not self.can_approve(step, user_id):
            raise PermissionError("无权审批此步骤")
        
        # 超时检查
        if self.check_timeout(step):
            self.create_timeout_alert(step, step.instance)
        
        # 记录操作
        self.record_action(step, user_id, decision, opinion)
        
        # 刷新实例
        self.db.refresh(step.instance)
        return step.instance
    
    def get_user_pending_approvals(self, user_id: int) -> List[ApprovalInstance]:
        """获取用户的待办审批列表"""
        steps = self.db.query(ApprovalStep).filter(
            ApprovalStep.assignee_id == user_id,
            ApprovalStep.step_status == "pending"
        ).all()
        
        instance_ids = list(set(s.instance_id for s in steps))
        instances = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.id.in_(instance_ids)
        ).all()
        
        return instances
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List[ApprovalInstance]:
        """获取用户的已办审批历史"""
        steps = self.db.query(ApprovalStep).filter(
            ApprovalStep.assignee_id == user_id,
            ApprovalStep.step_status.in_(["approved", "rejected"])
        ).order_by(ApprovalStep.completed_at.desc()).limit(limit).all()
        
        instance_ids = list(set(s.instance_id for s in steps))
        instances = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.id.in_(instance_ids)
        ).order_by(ApprovalInstance.created_at.desc()).all()
        
        return instances
