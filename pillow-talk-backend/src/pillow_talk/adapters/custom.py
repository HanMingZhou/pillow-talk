"""自定义模型适配器

支持用户自定义部署的多模态模型接口
兼容 OpenAI 格式的 API
"""
import httpx
from typing import AsyncIterator, Optional, List, Dict, Any
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError


class CustomAdapter(MultimodalInterface):
    """自定义模型适配器
    
    支持用户自定义部署的多模态模型
    兼容 OpenAI Chat Completions API 格式
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout: int = 30,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        """初始化自定义模型适配器
        
        Args:
            base_url: API 基础 URL（如 http://localhost:8000/v1）
            api_key: API Key
            model_name: 模型名称
            timeout: 请求超时时间（秒）
            custom_headers: 自定义 HTTP 头
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.custom_headers = custom_headers or {}
        
        # 构建完整的 API 端点
        # 兼容多种 URL 格式
        if '/chat/completions' in self.base_url:
            self.endpoint = self.base_url
        elif self.base_url.endswith('/v1'):
            self.endpoint = f"{self.base_url}/chat/completions"
        else:
            self.endpoint = f"{self.base_url}/v1/chat/completions"
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        使用 OpenAI 兼容的 API 格式
        
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
        
        if stream:
            return self._stream_response(messages)
        else:
            return await self._complete_response(messages)
    
    def _build_messages(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None
    ) -> List[dict]:
        """构建 OpenAI 格式的消息列表
        
        使用 OpenAI Vision API 的消息格式
        """
        messages = []
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role == "system":
                    messages.append({
                        "role": "system",
                        "content": msg.content
                    })
                elif msg.role in ["user", "assistant"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # 添加当前请求（图像 + 提示词）
        # 确保 image_base64 包含完整的 data URI
        if not image_base64.startswith('data:'):
            image_base64 = f"data:image/jpeg;base64,{image_base64}"
        
        current_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    }
                }
            ]
        }
        
        messages.append(current_message)
        
        return messages
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头
        
        Returns:
            HTTP 请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 添加自定义头
        headers.update(self.custom_headers)
        
        return headers
    
    async def _complete_response(self, messages: List[dict]) -> str:
        """获取完整响应"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers=self._build_headers(),
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False
                    },
                    timeout=self.timeout
                )
                
                # 检查响应状态
                if response.status_code == 401:
                    raise ModelAPIError("Invalid API key")
                elif response.status_code == 404:
                    raise ModelAPIError(
                        f"API endpoint not found: {self.endpoint}. "
                        "Please check your base_url configuration."
                    )
                elif response.status_code == 429:
                    raise ModelAPIError("Rate limit exceeded")
                elif response.status_code != 200:
                    error_detail = response.text
                    raise ModelAPIError(
                        f"Custom model API error (status {response.status_code}): {error_detail}"
                    )
                
                # 解析响应（OpenAI 格式）
                result = response.json()
                
                # 标准 OpenAI 响应格式
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                
                # 尝试其他可能的响应格式
                if "text" in result:
                    return result["text"]
                if "response" in result:
                    return result["response"]
                
                raise ModelAPIError(f"Unexpected response format: {result}")
                
        except httpx.TimeoutException:
            raise ModelTimeoutError(f"Custom model API request timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            raise ModelConnectionError(
                f"Failed to connect to custom model API at {self.endpoint}: {e}"
            )
        except (ModelAPIError, ModelTimeoutError, ModelConnectionError):
            raise
        except Exception as e:
            raise ModelAPIError(f"Custom model API error: {str(e)}")
    
    async def _stream_response(self, messages: List[dict]) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers=self._build_headers(),
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": True
                    },
                    timeout=self.timeout
                ) as response:
                    # 检查响应状态
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        raise ModelAPIError(
                            f"Custom model API error (status {response.status_code}): "
                            f"{error_detail.decode()}"
                        )
                    
                    # 处理 SSE 流（OpenAI 格式）
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # OpenAI SSE 格式: "data: {...}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            # 跳过结束标记
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                import json
                                data = json.loads(data_str)
                                
                                # OpenAI 流式响应格式
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                        if content:
                                            yield content
                                
                            except json.JSONDecodeError:
                                continue
                        
        except httpx.TimeoutException:
            raise ModelTimeoutError(f"Custom model API request timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            raise ModelConnectionError(
                f"Failed to connect to custom model API at {self.endpoint}: {e}"
            )
        except (ModelAPIError, ModelTimeoutError, ModelConnectionError):
            raise
        except Exception as e:
            raise ModelAPIError(f"Custom model API streaming error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接
        
        发送一个简单的测试请求
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers=self._build_headers(),
                    json={
                        "model": self.model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": "Hello"
                            }
                        ],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception:
            return False
