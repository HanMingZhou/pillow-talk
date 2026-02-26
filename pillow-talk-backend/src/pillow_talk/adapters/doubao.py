"""豆包（Doubao）模型适配器

支持字节跳动豆包视觉模型
使用 volcengine-python-sdk[ark] SDK
"""
import json
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError

try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    Ark = None  # type: ignore


class DoubaoAdapter(MultimodalInterface):
    """豆包视觉模型适配器
    
    使用 volcengine-python-sdk[ark] 进行接入
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "doubao-seed-1-6-flash-250828",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        timeout: int = 30
    ):
        """初始化豆包适配器
        
        Args:
            api_key: 豆包 API Key (ARK_API_KEY)
            model: 模型名称
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
            
        Raises:
            ImportError: 如果未安装 volcengine-python-sdk[ark]
        """
        if Ark is None:
            raise ImportError(
                "volcengine-python-sdk[ark] is required for Doubao adapter. "
                "Install it with: pip install volcengine-python-sdk[ark]"
            )
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # 初始化 Ark 客户端
        self.client = Ark(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        豆包 API 使用特殊的消息格式
        """
        messages = self._build_doubao_messages(
            image_base64,
            prompt,
            conversation_history
        )
        
        if stream:
            return self._stream_response(messages)
        else:
            return await self._complete_response(messages)
    
    def _build_doubao_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建豆包格式的消息
        
        豆包使用特殊的消息格式：
        - input_image: 图像 URL 或 base64
        - input_text: 文本内容
        """
        messages = []
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role != "system":
                    messages.append({
                        "role": msg.role,
                        "content": [
                            {
                                "type": "input_text",
                                "text": msg.content
                            }
                        ]
                    })
        
        # 添加当前请求（图像 + 提示词）
        content = [
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{image_base64}"
            },
            {
                "type": "input_text",
                "text": prompt
            }
        ]
        
        messages.append({
            "role": "user",
            "content": content
        })
        
        return messages
    
    async def _complete_response(self, messages: list) -> str:
        """获取完整响应"""
        try:
            # 豆包 SDK 使用同步调用
            # 在实际异步环境中，应该使用 asyncio.to_thread 包装
            import asyncio
            
            def _sync_call():
                response = self.client.responses.create(
                    model=self.model,
                    input=messages
                )
                return response
            
            response = await asyncio.to_thread(_sync_call)
            
            # 解析响应
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                return response.output.text
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ModelAPIError(f"Unexpected response format: {response}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Doubao API request timed out")
            elif "connect" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Doubao API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Doubao API error: {str(e)}")
    
    async def _stream_response(self, messages: list) -> AsyncIterator[str]:
        """流式响应处理
        
        注意：豆包 SDK 的流式支持可能需要特殊处理
        """
        try:
            import asyncio
            
            def _sync_stream():
                stream = self.client.responses.create(
                    model=self.model,
                    input=messages,
                    stream=True
                )
                return stream
            
            stream = await asyncio.to_thread(_sync_stream)
            
            for chunk in stream:
                if hasattr(chunk, 'output') and hasattr(chunk.output, 'text'):
                    if chunk.output.text:
                        yield chunk.output.text
                elif hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Doubao API request timed out")
            elif "connect" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Doubao API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Doubao API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接
        
        发送一个简单的测试请求
        """
        try:
            import asyncio
            
            def _sync_test():
                # 发送一个简单的测试请求
                test_messages = [{
                    "role": "user",
                    "content": [{
                        "type": "input_text",
                        "text": "Hello"
                    }]
                }]
                
                response = self.client.responses.create(
                    model=self.model,
                    input=test_messages
                )
                return response is not None
            
            return await asyncio.to_thread(_sync_test)
            
        except Exception:
            return False
