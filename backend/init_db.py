"""
测试初始化脚本 - 创建数据库表 + 初始化默认数据
运行: python init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, Base, SessionLocal
from app.models import Department, User, Template, AlertRule
from app.core.security import hash_password


def init_db():
    """初始化数据库"""
    print("📦 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    db = SessionLocal()
    try:
        # 初始化8部门
        departments = [
            "项目部", "工程部", "造价部", "采供部",
            "合同部", "财务部", "公司领导", "资料室"
        ]
        for name in departments:
            if not db.query(Department).filter(Department.name == name).first():
                db.add(Department(name=name))
                print(f"  ✅ 部门: {name}")
        db.commit()
        
        # 初始化管理员用户
        admin_dept = db.query(Department).filter(Department.name == "公司领导").first()
        if admin_dept:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    real_name="系统管理员",
                    department_id=admin_dept.id,
                    role="总经理",
                    password_hash=hash_password("admin123"),
                    is_active=True,
                )
                db.add(admin)
                print("  ✅ 管理员账户: admin / admin123")
            db.commit()
        
        # 初始化测试用户
        test_users = [
            ("zhangsan", "张三", "项目部", "项目经理", "project123"),
            ("lisi", "李四", "工程部", "工程管理员", "project123"),
            ("wangwu", "王五", "造价部", "造价工程师", "project123"),
            ("zhaoliu", "赵六", "采供部", "采购人员", "project123"),
            ("sunqi", "孙七", "合同部", "合同管理员", "project123"),
            ("zhouba", "周八", "财务部", "财务主管", "project123"),
            ("wengjiu", "吴九", "项目部", "施工员", "project123"),
            ("zhengshi", "郑十", "项目部", "总工", "project123"),
        ]
        
        for username, real_name, dept_name, role, pwd in test_users:
            if not db.query(User).filter(User.username == username).first():
                dept = db.query(Department).filter(Department.name == dept_name).first()
                if dept:
                    user = User(
                        username=username,
                        real_name=real_name,
                        department_id=dept.id,
                        role=role,
                        password_hash=hash_password(pwd),
                        is_active=True,
                    )
                    db.add(user)
                    print(f"  ✅ 用户: {username} ({real_name}) - {dept_name}/{role}")
        
        db.commit()
        
        # 初始化预警规则
        init_alert_rules(db)
        
        print("\n🎉 数据库初始化完成！")
        print("\n📋 登录信息:")
        print("   管理员: admin / admin123")
        print("   测试用户:")
        for u in test_users:
            print(f"     {u[0]} / {u[4]}")
        
    finally:
        db.close()


def init_alert_rules(db):
    """初始化预警规则"""
    rules = [
        ("timeout", {"type": "step_timeout"}, [{"level": 1, "role": "项目经理"}, {"level": 2, "role": "分管领导"}], 24),
        ("over_budget", {"type": "contract_over_100pct"}, [{"level": 1, "role": "造价部"}, {"level": 2, "role": "经营副总"}], 72),
        ("retention_due", {"type": "payment_reminder", "days_before": [7, 3, 1]}, [{"level": 1, "role": "责任人"}], 0),
        ("claim_timeout", {"type": "dual_28day", "warning_days": [5, 3, 1]}, [{"level": 1, "role": "项目经理"}, {"level": 2, "role": "总经理"}], 0),
    ]
    
    for alert_type, condition, sequence, interval in rules:
        if not db.query(AlertRule).filter(AlertRule.alert_type == alert_type).first():
            db.add(AlertRule(
                alert_type=alert_type,
                trigger_condition=condition,
                notify_sequence=sequence,
                escalation_interval_hours=interval,
            ))
            print(f"  ✅ 预警规则: {alert_type}")


if __name__ == "__main__":
    init_db()
