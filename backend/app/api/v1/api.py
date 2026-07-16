"""
API路由入口
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, departments, baseline, forms, approval, templates, documents, alerts, contracts
from app.api.v1.endpoints import m6_price, m7_contact, m8_visa, m9_claim, m10_change, m11_verification, m12_material, m13_consumption, mobile, permissions, dashboard

api_router = APIRouter()

# 认证
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 项目
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])

# 部门
api_router.include_router(departments.router, prefix="/departments", tags=["部门管理"])

# 权限矩阵
api_router.include_router(permissions.router, prefix="/permissions", tags=["权限矩阵"])

# 基线数据(M1)
api_router.include_router(baseline.router, prefix="/baseline", tags=["基线数据"])

# 业务表单
api_router.include_router(forms.router, prefix="/forms", tags=["业务表单"])

# 审批引擎
api_router.include_router(approval.router, prefix="/approval", tags=["审批引擎"])

# M6 认质认价
api_router.include_router(m6_price.router, prefix="/m6/price", tags=["认质认价"])

# M7 工作联系单
api_router.include_router(m7_contact.router, prefix="/m7/contact", tags=["工作联系单"])

# M8 签证执行
api_router.include_router(m8_visa.router, prefix="/m8/visa", tags=["签证执行"])

# M9 索赔执行
api_router.include_router(m9_claim.router, prefix="/m9/claim", tags=["索赔执行"])

# M10 设计变更
api_router.include_router(m10_change.router, prefix="/m10/change", tags=["设计变更"])

# M11 月验工计价
api_router.include_router(m11_verification.router, prefix="/m11/verification", tags=["月验工计价"])

# M12 材料结算
api_router.include_router(m12_material.router, prefix="/m12/material", tags=["材料结算"])

# M13 消耗核定
api_router.include_router(m13_consumption.router, prefix="/m13/consumption", tags=["消耗核定"])

# 模板管理
api_router.include_router(templates.router, prefix="/templates", tags=["模板管理"])

# 资料库
api_router.include_router(documents.router, prefix="/documents", tags=["项目资料库"])

# 预警
api_router.include_router(alerts.router, prefix="/alerts", tags=["预警管理"])

# 建造合同(M24)
api_router.include_router(contracts.router, prefix="/contracts", tags=["建造合同"])

# 移动端
api_router.include_router(mobile.router, prefix="/mobile", tags=["移动端"])

# 总经理驾驶舱
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["总经理驾驶舱"])
