"""
飞书推送服务 - 消息卡片发送
"""
import httpx
from app.core.config import settings
from datetime import datetime
from typing import Optional


class FeishuService:
    """飞书消息推送服务"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    @classmethod
    async def send_approval_request(cls, user_id: str, title: str, node_type: str, 
                                     instance_url: Optional[str] = None) -> dict:
        """
        发送审批待办通知
        :param user_id: 飞书用户ID
        :param title: 标题
        :param node_type: 节点类型(M7/M8等)
        :param instance_url: 审批链接
        """
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📋 审批待办: {title}"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**节点:** {node_type}\n**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "查看详情"
                                },
                                "type": "primary",
                                "url": instance_url or "#",
                            }
                        ]
                    }
                ]
            }
        }
        
        return await cls._send_to_user(user_id, message)
    
    @classmethod
    async def send_reminder(cls, user_id: str, title: str, days_left: int) -> dict:
        """
        发送到期提醒
        """
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⏰ 到期提醒: {title}"
                    },
                    "template": "warning"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**剩余天数:** {days_left}天\n**请及时处理**"
                        }
                    }
                ]
            }
        }
        
        return await cls._send_to_user(user_id, message)
    
    @classmethod
    async def send_escalation(cls, user_id: str, title: str, escalation_level: int) -> dict:
        """
        发送升级通知
        """
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 超时升级: {title}"
                    },
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**升级层级:** L{escalation_level}\n**请优先处理**"
                        }
                    }
                ]
            }
        }
        
        return await cls._send_to_user(user_id, message)
    
    @classmethod
    async def send_alert(cls, user_id: str, alert_type: str, message: str) -> dict:
        """
        发送预警通知
        """
        template_color = {
            "timeout": "red",
            "over_budget": "red",
            "retention_due": "orange",
            "claim_timeout": "red",
        }.get(alert_type, "blue")
        
        card_message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⚠️ 预警通知: {alert_type}"
                    },
                    "template": template_color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": message
                        }
                    }
                ]
            }
        }
        
        return await cls._send_to_user(user_id, card_message)
    
    @classmethod
    async def _send_to_user(cls, user_id: str, message: dict) -> dict:
        """
        发送消息到飞书用户
        """
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{cls.BASE_URL}/im/v1/messages",
                headers={
                    "Authorization": f"Bearer {await cls._get_tenant_access_token()}",
                    "Content-Type": "application/json",
                },
                json={
                    "receive_id": user_id,
                    **message,
                }
            )
            return response.json()
    
    @classmethod
    async def _get_tenant_access_token(cls) -> str:
        """
        获取租户tenant_access_token
        实际实现需要调用飞书API获取token
        """
        # TODO: 实现token获取逻辑
        if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
            print("⚠️ 飞书配置未设置，跳过推送")
            return ""
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{cls.BASE_URL}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": settings.FEISHU_APP_ID,
                    "app_secret": settings.FEISHU_APP_SECRET,
                }
            )
            data = response.json()
            return data.get("tenant_access_token", "")


# Webhook方式（简化版）
class FeishuWebhookService:
    """飞书Webhook机器人（简单消息推送）"""
    
    @classmethod
    async def send(cls, webhook_url: str, text: str) -> bool:
        """
        通过Webhook发送简单文本消息
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    webhook_url,
                    json={
                        "msg_type": "text",
                        "content": {"text": text},
                    }
                )
                return response.status_code == 200
        except Exception as e:
            print(f"❌ 飞书Webhook推送失败: {e}")
            return False
