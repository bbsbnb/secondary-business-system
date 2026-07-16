"""
数据库连接管理 - SQLAlchemy 2.0
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


# 共享 metadata 实例，确保所有模型使用同一个 registry
_shared_metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

Base = declarative_base(metadata=_shared_metadata)


def get_url():
    return getattr(settings, 'DATABASE_URL', 'sqlite:///./tianxing.db')


def get_engine():
    url = get_url()
    kwargs = {}
    if 'sqlite' in url:
        kwargs['connect_args'] = {'check_same_thread': False}
    return create_engine(url, **kwargs)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
