"""千问（Qwen）模型适配器

支持阿里云百炼千问视觉模型
使用 OpenAI 兼容的 API 接口
"""
import json
import httpx
from typing import AsyncIterator, Optional, List
from .base import MultimodalInterface
from ..models.config import Message
from ..utils.exceptions import ModelConnectionError, ModelTimeoutError, ModelAPIError


class QwenAdapter(MultimodalInterface):
    """千问视觉模型适配器
    
    使用阿里云百炼 API（OpenAI 兼容格式）
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen3.5-plus",
        region: str = "beijing",  # beijing, virginia, singapore
        timeout: int = 30
    ):
        """初始化千问适配器
        
        Args:
            api_key: 阿里云百炼 API Key (DASHSCOPE_API_KEY)
            model: 模型名称（如 qwen3.5-plus, qwen-vl-max 等）
            region: 地域（beijing/virginia/singapore）
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        
        # 根据地域设置 base_url
        region_urls = {
            "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "virginia": "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
            "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        }
        
        self.base_url = region_urls.get(region, region_urls["beijing"])
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def process_image(
        self,
        image_base64: str,
        prompt: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """处理图像并返回响应
        
        千问使用 OpenAI 兼容的消息格式
        """
        messages = self._build_messages(image_base64, prompt, conversation_history)
        
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
        """构建千问格式的消息
        
        千问使用 OpenAI 兼容的格式
        """
        messages = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": prompt
        })
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                if msg.role != "system":
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
                },
                {
                    "type": "text",
                    "text": "请根据图像内容回答。"
                }
            ]
        })
        
        return messages
    
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
                    f"Qwen API error: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except httpx.TimeoutException:
            raise ModelTimeoutError("Qwen API request timed out")
        except httpx.ConnectError:
            raise ModelConnectionError("Failed to connect to Qwen API")
        except Exception as e:
            if isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Qwen API error: {str(e)}")
    
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
                        f"Qwen API error: {response.status_code}"
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
            raise ModelTimeoutError("Qwen API request timed out")
        except httpx.ConnectError:
            raise ModelConnectionError("Failed to connect to Qwen API")
        except Exception as e:
            if isinstance(e, (ModelAPIError, ModelTimeoutError, ModelConnectionError)):
                raise
            raise ModelAPIError(f"Qwen API error: {str(e)}")
    
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
