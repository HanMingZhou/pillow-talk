"""Google Gemini 视觉模型适配器

支持 Google Gemini 多模态模型
使用 google-genai SDK
"""
import base64
import asyncio
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore


class GeminiAdapter(MultimodalInterface):
    """Google Gemini 视觉模型适配器
    
    使用 google-genai SDK 进行接入
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        timeout: int = 30
    ):
        """初始化 Gemini 适配器
        
        Args:
            api_key: Google Gemini API Key
            model: 模型名称（如 gemini-2.0-flash-exp, gemini-1.5-pro 等）
            timeout: 请求超时时间（秒）
            
        Raises:
            ImportError: 如果未安装 google-genai
        """
        if genai is None or types is None:
            raise ImportError(
                "google-genai is required for Gemini adapter. "
                "Install it with: pip install google-genai"
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        
        # 初始化 Gemini 客户端
        self.client = genai.Client(api_key=self.api_key)
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        Gemini 使用特殊的 Part 格式
        """
        contents = self._build_gemini_contents(
            image_base64,
            prompt,
            conversation_history
        )
        
        if stream:
            return self._stream_response(contents)
        else:
            return await self._complete_response(contents)
    
    def _build_gemini_contents(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List:
        """构建 Gemini 格式的内容
        
        Gemini 使用 Part 对象来表示内容
        """
        contents = []
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role == "system":
                    # Gemini 不直接支持 system role，将其作为 user 消息
                    contents.append({
                        "role": "user",
                        "parts": [{"text": f"System: {msg.content}"}]
                    })
                elif msg.role == "user":
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg.content}]
                    })
                elif msg.role == "assistant":
                    contents.append({
                        "role": "model",  # Gemini 使用 "model" 而不是 "assistant"
                        "parts": [{"text": msg.content}]
                    })
        
        # 添加当前请求（图像 + 提示词）
        # 解码 base64 图像数据
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise ModelAPIError(f"Failed to decode base64 image: {e}")
        
        # 构建当前消息的 parts
        current_parts = [
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg'
            ),
            prompt
        ]
        
        contents.append(current_parts)
        
        return contents
    
    async def _complete_response(self, contents: list) -> str:
        """获取完整响应"""
        try:
            # Gemini SDK 使用同步调用，需要在异步环境中包装
            def _sync_call():
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents
                )
                return response
            
            response = await asyncio.to_thread(_sync_call)
            
            # 解析响应
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts_text = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            parts_text.append(part.text)
                    return ''.join(parts_text)
            
            raise ModelAPIError(f"Unexpected response format: {response}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Gemini API request timed out")
            elif "connect" in str(e).lower() or "connection" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Gemini API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Gemini API error: {str(e)}")
    
    async def _stream_response(self, contents: list) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            def _sync_stream():
                stream = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT"]
                    )
                )
                return stream
            
            # 注意：Gemini SDK 的流式支持可能需要特殊处理
            # 这里提供基本实现，可能需要根据实际 SDK 行为调整
            response = await asyncio.to_thread(_sync_stream)
            
            # 如果响应支持迭代
            if hasattr(response, '__iter__'):
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            else:
                # 如果不支持流式，返回完整响应
                if hasattr(response, 'text'):
                    yield response.text
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Gemini API request timed out")
            elif "connect" in str(e).lower() or "connection" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Gemini API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Gemini API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接
        
        发送一个简单的测试请求
        """
        try:
            def _sync_test():
                # 发送一个简单的测试请求
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=["Hello"]
                )
                return response is not None
            
            return await asyncio.to_thread(_sync_test)
            
        except Exception:
            return False
