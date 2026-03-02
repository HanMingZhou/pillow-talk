"""模型适配器基类

定义多模态模型的统一接口
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any
from ..models.config import Message


class MultimodalInterface(ABC):
    """多模态模型统一接口
    
    所有模型适配器必须实现此接口
    """
    
    @abstractmethod
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像和文本输入，返回模型响应
        
        Args:
            image_base64: Base64 编码的图像数据
            prompt: 文本提示词
            conversation_history: 对话历史
            stream: 是否使用流式输出
            
        Returns:
            流式输出时返回 AsyncIterator[str]，否则返回完整字符串
            
        Raises:
            ModelConnectionError: 模型连接失败
            ModelTimeoutError: 模型响应超时
            ModelAPIError: 模型 API 错误
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试模型连接是否正常
        
        Returns:
            连接是否成功
        """
        pass
    
    def _build_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, Any]]:
        """构建消息列表（子类可以重写此方法以适配不同格式）
        
        Args:
            image_base64: Base64 编码的图像
            prompt: 提示词
            conversation_history: 对话历史
            
        Returns:
            消息列表
        """
        messages: List[Dict[str, Any]] = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": prompt
        })
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role != "system":  # 跳过系统消息
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # 添加当前图像
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        })
        
        return messages
