"""智谱 GLM 视觉模型适配器

支持智谱 AI GLM-4V 系列视觉模型
使用 zai-sdk
"""
import asyncio
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError

try:
    from zai import ZhipuAiClient
except ImportError:
    ZhipuAiClient = None  # type: ignore


class GLMAdapter(MultimodalInterface):
    """智谱 GLM 视觉模型适配器
    
    使用 zai-sdk 进行接入
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "glm-4.6v-flash",
        timeout: int = 30,
        enable_thinking: bool = False
    ):
        """初始化 GLM 适配器
        
        Args:
            api_key: 智谱 AI API Key
            model: 模型名称（如 glm-4.6v-flash, glm-4v-plus 等）
            timeout: 请求超时时间（秒）
            enable_thinking: 是否启用思考模式
            
        Raises:
            ImportError: 如果未安装 zai-sdk
        """
        if ZhipuAiClient is None:
            raise ImportError(
                "zai-sdk is required for GLM adapter. "
                "Install it with: pip install zai-sdk"
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.enable_thinking = enable_thinking
        
        # 初始化智谱 AI 客户端
        self.client = ZhipuAiClient(api_key=self.api_key)
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        GLM 使用 OpenAI 兼容的消息格式
        """
        messages = self._build_glm_messages(
            image_base64,
            prompt,
            conversation_history
        )
        
        if stream:
            return self._stream_response(messages)
        else:
            return await self._complete_response(messages)
    
    def _build_glm_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建 GLM 格式的消息
        
        GLM 使用类似 OpenAI 的格式
        """
        messages = []
        
        # 添加系统提示（如果有对话历史）
        if conversation_history:
            for msg in conversation_history:
                if msg.role == "system":
                    messages.append({
                        "role": "system",
                        "content": msg.content
                    })
                elif msg.role in ("user", "assistant"):
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
            # GLM SDK 使用同步调用，需要在异步环境中包装
            def _sync_call():
                kwargs = {
                    "model": self.model,
                    "messages": messages
                }
                
                # 如果启用思考模式
                if self.enable_thinking:
                    kwargs["thinking"] = {"type": "enabled"}
                
                response = self.client.chat.completions.create(**kwargs)
                return response
            
            response = await asyncio.to_thread(_sync_call)
            
            # 解析响应
            if hasattr(response, 'choices') and len(response.choices) > 0:
                message = response.choices[0].message
                if hasattr(message, 'content'):
                    return message.content
                else:
                    return str(message)
            else:
                raise ModelAPIError(f"Unexpected response format: {response}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("GLM API request timed out")
            elif "connect" in str(e).lower() or "connection" in str(e).lower():
                raise ModelConnectionError("Failed to connect to GLM API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"GLM API error: {str(e)}")
    
    async def _stream_response(self, messages: list) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            def _sync_stream():
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "stream": True
                }
                
                # 如果启用思考模式
                if self.enable_thinking:
                    kwargs["thinking"] = {"type": "enabled"}
                
                stream = self.client.chat.completions.create(**kwargs)
                return stream
            
            stream = await asyncio.to_thread(_sync_stream)
            
            for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("GLM API request timed out")
            elif "connect" in str(e).lower() or "connection" in str(e).lower():
                raise ModelConnectionError("Failed to connect to GLM API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"GLM API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接
        
        发送一个简单的测试请求
        """
        try:
            def _sync_test():
                # 发送一个简单的测试请求
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
