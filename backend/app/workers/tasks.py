"""
Celery异步任务 - 定时监控
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tianxing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 每分钟执行超时监控
    beat_schedule={
        "monitor-timeouts": {
            "task": "app.workers.tasks.monitor_timeouts",
            "schedule": 60.0,  # 每60秒
        },
        "check-retention-due": {
            "task": "app.workers.tasks.check_retention_due",
            "schedule": 3600.0,  # 每小时
        },
        "check-over-budget": {
            "task": "app.workers.tasks.check_over_budget",
            "schedule": 3600.0,  # 每小时
        },
    }
)


@celery_app.task
def monitor_timeouts():
    """监控所有审批节点超时"""
    from app.core.database import SessionLocal
    from app.services.workflow.engine import ApprovalEngine
    from datetime import datetime
    
    db = SessionLocal()
    try:
        from app.models import ApprovalStep, Alert
        
        overdue = db.query(ApprovalStep).filter(
            ApprovalStep.step_status == "pending",
            ApprovalStep.timeout_at < datetime.utcnow()
        ).all()
        
        for step in overdue:
            # 检查是否已经创建过此超时预警
            existing = db.query(Alert).filter(
                Alert.related_id == step.id,
                Alert.alert_type == "timeout",
                Alert.resolved == False
            ).first()
            
            if not existing:
                alert = Alert(
                    project_id=step.instance.project_id,
                    node_type=step.instance.node_type,
                    alert_type="timeout",
                    severity="critical",
                    related_id=step.id,
                    message=f"审批超时: {step.instance.node_type} 第{step.step_order}步",
                )
                db.add(alert)
        
        db.commit()
    finally:
        db.close()


@celery_app.task
def check_retention_due():
    """检查回款到期提醒(M5)"""
    pass


@celery_app.task
def check_over_budget():
    """检查超概预警(M11/M24)"""
    pass
