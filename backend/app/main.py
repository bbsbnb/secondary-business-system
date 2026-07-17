"""
天行建筑智能管理平台 - FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.core.seed import seed_initial_data


def create_application() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    seed_initial_data()

    app = FastAPI(
        title="天行建筑智能管理平台",
        description="建筑施工企业月度经营全流程管理系统",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
