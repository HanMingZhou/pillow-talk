"""日志系统模块

使用 structlog 实现结构化日志记录
"""
import sys
import structlog
from typing import Any


def setup_logger(log_level: str = "INFO", log_format: str = "json") -> structlog.BoundLogger:
    """配置结构化日志系统
    
    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_format: 日志格式（json/text）
        
    Returns:
        配置好的日志记录器
    """
    # 配置处理器
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    # 根据格式选择渲染器
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib, log_level.upper(), structlog.stdlib.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


class RequestLogger:
    """请求日志记录器
    
    提供统一的请求日志记录接口
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        """初始化请求日志记录器
        
        Args:
            logger: structlog 日志记录器实例
        """
        self.logger = logger
    
    def log_request(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        **kwargs: Any
    ) -> None:
        """记录请求信息
        
        Args:
            request_id: 请求 ID
            endpoint: API 端点
            method: HTTP 方法
            **kwargs: 其他上下文信息
        """
        self.logger.info(
            "request_received",
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            **kwargs
        )
    
    def log_response(
        self,
        request_id: str,
        status_code: int,
        latency_ms: int,
        **kwargs: Any
    ) -> None:
        """记录响应信息
        
        Args:
            request_id: 请求 ID
            status_code: HTTP 状态码
            latency_ms: 处理延迟（毫秒）
            **kwargs: 其他上下文信息
        """
        self.logger.info(
            "request_completed",
            request_id=request_id,
            status_code=status_code,
            latency_ms=latency_ms,
            **kwargs
        )
    
    def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        **kwargs: Any
    ) -> None:
        """记录错误信息
        
        Args:
            request_id: 请求 ID
            error_type: 错误类型
            error_message: 错误消息
            **kwargs: 其他上下文信息
        """
        self.logger.error(
            "request_error",
            request_id=request_id,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
    
    def log_model_call(
        self,
        request_id: str,
        provider: str,
        model: str,
        latency_ms: int,
        token_usage: dict[str, int] | None = None,
        **kwargs: Any
    ) -> None:
        """记录模型调用信息
        
        Args:
            request_id: 请求 ID
            provider: 模型提供商
            model: 模型名称
            latency_ms: 调用延迟（毫秒）
            token_usage: Token 使用量
            **kwargs: 其他上下文信息
        """
        self.logger.info(
            "model_call",
            request_id=request_id,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            **kwargs
        )
