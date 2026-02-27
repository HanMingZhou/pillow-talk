"""Anthropic Claude 视觉模型适配器

支持 Claude 3 系列多模态模型（Claude 3 Opus, Sonnet, Haiku）
"""
import base64
import httpx
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError


class ClaudeAdapter(MultimodalInterface):
    """Anthropic Claude 视觉模型适配器
    
    支持 Claude 3 系列多模态模型
    """
    
    # Claude API 端点
    API_URL = "https://api.anthropic.com/v1/messages"
    
    # 支持的模型
    SUPPORTED_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620"
    ]
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 30,
        max_tokens: int = 4096
    ):
        """初始化 Claude 适配器
        
        Args:
            api_key: Anthropic API Key
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_tokens: 最大生成 token 数
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        
        # 验证模型名称
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}"
            )
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        Args:
            image_base64: Base64 编码的图像数据
            prompt: 用户提示词
            conversation_history: 对话历史
            stream: 是否使用流式响应
            
        Returns:
            生成的文本响应（流式或完整）
        """
        messages = self._build_messages(
            image_base64,
            prompt,
            conversation_history
        )
        
        # 提取 system prompt
        system_prompt = self._extract_system_prompt(conversation_history)
        
        if stream:
            return self._stream_response(messages, system_prompt)
        else:
            return await self._complete_response(messages, system_prompt)
    
    def _build_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建 Claude 格式的消息列表
        
        Claude 使用特殊的消息格式，图像作为 content 的一部分
        """
        messages = []
        
        # 添加对话历史（跳过 system 消息，它们会单独处理）
        if conversation_history:
            for msg in conversation_history:
                if msg.role == "system":
                    continue  # System messages handled separately
                elif msg.role in ["user", "assistant"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # 添加当前请求（图像 + 提示词）
        # Claude 要求图像数据不包含 data:image/jpeg;base64, 前缀
        clean_image_data = image_base64
        if ',' in image_base64:
            clean_image_data = image_base64.split(',', 1)[1]
        
        # 检测图像格式
        media_type = "image/jpeg"
        if image_base64.startswith("data:image/png"):
            media_type = "image/png"
        elif image_base64.startswith("data:image/webp"):
            media_type = "image/webp"
        elif image_base64.startswith("data:image/gif"):
            media_type = "image/gif"
        
        # 构建当前消息
        current_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": clean_image_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
        
        messages.append(current_message)
        
        return messages
    
    def _extract_system_prompt(
        self,
        conversation_history: Optional[List[Message]] = None
    ) -> Optional[str]:
        """从对话历史中提取 system prompt
        
        Claude 将 system prompt 作为单独的参数
        """
        if not conversation_history:
            return None
        
        system_messages = [
            msg.content for msg in conversation_history
            if msg.role == "system"
        ]
        
        if system_messages:
            return "\n\n".join(system_messages)
        
        return None
    
    async def _complete_response(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """获取完整响应"""
        try:
            async with httpx.AsyncClient() as client:
                # 构建请求体
                request_body = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": messages
                }
                
                if system_prompt:
                    request_body["system"] = system_prompt
                
                # 发送请求
                response = await client.post(
                    self.API_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json=request_body,
                    timeout=self.timeout
                )
                
                # 检查响应状态
                if response.status_code == 401:
                    raise ModelAPIError("Invalid API key")
                elif response.status_code == 429:
                    raise ModelAPIError("Rate limit exceeded")
                elif response.status_code != 200:
                    error_detail = response.text
                    raise ModelAPIError(
                        f"Claude API error (status {response.status_code}): {error_detail}"
                    )
                
                # 解析响应
                result = response.json()
                
                # Claude 响应格式: {"content": [{"type": "text", "text": "..."}], ...}
                if "content" in result and len(result["content"]) > 0:
                    text_parts = [
                        item["text"] for item in result["content"]
                        if item.get("type") == "text"
                    ]
                    return "".join(text_parts)
                
                raise ModelAPIError(f"Unexpected response format: {result}")
                
        except httpx.TimeoutException:
            raise ModelTimeoutError("Claude API request timed out")
        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to Claude API: {e}")
        except (ModelAPIError, ModelTimeoutError, ModelConnectionError):
            raise
        except Exception as e:
            raise ModelAPIError(f"Claude API error: {str(e)}")
    
    async def _stream_response(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            async with httpx.AsyncClient() as client:
                # 构建请求体
                request_body = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": messages,
                    "stream": True
                }
                
                if system_prompt:
                    request_body["system"] = system_prompt
                
                # 发送流式请求
                async with client.stream(
                    "POST",
                    self.API_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json=request_body,
                    timeout=self.timeout
                ) as response:
                    # 检查响应状态
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        raise ModelAPIError(
                            f"Claude API error (status {response.status_code}): {error_detail.decode()}"
                        )
                    
                    # 处理 SSE 流
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # Claude SSE 格式: "data: {...}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            # 跳过特殊事件
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                import json
                                data = json.loads(data_str)
                                
                                # Claude 流式响应格式
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            yield text
                                
                            except json.JSONDecodeError:
                                continue
                        
        except httpx.TimeoutException:
            raise ModelTimeoutError("Claude API request timed out")
        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to Claude API: {e}")
        except (ModelAPIError, ModelTimeoutError, ModelConnectionError):
            raise
        except Exception as e:
            raise ModelAPIError(f"Claude API streaming error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接
        
        发送一个简单的测试请求
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 10,
                        "messages": [
                            {
                                "role": "user",
                                "content": "Hello"
                            }
                        ]
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception:
            return False
