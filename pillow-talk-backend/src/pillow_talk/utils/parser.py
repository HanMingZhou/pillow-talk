"""解析器和格式化器模块

提供配置文件解析和数据格式化功能
"""
import json
from typing import Any, Dict
from .exceptions import PillowTalkException


class Parser:
    """解析器类
    
    提供多种格式的解析功能
    """
    
    @staticmethod
    def parse_json(content: str) -> Dict[str, Any]:
        """解析 JSON 数据
        
        Args:
            content: JSON 字符串
            
        Returns:
            解析后的字典
            
        Raises:
            ValueError: JSON 格式无效时
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format at line {e.lineno}, column {e.colno}: {e.msg}")
    
    @staticmethod
    def parse_env(content: str) -> Dict[str, str]:
        """解析 .env 文件
        
        Args:
            content: .env 文件内容
            
        Returns:
            环境变量字典
        """
        env_vars: Dict[str, str] = {}
        
        for line_num, line in enumerate(content.strip().split("\n"), 1):
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            
            # 解析键值对
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
            else:
                raise ValueError(f"Invalid .env format at line {line_num}: missing '='")
        
        return env_vars
    
    @staticmethod
    def extract_text_from_model_response(response: Dict[str, Any], provider: str) -> str:
        """从模型响应中提取文本内容
        
        Args:
            response: 模型 API 响应
            provider: 模型提供商
            
        Returns:
            提取的文本内容
            
        Raises:
            ValueError: 响应格式无效时
        """
        try:
            if provider == "openai":
                return response["choices"][0]["message"]["content"]
            elif provider == "gemini":
                return response["candidates"][0]["content"]["parts"][0]["text"]
            elif provider == "claude":
                return response["content"][0]["text"]
            elif provider == "doubao":
                return response["choices"][0]["message"]["content"]
            else:
                # 自定义模型，尝试通用格式
                if "choices" in response:
                    return response["choices"][0]["message"]["content"]
                elif "text" in response:
                    return response["text"]
                else:
                    raise ValueError(f"Unknown response format for provider: {provider}")
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Failed to extract text from response: {e}")


class PrettyPrinter:
    """格式化输出器类
    
    提供数据格式化功能
    """
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """格式化 JSON 数据
        
        Args:
            data: 要格式化的数据
            indent: 缩进空格数
            
        Returns:
            格式化后的 JSON 字符串
        """
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def format_error(error: Exception) -> Dict[str, Any]:
        """格式化错误信息
        
        Args:
            error: 异常对象
            
        Returns:
            格式化后的错误信息字典
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 如果是自定义异常，提取建议
        if isinstance(error, PillowTalkException):
            suggestion = error.suggestion
            error_code = error.error_code
        else:
            suggestion = get_error_suggestion(error)
            error_code = 1000
        
        return {
            "error_type": error_type,
            "error_code": error_code,
            "error_message": error_message,
            "suggestion": suggestion
        }


def get_error_suggestion(error: Exception) -> str:
    """根据错误类型返回建议
    
    Args:
        error: 异常对象
        
    Returns:
        解决建议
    """
    error_type = type(error).__name__
    
    suggestions = {
        "ConnectionError": "请检查网络连接",
        "TimeoutError": "请求超时，请稍后重试",
        "ValueError": "请检查输入参数是否正确",
        "KeyError": "缺少必需的字段",
        "TypeError": "数据类型不匹配",
        "FileNotFoundError": "文件不存在",
        "PermissionError": "权限不足",
    }
    
    return suggestions.get(error_type, "请联系技术支持")
