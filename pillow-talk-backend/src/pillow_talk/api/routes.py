"""API 路由

定义所有 API 端点。
"""
import time
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import structlog

from ..models.request import ChatRequest, TestConnectionRequest
from ..models.response import (
    ChatResponse,
    ChatData,
    TestConnectionResponse,
    TestConnectionData,
    ModelsResponse,
    ModelInfo,
    HealthResponse
)
from ..core.conversation import ConversationManager
from ..core.image import ImagePreprocessor
from ..core.prompt import PromptEngine
from ..adapters import ModelAdapterFactory
from ..tts import TTSSystem
from ..config import settings
from .dependencies import (
    get_conversation_manager,
    get_image_preprocessor,
    get_prompt_engine,
    get_tts_system,
    get_request_id
)


logger = structlog.get_logger(__name__)

# 创建路由器
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查端点
    
    Returns:
        HealthResponse: 服务健康状态
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now().isoformat()
    )


@router.get("/api/v1/models", response_model=ModelsResponse)
async def list_models(
    request_id: str = Depends(get_request_id)
) -> ModelsResponse:
    """获取支持的模型列表
    
    Args:
        request_id: 请求 ID
        
    Returns:
        ModelsResponse: 模型列表
    """
    logger.info("list_models_request", request_id=request_id)
    
    models = [
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            supports_vision=True,
            supports_streaming=True,
            description="OpenAI 最新多模态模型"
        ),
        ModelInfo(
            id="gpt-4-vision-preview",
            name="GPT-4 Vision",
            provider="openai",
            supports_vision=True,
            supports_streaming=True,
            description="OpenAI GPT-4 视觉模型"
        ),
        ModelInfo(
            id="qwen-vl-plus",
            name="Qwen VL Plus",
            provider="qwen",
            supports_vision=True,
            supports_streaming=True,
            description="阿里云千问视觉模型"
        ),
        ModelInfo(
            id="doubao-vision",
            name="Doubao Vision",
            provider="doubao",
            supports_vision=True,
            supports_streaming=True,
            description="字节跳动豆包视觉模型"
        ),
        ModelInfo(
            id="glm-4v",
            name="GLM-4V",
            provider="glm",
            supports_vision=True,
            supports_streaming=True,
            description="智谱 AI GLM 视觉模型"
        ),
        ModelInfo(
            id="gemini-pro-vision",
            name="Gemini Pro Vision",
            provider="gemini",
            supports_vision=True,
            supports_streaming=True,
            description="Google Gemini 视觉模型"
        ),
    ]
    
    return ModelsResponse(
        code=0,
        message="success",
        data=models
    )


@router.post("/api/v1/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    request: TestConnectionRequest,
    request_id: str = Depends(get_request_id)
) -> TestConnectionResponse:
    """测试模型连接
    
    Args:
        request: 测试连接请求
        request_id: 请求 ID
        
    Returns:
        TestConnectionResponse: 连接测试结果
    """
    start_time = time.time()
    
    logger.info(
        "test_connection_request",
        request_id=request_id,
        provider=request.provider
    )
    
    try:
        # 创建适配器配置
        adapter_config = _build_adapter_config(request.provider, request.custom_config)
        
        # 创建适配器
        adapter = ModelAdapterFactory.create_adapter(
            provider=request.provider,
            **adapter_config
        )
        
        # 测试连接
        success = await adapter.test_connection()
        latency_ms = int((time.time() - start_time) * 1000)
        
        await adapter.close()
        
        logger.info(
            "test_connection_success",
            request_id=request_id,
            provider=request.provider,
            latency_ms=latency_ms
        )
        
        return TestConnectionResponse(
            code=0,
            message="success",
            data=TestConnectionData(
                success=success,
                latency_ms=latency_ms,
                error_message=None if success else "Connection failed"
            ),
            request_id=request_id
        )
    
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            "test_connection_failed",
            request_id=request_id,
            provider=request.provider,
            error=str(e),
            exc_info=True
        )
        
        return TestConnectionResponse(
            code=1,
            message="error",
            data=TestConnectionData(
                success=False,
                latency_ms=latency_ms,
                error_message=str(e)
            ),
            request_id=request_id
        )


@router.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    image_preprocessor: ImagePreprocessor = Depends(get_image_preprocessor),
    prompt_engine: PromptEngine = Depends(get_prompt_engine),
    tts_system: TTSSystem | None = Depends(get_tts_system),
    request_id: str = Depends(get_request_id)
):
    """统一对话接口
    
    支持流式和非流式响应。
    
    Args:
        request: 对话请求
        conversation_manager: 对话管理器
        image_preprocessor: 图像预处理器
        prompt_engine: Prompt 引擎
        tts_system: TTS 系统（可选）
        request_id: 请求 ID
        
    Returns:
        ChatResponse 或 StreamingResponse
    """
    start_time = time.time()
    
    logger.info(
        "chat_request",
        request_id=request_id,
        provider=request.provider,
        stream=request.stream,
        tts_enabled=request.tts_enabled
    )
    
    try:
        # 1. 解码和验证图像
        image_data = ImagePreprocessor.decode_base64(request.image_base64)
        
        if not image_preprocessor.validate_image(image_data):
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # 2. 处理图像
        processed_image = await image_preprocessor.process(image_data)
        image_process_time = time.time() - start_time
        
        # 3. 获取或创建对话
        if request.conversation_id:
            if not conversation_manager.conversation_exists(request.conversation_id):
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_id = request.conversation_id
        else:
            conversation_id = conversation_manager.create_conversation()
        
        # 4. 获取对话历史
        history = conversation_manager.get_history(conversation_id)
        
        # 5. 构建消息
        messages = prompt_engine.build_messages(
            system_prompt=request.system_prompt,
            conversation_history=history,
            image_base64=processed_image
        )
        
        # 6. 创建模型适配器
        adapter_config = _build_adapter_config(request.provider, request.custom_config)
        adapter = ModelAdapterFactory.create_adapter(
            provider=request.provider,
            **adapter_config
        )
        
        # 7. 处理流式或非流式响应
        if request.stream:
            # 流式响应
            return StreamingResponse(
                _stream_chat_response(
                    adapter=adapter,
                    messages=messages,
                    conversation_manager=conversation_manager,
                    conversation_id=conversation_id,
                    request_id=request_id
                ),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            response_text = await adapter.process_image(
                image_base64=processed_image,
                prompt=request.system_prompt,
                conversation_history=history,
                stream=False
            )
            
            await adapter.close()
            
            model_process_time = time.time() - start_time - image_process_time
            
            # 8. 保存对话
            conversation_manager.add_message(conversation_id, "user", "Image uploaded")
            conversation_manager.add_message(conversation_id, "assistant", response_text)
            
            # 9. 生成 TTS 音频（如果启用）
            audio_url = None
            tts_process_time = 0
            
            if request.tts_enabled and tts_system:
                tts_start = time.time()
                try:
                    audio_response = await tts_system.generate_audio(
                        text=response_text,
                        voice=request.tts_voice,
                        speed=request.tts_speed
                    )
                    if audio_response:
                        audio_url = audio_response.audio_url
                    tts_process_time = time.time() - tts_start
                except Exception as e:
                    logger.error(
                        "tts_generation_failed",
                        request_id=request_id,
                        error=str(e)
                    )
                    # 继续返回文本响应，TTS 失败不影响主流程
            
            # 10. 计算总延迟
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "chat_completed",
                request_id=request_id,
                conversation_id=conversation_id,
                total_latency_ms=total_latency_ms,
                image_process_ms=int(image_process_time * 1000),
                model_process_ms=int(model_process_time * 1000),
                tts_process_ms=int(tts_process_time * 1000)
            )
            
            return ChatResponse(
                code=0,
                message="success",
                data=ChatData(
                    text=response_text,
                    audio_url=audio_url,
                    conversation_id=conversation_id,
                    latency_ms=total_latency_ms
                ),
                request_id=request_id
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "chat_failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_response(
    adapter,
    messages: list,
    conversation_manager: ConversationManager,
    conversation_id: str,
    request_id: str
) -> AsyncGenerator[str, None]:
    """流式对话响应生成器
    
    Args:
        adapter: 模型适配器
        messages: 消息列表
        conversation_manager: 对话管理器
        conversation_id: 对话 ID
        request_id: 请求 ID
        
    Yields:
        str: SSE 格式的响应数据
    """
    try:
        full_response = ""
        
        async for chunk in adapter.process_image_streaming(messages):
            full_response += chunk
            # 发送 SSE 格式数据
            yield f"data: {chunk}\n\n"
        
        # 保存完整对话
        conversation_manager.add_message(conversation_id, "user", "Image uploaded")
        conversation_manager.add_message(conversation_id, "assistant", full_response)
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
        
        logger.info(
            "stream_chat_completed",
            request_id=request_id,
            conversation_id=conversation_id
        )
    
    except Exception as e:
        logger.error(
            "stream_chat_failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        yield f"data: [ERROR] {str(e)}\n\n"
    
    finally:
        await adapter.close()


def _build_adapter_config(provider: str, custom_config=None) -> dict:
    """构建适配器配置
    
    Args:
        provider: 模型提供商
        custom_config: 自定义配置
        
    Returns:
        dict: 适配器配置字典
        
    Raises:
        HTTPException: 如果配置无效
    """
    if provider == "openai":
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API Key not configured"
            )
        return {
            "api_key": settings.openai_api_key,
            "timeout": settings.model_timeout
        }
    
    elif provider == "doubao":
        if not settings.doubao_api_key:
            raise HTTPException(
                status_code=400,
                detail="Doubao API Key not configured"
            )
        return {
            "api_key": settings.doubao_api_key,
            "timeout": settings.model_timeout
        }
    
    elif provider == "qwen":
        if not settings.google_api_key:  # 临时使用
            raise HTTPException(
                status_code=400,
                detail="Qwen API Key not configured"
            )
        return {
            "api_key": settings.google_api_key,
            "timeout": settings.model_timeout
        }
    
    elif provider == "glm":
        if not settings.glm_api_key:
            raise HTTPException(
                status_code=400,
                detail="GLM API Key not configured"
            )
        return {
            "api_key": settings.glm_api_key,
            "timeout": settings.model_timeout
        }
    
    elif provider == "gemini":
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=400,
                detail="Gemini API Key not configured"
            )
        return {
            "api_key": settings.gemini_api_key,
            "timeout": settings.model_timeout
        }
    
    elif provider == "custom":
        if not custom_config:
            raise HTTPException(
                status_code=400,
                detail="Custom config required for custom provider"
            )
        return {
            "base_url": custom_config.base_url,
            "api_key": custom_config.api_key,
            "model_name": custom_config.model_name,
            "headers": custom_config.headers,
            "timeout": settings.model_timeout
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}"
        )


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """提供音频文件服务
    
    Args:
        filename: 音频文件名
        
    Returns:
        FileResponse: 音频文件
        
    Raises:
        HTTPException: 如果文件不存在
    """
    # 从 TTS 配置获取音频存储目录
    audio_dir = Path(settings.tts_audio_dir) if hasattr(settings, 'tts_audio_dir') else Path("audio_files")
    audio_path = audio_dir / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )
