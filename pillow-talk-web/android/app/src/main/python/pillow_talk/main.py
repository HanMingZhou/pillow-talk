"""FastAPI 应用主入口

Pillow Talk 后端服务的主应用
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
import structlog

from .config import settings
from .utils.logger import setup_logger
from .api.routes import router
from .api.middleware import (
    RequestLoggingMiddleware,
    ExceptionHandlerMiddleware,
    RequestTrackingMiddleware,
    setup_cors_middleware
)
from .api.dependencies import cleanup_resources

# 初始化日志
logger = setup_logger(settings.log_level, settings.log_format)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时
    logger.info("application_starting", version=settings.app_version)
    
    # 验证配置
    try:
        settings.validate_required_fields()
        logger.info("configuration_validated")
    except ValueError as e:
        logger.error("configuration_error", error=str(e))
        raise
    
    yield
    
    # 关闭时
    logger.info("application_shutting_down")
    await cleanup_resources()
    logger.info("application_stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="多模态智能视觉语音助手后端服务",
    lifespan=lifespan
)

# 配置中间件（顺序很重要）
# 1. CORS 中间件
setup_cors_middleware(app, settings.allowed_origins)

# 2. 请求追踪中间件
app.add_middleware(RequestTrackingMiddleware)

# 3. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 4. 异常处理中间件
app.add_middleware(ExceptionHandlerMiddleware)

# 注册路由
app.include_router(router)

logger.info(
    "application_initialized",
    host=settings.host,
    port=settings.port,
    debug=settings.debug
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pillow_talk.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
