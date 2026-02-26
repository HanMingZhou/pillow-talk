"""OpenAI 模型适配器

支持 GPT-4V 和 GPT-4o 等多模态模型
"""
import json
import httpx
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError


class OpenAIAdapter(MultimodalInterface):
    """OpenAI GPT-4V/GPT-4o 适配器"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30
    ):
        """初始化 OpenAI 适配器
        
        Args:
            api_key: OpenAI API Key
            model: 模型名称
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应"""
        messages = self._build_messages(image_base64, prompt, conversation_history)
        
        if stream:
            return self._stream_response(messages)
        else:
            return await self._complete_response(messages)
    
    async def _complete_response(self, messages: list) -> str:
        """获取完整响应"""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code != 200:
                raise ModelAPIError(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except httpx.TimeoutException:
            raise ModelTimeoutError("OpenAI API request timed out")
        except httpx.ConnectError:
            raise ModelConnectionError("Failed to connect to OpenAI API")
        except Exception as e:
            if isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"OpenAI API error: {str(e)}")
    
    async def _stream_response(self, messages: list) -> AsyncIterator[str]:
        """流式响应处理"""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "stream": True
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status_code != 200:
                    raise ModelAPIError(
                        f"OpenAI API error: {response.status_code}"
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if content := chunk["choices"][0]["delta"].get("content"):
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                            
        except httpx.TimeoutException:
            raise ModelTimeoutError("OpenAI API request timed out")
        except httpx.ConnectError:
            raise ModelConnectionError("Failed to connect to OpenAI API")
        except Exception as e:
            if isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"OpenAI API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        """关闭客户端"""
        await self.client.aclose()
