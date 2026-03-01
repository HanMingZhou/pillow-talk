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
    
    async def process_image_streaming(
        self,
        messages: list
    ) -> AsyncIterator[str]:
        """流式处理（用于路由直接调用）"""
        async for chunk in self._stream_response(messages):
            yield chunk
    
    def _build_doubao_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建豆包格式的消息
        
        豆包使用标准的 OpenAI 格式：
        - type: "image_url" 或 "text"
        - image_url: {"url": "data:image/jpeg;base64,..."}
        - text: 文本内容
        """
        messages = []
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role != "system":
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # 添加当前请求（图像 + 提示词）
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            },
            {
                "type": "text",
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
            import asyncio
            
            def _sync_call():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    thinking={"type": "disabled"}  # 禁用深度思考模式
                )
                return response
            
            response = await asyncio.to_thread(_sync_call)
            
            # 标准 OpenAI 格式响应
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            
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
        """流式响应处理"""
        try:
            import asyncio
            
            def _sync_stream():
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    thinking={"type": "disabled"}  # 禁用深度思考模式
                )
                return completion
            
            completion = await asyncio.to_thread(_sync_stream)
            
            # 使用 with 确保连接自动关闭，防止连接泄漏
            with completion:
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Doubao API request timed out")
            elif "connect" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Doubao API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Doubao API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            import asyncio
            
            def _sync_test():
                test_messages = [{
                    "role": "user",
                    "content": "Hello"
                }]
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=test_messages
                )
                return response is not None
            
            return await asyncio.to_thread(_sync_test)
            
        except Exception:
            return False

    async def close(self):
        """关闭客户端连接"""
        # Ark 客户端不需要显式关闭
        pass
