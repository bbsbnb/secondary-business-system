from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Department, Project, ProjectMember, User


def seed_initial_data() -> None:
    db = SessionLocal()
    try:
        dept_names = [
            "项目部",
            "工程部",
            "造价部",
            "采购部",
            "合同部",
            "财务部",
            "公司领导",
            "资料室",
        ]
        departments: dict[str, Department] = {}
        for name in dept_names:
            department = db.query(Department).filter(Department.name == name).first()
            if not department:
                department = Department(name=name)
                db.add(department)
                db.flush()
            departments[name] = department

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                real_name="系统管理员",
                department_id=departments["公司领导"].id,
                role="系统管理员",
                password_hash=hash_password("admin123"),
                is_active=True,
            )
            db.add(admin)
            db.flush()

        project = db.query(Project).filter(Project.project_code == "TX-2026-001").first()
        if not project:
            project = Project(
                project_code="TX-2026-001",
                project_name="天行总部综合楼",
                contract_no="HT-2026-001",
                manager_id=admin.id,
                status="active",
            )
            db.add(project)
            db.flush()

        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == admin.id,
        ).first()
        if not membership:
            db.add(ProjectMember(project_id=project.id, user_id=admin.id, project_role="creator"))

        db.commit()
    finally:
        db.close()
