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
    
    async def process_image_streaming(
        self,
        messages: list
    ) -> AsyncIterator[str]:
        """流式处理（用于路由直接调用）
        
        从标准消息格式中提取图像和提示词，然后调用流式响应
        """
        # 从 messages 中提取图像和提示词
        image_base64 = None
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
                
                # 处理系统消息
                if role == "system" and isinstance(content, str):
                    prompt_parts.append(content)
                
                # 处理用户消息
                elif role == "user":
                    if isinstance(content, str):
                        prompt_parts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if item.get("type") == "image_url":
                                    image_url = item.get("image_url", {})
                                    if isinstance(image_url, dict):
                                        url = image_url.get("url", "")
                                    else:
                                        url = image_url
                                    
                                    # 提取 base64 数据
                                    if "base64," in url:
                                        image_base64 = url.split("base64,")[1]
                                    else:
                                        image_base64 = url
                                elif item.get("type") == "text":
                                    prompt_parts.append(item.get("text", ""))
        
        if not image_base64:
            raise ModelAPIError("No image found in messages")
        
        if not prompt_parts:
            raise ModelAPIError("No prompt found in messages")
        
        # 合并所有提示词部分
        prompt = "\n\n".join(prompt_parts)
        
        # 构建 Gemini 格式的内容并流式输出
        contents = self._build_gemini_contents(image_base64, prompt, None)
        async for chunk in self._stream_response(contents):
            yield chunk
    
    def _build_gemini_contents(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List:
        """构建 Gemini 格式的内容
        
        Gemini 使用简单的列表格式，包含 Part 对象和文本
        """
        # 解码 base64 图像数据
        try:
            # 移除可能的 data URL 前缀
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',', 1)[1]
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise ModelAPIError(f"Failed to decode base64 image: {e}")
        
        # 构建内容列表（按照官方示例格式）
        contents = [
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg'
            ),
            prompt
        ]
        
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
                # 使用流式生成
                return self.client.models.generate_content_stream(
                    model=self.model,
                    contents=contents
                )
            
            # 在线程中执行同步流式调用
            stream = await asyncio.to_thread(_sync_stream)
            
            # 迭代流式响应
            for chunk in stream:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Gemini API request timed out")
            elif "connect" in str(e).lower() or "connection" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Gemini API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Gemini API streaming error: {str(e)}")
    
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
    
    async def close(self) -> None:
        """关闭客户端"""
        pass  # Gemini SDK 不需要显式关闭
