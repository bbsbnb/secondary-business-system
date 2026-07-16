"""验证脚本 - 测试后端框架能否正常启动
用法: cd backend && python verify_backend.py
"""
import os
os.environ['DATABASE_URL'] = 'sqlite:///./tianxing_verify.db'

# Clear any cached SQLAlchemy metadata from previous sandbox imports
import sys
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith('app'):
        del sys.modules[mod_name]

# Now fresh import order matters: models first (registers tables), then create_all
from app.models import (
    Project, User, Department, BaselineData, ApprovalInstance,
    ApprovalStep, ApprovalStepTemplate, ParallelReviewGroup,
    BusinessForm, Template, ProjectDocument, ConstructionContract,
    Alert, AlertRule, ProjectMember
)
ml = [Project, User, Department, BaselineData, ApprovalInstance,
    ApprovalStep, ApprovalStepTemplate, ParallelReviewGroup,
    BusinessForm, Template, ProjectDocument, ConstructionContract,
    Alert, AlertRule, ProjectMember]
print(f"OK: {len(ml)} models loaded")

from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print("OK: Tables created")

from app.schemas.__init__ import (
    LoginRequest, TokenResponse, UserCreate, UserResponse,
    ProjectCreate, ProjectResponse, BaselineCreate, BaselineResponse,
    ApprovalInstanceCreate, ApprovalAction,
    BusinessFormCreate, BusinessFormResponse,
    TemplateCreate, TemplateResponse,
    DocumentCreate, DocumentResponse,
    AlertResponse, ConstructionContractResponse,
)
print("OK: Schemas loaded")

from app.services.workflow.engine import ApprovalEngine
print("OK: Engine loaded")

from app.main import app
title = app.title
version = app.version
print(f"OK: App {title} v{version}")

routes = []
for r in app.routes:
    if hasattr(r, "path") and hasattr(r, "methods"):
        m = ",".join(sorted(r.methods)) if r.methods else "-"
        t = getattr(getattr(r, "route", None), "tags", [])
        routes.append((m, r.path, ", ".join(t)))

print("\nAPI Routes:")
for method, path, tags in sorted(routes):
    print(f"  {method:>8} {path:<50} [{tags}]")
print(f"\nTotal routes: {len(routes)}")

from app.core.database import SessionLocal
from app.core.security import hash_password

db = SessionLocal()
try:
    dept_names = ["项目部", "工程部", "造价部", "采供部", "合同部", "财务部", "公司领导", "资料室"]
    depts = {}
    for name in dept_names:
        existing = db.query(Department).filter(Department.name == name).first()
        if not existing:
            d = Department(name=name)
            db.add(d)
            db.flush()
            depts[name] = d.id
        else:
            depts[name] = existing.id
    db.commit()
    
    admin_dept_id = depts.get("公司领导")
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin", real_name="系统管理员",
            department_id=admin_dept_id, role="总经理",
            password_hash=hash_password("admin123"), is_active=True,
        )
        db.add(admin)
        db.commit()
    
    print(f"\nOK: Test data created: {len(depts)} departments, admin ready")
    print("   Login: admin / admin123")
finally:
    db.close()

print("\nBackend verified successfully!")
print("Start server: cd backend && uvicorn app.main:app --reload")
