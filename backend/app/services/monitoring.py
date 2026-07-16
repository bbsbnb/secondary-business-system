"""
定时任务 - 超时监控 + 到期提醒
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import ApprovalStep, Alert, ConstructionContract, AlertRule
from app.services.feishu import FeishuService, FeishuWebhookService


async def monitor_timeouts():
    """
    监控所有审批节点超时
    每分钟执行一次
    """
    db = SessionLocal()
    try:
        # 查找超时的审批步骤
        overdue_steps = db.query(ApprovalStep).filter(
            ApprovalStep.step_status == "pending",
            ApprovalStep.timeout_at < datetime.utcnow(),
        ).all()
        
        for step in overdue_steps:
            # 检查是否已创建超时预警
            existing = db.query(Alert).filter(
                Alert.related_id == step.id,
                Alert.alert_type == "timeout",
                Alert.resolved == False,
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
                
                # 发送飞书通知
                # TODO: 获取审批人飞书ID并发送
                # await FeishuService.send_escalation(
                #     user_id=step.assignee.feishu_user_id,
                #     title=f"{step.instance.node_type} 审批超时",
                #     escalation_level=1,
                # )
        
        db.commit()
    finally:
        db.close()


async def check_retention_due():
    """
    检查回款到期提醒(M5)
    T-7/T-3/T-1天倒推提醒
    """
    pass


async def check_over_budget():
    """
    检查超概预警(M11/M24)
    累计达100%触发T6
    """
    db = SessionLocal()
    try:
        over_budget_cases = db.query(ConstructionContract).filter(
            ConstructionContract.over_budget == True,
            ConstructionContract.over_budget_explanation == None,
            ConstructionContract.over_budget_deadline < datetime.utcnow() - timedelta(days=3),
            ConstructionContract.over_budget_escalated == False,
        ).all()
        
        for case in over_budget_cases:
            case.over_budget_escalated = True
            alert = Alert(
                project_id=case.project_id,
                node_type="M24",
                alert_type="over_budget",
                severity="critical",
                related_id=case.id,
                message=f"超概预警: 建造合同{case.month}超概且3日内未提交说明",
            )
            db.add(alert)
        
        db.commit()
    finally:
        db.close()


async def run_all_monitoring():
    """运行所有监控任务"""
    while True:
        try:
            await monitor_timeouts()
            await check_over_budget()
        except Exception as e:
            print(f"❌ 监控任务异常: {e}")
        
        await asyncio.sleep(60)  # 每分钟执行
