"""自定义异常类

定义系统中使用的所有自定义异常
"""


class PillowTalkException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: int = 1000, suggestion: str = ""):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            suggestion: 解决建议
        """
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion or "请联系技术支持"
        super().__init__(self.message)


class ModelConnectionError(PillowTalkException):
    """模型连接错误"""
    
    def __init__(self, message: str = "无法连接到模型服务"):
        super().__init__(
            message=message,
            error_code=2001,
            suggestion="请检查网络连接和 API Key 是否正确"
        )


class ModelTimeoutError(PillowTalkException):
    """模型响应超时错误"""
    
    def __init__(self, message: str = "模型响应超时"):
        super().__init__(
            message=message,
            error_code=2002,
            suggestion="模型响应超时，请稍后重试"
        )


class ModelAPIError(PillowTalkException):
    """模型 API 错误"""
    
    def __init__(self, message: str = "模型 API 返回错误"):
        super().__init__(
            message=message,
            error_code=2003,
            suggestion="模型 API 调用失败，请检查请求参数和配置"
        )


class TTSServiceError(PillowTalkException):
    """TTS 服务错误"""
    
    def __init__(self, message: str = "语音合成服务错误"):
        super().__init__(
            message=message,
            error_code=3001,
            suggestion="语音合成失败，请检查 TTS 服务配置"
        )


class TTSGenerationError(PillowTalkException):
    """TTS 生成错误"""
    
    def __init__(self, message: str = "语音生成失败"):
        super().__init__(
            message=message,
            error_code=3002,
            suggestion="语音生成失败，请检查输入文本和配置"
        )


class TTSProviderUnavailableError(PillowTalkException):
    """TTS 提供商不可用错误"""
    
    def __init__(self, message: str = "TTS 提供商不可用"):
        super().__init__(
            message=message,
            error_code=3003,
            suggestion="TTS 提供商不可用，请检查服务状态"
        )


class RateLimitError(PillowTalkException):
    """限流错误"""
    
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(
            message=message,
            error_code=4001,
            suggestion="请求过于频繁，请稍后再试"
        )


class AuthenticationError(PillowTalkException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            error_code=4002,
            suggestion="认证失败，请检查 API Key 是否正确"
        )


class ImageProcessingError(PillowTalkException):
    """图像处理错误"""
    
    def __init__(self, message: str = "图像处理失败"):
        super().__init__(
            message=message,
            error_code=5001,
            suggestion="图像处理失败，请检查图像格式和大小"
        )


class ConversationNotFoundError(PillowTalkException):
    """对话不存在错误"""
    
    def __init__(self, message: str = "对话不存在"):
        super().__init__(
            message=message,
            error_code=6001,
            suggestion="对话不存在或已过期，请创建新对话"
        )


class ConfigurationError(PillowTalkException):
    """配置错误"""
    
    def __init__(self, message: str = "配置错误"):
        super().__init__(
            message=message,
            error_code=7001,
            suggestion="配置错误，请检查环境变量和配置文件"
        )
