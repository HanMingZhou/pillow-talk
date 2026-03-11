"""API 中间件

提供请求日志、异常处理、CORS 和请求追踪中间件。
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import structlog

from ..utils.exceptions import PillowTalkException
from ..utils.parser import PrettyPrinter


logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件
    
    记录所有请求和响应的详细信息。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志
        
        Args:
            request: FastAPI 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        # 获取或生成 request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 记录请求开始
        start_time = time.time()
        
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加自定义响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录请求完成
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time
            )
            
            return response
        
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                process_time=process_time,
                exc_info=True
            )
            
            # 重新抛出异常，让异常处理中间件处理
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件
    
    捕获未处理的异常并返回标准错误响应。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并捕获异常
        
        Args:
            request: FastAPI 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        try:
            return await call_next(request)
        
        except PillowTalkException as e:
            # 处理自定义异常
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            
            error_info = PrettyPrinter.format_error(e)
            
            return JSONResponse(
                status_code=500,
                content={
                    "code": e.error_code,
                    "message": e.message,
                    "error_type": error_info["error_type"],
                    "suggestion": error_info["suggestion"],
                    "request_id": request_id
                }
            )
        
        except Exception as e:
            # 处理未预期的异常
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "code": 1000,
                    "message": "Internal server error",
                    "error_type": type(e).__name__,
                    "suggestion": "请联系技术支持",
                    "request_id": request_id
                }
            )


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件
    
    为每个请求添加唯一的 request_id。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加追踪 ID
        
        Args:
            request: FastAPI 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 响应对象
        """
        # 获取或生成 request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 将 request_id 添加到请求状态中，供后续使用
        request.state.request_id = request_id
        
        # 处理请求
        response = await call_next(request)
        
        # 添加 request_id 到响应头
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_cors_middleware(app, allowed_origins: list[str]) -> None:
    """配置 CORS 中间件
    
    Args:
        app: FastAPI 应用实例
        allowed_origins: 允许的来源列表
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
    
    logger.info(
        "CORS middleware configured",
        allowed_origins=allowed_origins
    )
