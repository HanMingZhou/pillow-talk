"""千问（Qwen）模型适配器

支持阿里云百炼千问视觉模型
使用 dashscope SDK
"""
import asyncio
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError

try:
    import dashscope
except ImportError:
    dashscope = None  # type: ignore


class QwenAdapter(MultimodalInterface):
    """千问视觉模型适配器
    
    使用 dashscope SDK
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-vl-max",
        timeout: int = 30
    ):
        """初始化千问适配器
        
        Args:
            api_key: 阿里云百炼 API Key (DASHSCOPE_API_KEY)
            model: 模型名称（如 qwen-vl-max, qwen-vl-plus 等）
            timeout: 请求超时时间（秒）
            
        Raises:
            ImportError: 如果未安装 dashscope
        """
        if dashscope is None:
            raise ImportError(
                "dashscope is required for Qwen adapter. "
                "Install it with: pip install dashscope"
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        dashscope.api_key = api_key
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应"""
        messages = self._build_qwen_messages(
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
        """流式处理（用于路由直接调用）
        
        将 OpenAI 格式的消息转换为千问格式
        """
        # 转换消息格式
        qwen_messages = self._convert_messages_to_qwen_format(messages)
        async for chunk in self._stream_response(qwen_messages):
            yield chunk
    
    def _convert_messages_to_qwen_format(self, messages: list) -> list:
        """将 OpenAI 格式的消息转换为千问格式"""
        qwen_messages = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # 保存 system 消息内容
            if role == "system":
                system_prompt = content
                continue
            
            # 处理用户消息
            if role == "user":
                if isinstance(content, list):
                    # OpenAI 格式的多模态内容
                    qwen_content = []
                    
                    # 如果有 system prompt，将其作为第一个文本内容
                    if system_prompt:
                        qwen_content.append({"text": system_prompt})
                        system_prompt = None  # 只添加一次
                    
                    for item in content:
                        if item.get("type") == "image_url":
                            image_url = item.get("image_url", {}).get("url", "")
                            qwen_content.append({"image": image_url})
                        elif item.get("type") == "text":
                            qwen_content.append({"text": item.get("text", "")})
                    
                    qwen_messages.append({"role": "user", "content": qwen_content})
                else:
                    # 纯文本内容
                    text_content = []
                    if system_prompt:
                        text_content.append({"text": system_prompt})
                        system_prompt = None
                    text_content.append({"text": content})
                    qwen_messages.append({"role": "user", "content": text_content})
            else:
                # assistant 消息保持不变
                qwen_messages.append({"role": role, "content": content})
        
        return qwen_messages
    
    def _build_qwen_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建千问格式的消息
        
        千问使用特殊的消息格式：
        - image: 图像 URL 或 base64
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
            {"image": f"data:image/jpeg;base64,{image_base64}"},
            {"text": prompt}
        ]
        
        messages.append({
            "role": "user",
            "content": content
        })
        
        return messages
    
    async def _complete_response(self, messages: list) -> str:
        """获取完整响应"""
        try:
            def _sync_call():
                response = dashscope.MultiModalConversation.call(
                    api_key=self.api_key,
                    model=self.model,
                    messages=messages,
                    enable_thinking=False  # 禁用深度思考模式
                )
                return response
            
            response = await asyncio.to_thread(_sync_call)
            
            # 解析响应
            if response.status_code == 200:
                return response.output.choices[0].message.content[0]["text"]
            else:
                raise ModelAPIError(
                    f"Qwen API error: {response.code} - {response.message}"
                )
                
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Qwen API request timed out")
            elif "connect" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Qwen API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Qwen API error: {str(e)}")
    
    async def _stream_response(self, messages: list) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            def _sync_stream():
                responses = dashscope.MultiModalConversation.call(
                    api_key=self.api_key,
                    model=self.model,
                    messages=messages,
                    stream=True,
                    incremental_output=True,
                    enable_thinking=False  # 禁用深度思考模式
                )
                return responses
            
            responses = await asyncio.to_thread(_sync_stream)
            
            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if isinstance(content, list) and len(content) > 0:
                        if "text" in content[0]:
                            yield content[0]["text"]
                else:
                    raise ModelAPIError(
                        f"Qwen API error: {response.code} - {response.message}"
                    )
                        
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError("Qwen API request timed out")
            elif "connect" in str(e).lower():
                raise ModelConnectionError("Failed to connect to Qwen API")
            elif isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Qwen API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            def _sync_test():
                test_messages = [{
                    "role": "user",
                    "content": [{"text": "Hello"}]
                }]
                
                response = dashscope.MultiModalConversation.call(
                    api_key=self.api_key,
                    model=self.model,
                    messages=test_messages
                )
                return response.status_code == 200
            
            return await asyncio.to_thread(_sync_test)
            
        except Exception:
            return False
    
    async def close(self) -> None:
        """关闭客户端"""
        pass  # dashscope 不需要显式关闭
