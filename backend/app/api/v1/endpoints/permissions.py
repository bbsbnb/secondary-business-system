"""
权限管理API - 部门权限矩阵查询
"""
from fastapi import APIRouter, Depends
from app.core.permissions import PermissionChecker
from app.core.security import get_current_user
from app.models import User
from app.schemas import DepartmentResponse

router = APIRouter()


@router.get("/matrix")
async def get_permission_matrix(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的完整权限矩阵
    返回: 可访问的节点、角色、部门信息
    """
    checker = PermissionChecker()
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "real_name": current_user.real_name,
            "department": current_user.department_name,
            "role": current_user.role,
        },
        "accessible_nodes": checker.get_user_accessible_nodes(
            current_user, 0, None  # project_id not needed for this query
        ),
        "department_roles": PermissionChecker.DEPARTMENT_ROLES,
        "node_permissions": PermissionChecker.NODE_PERMISSIONS,
        "constraint_departments": PermissionChecker.CONSTRAINT_DEPARTMENTS,
    }


@router.get("/departments-roles")
async def list_departments_with_roles():
    """获取8部门及其对应角色"""
    return {
        "departments": [
            {"name": "项目部", "roles": PermissionChecker.DEPARTMENT_ROLES["项目部"]},
            {"name": "工程部", "roles": PermissionChecker.DEPARTMENT_ROLES["工程部"]},
            {"name": "造价部", "roles": PermissionChecker.DEPARTMENT_ROLES["造价部"]},
            {"name": "采供部", "roles": PermissionChecker.DEPARTMENT_ROLES["采供部"]},
            {"name": "合同部", "roles": PermissionChecker.DEPARTMENT_ROLES["合同部"]},
            {"name": "财务部", "roles": PermissionChecker.DEPARTMENT_ROLES["财务部"]},
            {"name": "公司领导", "roles": PermissionChecker.DEPARTMENT_ROLES["公司领导"]},
            {"name": "资料室", "roles": PermissionChecker.DEPARTMENT_ROLES["资料室"]},
        ]
    }


@router.get("/nodes/{node_type}/permissions")
async def get_node_permissions(node_type: str):
    """获取特定节点的权限要求"""
    checker = PermissionChecker()
    
    allowed_depts = PermissionChecker.NODE_PERMISSIONS.get(node_type, [])
    constraints = {}
    
    # 根据节点类型推断铁律约束
    constraint_map = {
        "M4": ["T2", "T5"],
        "M6": ["T2"],
        "M7": ["T2"],
        "M8": ["T1", "T2", "T3"],
        "M9": ["T1", "T2"],
        "M10": ["T2"],
        "M11": ["T1", "T2", "T6"],
        "M12": ["T1", "T2"],
        "M24": ["T6"],
    }
    
    constraints = constraint_map.get(node_type, [])
    
    return {
        "node_type": node_type,
        "allowed_departments": allowed_depts,
        "constraints": constraints,
    }
