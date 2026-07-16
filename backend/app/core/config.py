"""
应用配置中心
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "天行建筑智能管理平台"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # 数据库
    DATABASE_URL: str = "postgresql://Administrator@localhost:5432/tianxing"
    
    # JWT
    SECRET_KEY: str = "tianxing-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小时
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO 对象存储
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "tianxing-uploads"
    
    # 飞书
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_WEBHOOK_URL: str = ""
    
    # 部门列表（8部门）
    DEPARTMENTS: list = [
        "项目部", "工程部", "造价部", "采供部",
        "合同部", "财务部", "公司领导", "资料室"
    ]
    
    # 节点类型列表
    NODE_TYPES: list = [
        "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10",
        "M11", "M12", "M13",
        "M14", "M15", "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23",
        "M24", "M25"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
