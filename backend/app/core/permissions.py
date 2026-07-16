"""
RBAC权限系统 - 8部门×角色矩阵
支持: 数据隔离(项目级) + 节点级权限 + 字段级权限
"""
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Department, ProjectMember
from app.models import ApprovalStepTemplate


class PermissionChecker:
    """权限检查器"""
    
    # 8部门角色定义
    DEPARTMENT_ROLES = {
        "项目部": ["项目经理", "施工员", "生产经理", "质量员", "安全员", "材料员"],
        "工程部": ["工程管理员", "生产副总"],
        "造价部": ["造价员", "造价工程师"],
        "采供部": ["采购人员", "供应商管理员"],
        "合同部": ["合同管理员"],
        "财务部": ["财务人员", "财务主管"],
        "公司领导": ["经营副总", "生产副总", "总经理"],
        "资料室": ["合同资料员", "资料管理员"],
    }
    
    # 节点级权限矩阵: node_type -> required_department
    NODE_PERMISSIONS = {
        "M1": ["项目部"],       # 基线录入
        "M2": ["项目部"],       # 任务分解
        "M3": ["项目部"],       # 策划编制
        "M4": ["项目部", "工程部", "造价部", "公司领导"],  # 策划审核
        "M5": ["项目部"],       # 回款落实
        "M6": ["项目部", "采供部", "造价部", "公司领导"],  # 认质认价
        "M7": ["项目部", "造价部"],  # 联系单
        "M8": ["项目部", "工程部", "造价部", "公司领导"],  # 签证执行
        "M9": ["项目部", "工程部", "造价部", "公司领导"],  # 索赔执行
        "M10": ["项目部", "采供部", "造价部"],  # 设计变更
        "M11": ["项目部", "合同部", "造价部", "公司领导", "财务部"],  # 月验工计价
        "M12": ["采供部", "合同部", "造价部", "公司领导", "财务部"],  # 材料结算
        "M13": ["项目部", "采供部", "财务部", "造价部"],  # 消耗核定
        "M14-M23": ["项目部", "工程部", "造价部", "采供部", "合同部", "财务部", "公司领导", "资料室"],  # 月度检查
        "M24": ["造价部"],      # 建造合同
        "M25": ["项目部", "公司领导"],  # 月度复盘
    }
    
    # 铁律约束节点: constraint_code -> required_department
    CONSTRAINT_DEPARTMENTS = {
        "T1": ["公司领导"],     # 总经理终审
        "T2": ["造价部"],       # 造价部强制前置
        "T3": ["公司领导"],     # 法代联签
        "T5": ["公司领导"],     # 经营副总牵头
        "T6": ["造价部"],       # 超概说明
    }
    
    @classmethod
    def check_user_in_project(cls, db: Session, user: User, project_id: int) -> bool:
        """检查用户是否属于指定项目"""
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        ).first()
        return member is not None
    
    @classmethod
    def check_department_access(cls, user: User, required_departments: List[str]) -> bool:
        """检查用户部门是否在允许列表中"""
        if not user.department:
            return False
        return user.department.name in required_departments
    
    @classmethod
    def check_node_permission(cls, user: User, node_type: str, project_id: int, db: Session) -> bool:
        """
        综合权限检查: 项目成员 + 部门权限
        """
        # 1. 检查是否是项目成员
        if not cls.check_user_in_project(db, user, project_id):
            return False
        
        # 2. 获取该节点的允许部门
        dept_list = cls.NODE_PERMISSIONS.get(node_type, [])
        if not dept_list:
            return False
        
        # 3. 检查用户部门是否在允许列表中
        return cls.check_department_access(user, dept_list)
    
    @classmethod
    def check_constraint_permission(cls, user: User, constraint_code: str, project_id: int, db: Session) -> bool:
        """检查铁律约束节点权限"""
        required_depts = cls.CONSTRAINT_DEPARTMENTS.get(constraint_code, [])
        if not required_depts:
            return True
        
        return cls.check_department_access(user, required_depts)
    
    @classmethod
    def get_user_accessible_nodes(cls, user: User, project_id: int, db: Session) -> List[str]:
        """获取用户可访问的所有节点类型"""
        accessible = []
        for node_type, depts in cls.NODE_PERMISSIONS.items():
            if cls.check_department_access(user, depts):
                accessible.append(node_type)
        return accessible
    
    @classmethod
    def get_user_pending_count(cls, db: Session, user: User) -> int:
        """获取用户待办数量"""
        from app.models import ApprovalStep
        count = db.query(ApprovalStep).filter(
            ApprovalStep.assignee_id == user.id,
            ApprovalStep.step_status == "pending"
        ).count()
        return count


def require_permission(required_departments: Optional[List[str]] = None, required_roles: Optional[List[str]] = None):
    """
    权限装饰器
    usage: @require_permission(required_departments=["造价部"])
           @require_permission(required_roles=["项目经理"])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.core.database import get_db
            from app.core.security import get_current_user
            
            db = next(get_db())
            user = get_current_user()
            
            if required_departments and user.department_name not in required_departments:
                raise HTTPException(status_code=403, detail=f"需要{required_departments}部门权限")
            
            if required_roles and user.role not in required_roles:
                raise HTTPException(status_code=403, detail=f"需要{required_roles}角色权限")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_project_member(project_id: int):
    """要求用户是项目成员"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.core.database import get_db
            from app.core.security import get_current_user
            
            db = next(get_db())
            user = get_current_user()
            
            checker = PermissionChecker()
            if not checker.check_user_in_project(db, user, project_id):
                raise HTTPException(status_code=403, detail="无权访问此项目")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
