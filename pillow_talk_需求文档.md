# Pillow Talk 需求文档（最终版）

## 1. 项目概述

### 1.1 项目定位
Pillow Talk 是一款基于多模态大语言模型（MLLM）的智能视觉语音助手。用户通过移动设备摄像头扫描现实物体，系统利用 AI 进行视觉理解，并根据预设 Prompt 生成自然的语音对话输出，提供陪伴、科普或娱乐体验。

### 1.2 核心目标
- **视觉识别**：实时预览或拍照扫描物体，利用多模态模型进行视觉理解
- **模型聚合**：支持主流云厂商模型及用户自定义部署的模型接口
- **语音交互**：将 AI 生成的文本转化为自然语音输出（TTS）
- **跨平台**：同时发布 iOS 和 Android 应用

---

## 2. 用户场景

| 场景 | 描述 | 预期结果 |
| :--- | :--- | :--- |
| 基础识别 | 用户打开 App，对准桌上的苹果拍照 | 识别出苹果，用语音说："这是一个看起来很美味的红苹果，你想尝尝吗？" |
| 自定义模型 | 用户配置自己部署的模型 API 地址和 Key | 成功调用私有模型，数据不经过公有云 |
| 人设切换 | 用户切换不同"人设"（科普专家、可爱宠物、毒舌评论家） | AI 回复的语气和风格随人设改变 |
| 多轮对话 | 用户与识别的物体进行连续对话 | 保持上下文，实现自然的多轮交互 |

---

## 3. 核心功能需求

### 3.1 移动端应用

#### 3.1.1 摄像头模块
- 实时预览与自动对焦
- 支持手动拍照或自动识别模式（可配置频率，如每 2 秒）
- 图像预处理：压缩、裁剪后转换为 Base64 上传
- 权限管理：相机、麦克风、存储权限

#### 3.1.2 模型配置页
- **预设模型列表**：
  - OpenAI (GPT-4o, GPT-4V)
  - Google (Gemini 2.5 Pro)
  - Anthropic (Claude 4.5 Sonnet)
  - 豆包 (doubao-seedance-2-0-260128) 
  - Meta LLaMA 多模态版本
- **自定义模型**：
  - 输入 Base URL、API Key、Model Name
  - 支持自定义 Header 和 Token 认证
  - 提供"测试连接"功能验证配置有效性

#### 3.1.3 Prompt 管理
- 内置 Prompt 模板（如："你是一个博学的博物馆讲解员"）
- 支持用户自定义 System Prompt
- 支持多 Prompt 模式切换
- 支持情绪风格模式（温柔、活泼、专业等）

#### 3.1.4 交互界面
- **扫描界面**：全屏相机预览，底部操作栏
- **对话界面**：显示识别结果文本，播放语音波形动画
- **历史记录**：本地保存最近的扫描和对话记录
- **对话模式**：支持单轮识别和多轮对话上下文保持

#### 3.1.5 语音播放
- 集成 TTS 播放控件，支持暂停、重播
- 支持男声/女声、语速调整
- 支持流式播放和语音缓存
- 支持中英文

### 3.2 后端服务

#### 3.2.1 模型适配层
- 定义统一的 `MultimodalInterface` 抽象基类
- 实现各厂商适配器（OpenAIAdapter, GeminiAdapter, ClaudeAdapter,DoubaoAdapter,CustomAdapter）
- 统一输入输出格式：Image + Prompt → Text
- 支持流式输出（SSE）

#### 3.2.2 Prompt 引擎
- 接收前端传来的图像和 System Prompt
- 组装符合各模型要求的 Message 结构
- 支持多轮对话上下文管理

#### 3.2.3 语音服务（TTS）
- 支持多种 TTS 服务：
  - OpenAI TTS
  - Google Cloud TTS
  - Microsoft Azure TTS
  - Edge TTS
  - 阿里云 TTS
  - 本地 Coqui TTS（可选）
- 支持流式音频输出

#### 3.2.4 API 接口设计

**统一对话接口**
```http
POST /api/v1/chat
Content-Type: application/json

{
  "image_base64": "data:image/jpeg;base64,...",
  "system_prompt": "你是一只猫，请用喵星人语气说话",
  "provider": "openai",  // 或 "custom"
  "custom_config": {     // provider 为 custom 时必填
    "base_url": "http://my-server/v1",
    "api_key": "sk-...",
    "model_name": "llava-v1.5"
  },
  "conversation_id": "uuid",  // 多轮对话 ID（可选）
  "stream": true              // 是否流式输出
}
```

**响应格式**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "text": "喵！这是一个球！我要玩！",
    "audio_url": "https://storage.../audio.mp3",
    "conversation_id": "uuid",
    "latency_ms": 1200
  }
}
```

**其他接口**
```http
POST /api/v1/analyze        # 仅识别，返回文本
POST /api/v1/synthesize     # 仅 TTS，返回音频
GET  /api/v1/models         # 获取支持的模型列表
POST /api/v1/test-connection # 测试自定义模型连接
```

---

## 4. 技术架构

### 4.1 架构图
```
[Mobile App (React Native + TypeScript)]
            ↓ HTTPS/JSON
[API Gateway / Python Backend (FastAPI)]
            ↓
    [Model Router] ──→ [OpenAI API]
            ↓          [Google API]
    [TTS Service]      [Anthropic API]
            ↓          [Custom API]
    [Audio Stream]
```

### 4.2 技术选型

**移动端**
- 框架：React Native (推荐使用 Expo)
- 语言：TypeScript
- 核心库：
  - `expo-camera`：摄像头调用
  - `expo-av`：音频播放
  - `react-navigation`：路由导航
  - `axios`：HTTP 请求

**后端**
- 语言：Python 3.12+
- 框架：FastAPI
- 核心库：
  - `pydantic`：数据验证
  - `pydantic-settings`：配置管理
  - `httpx`：异步 HTTP 客户端
  - `openai`：OpenAI SDK
  - `structlog` 或 `loguru`：日志管理
  - `redis`：缓存（可选）
  - `postgresql`：历史记录存储（可选）

**部署**
- Docker + Nginx
- Kubernetes（可选）

---

## 5. Python 项目开发规范（严格遵守）

### 5.1 项目结构（Src Layout）
```
pillow-talk-backend/
├── src/
│   └── pillow_talk/
│       ├── __init__.py
│       ├── main.py              # FastAPI 应用入口
│       ├── api/                 # API 路由
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   └── models.py
│       ├── core/                # 核心配置
│       │   ├── config.py
│       │   ├── security.py
│       │   └── exceptions.py
│       ├── models/              # Pydantic 数据模型
│       │   ├── request.py
│       │   └── response.py
│       ├── services/            # 业务逻辑
│       │   ├── llm/             # 多模态模型适配
│       │   │   ├── base.py
│       │   │   ├── openai.py
│       │   │   ├── gemini.py
│       │   │   └── custom.py
│       │   └── tts/             # 语音合成
│       │       ├── base.py
│       │       └── openai_tts.py
│       └── utils/               # 工具函数
├── tests/                       # 测试代码
│   ├── test_api/
│   ├── test_services/
│   └── conftest.py
├── pyproject.toml               # Poetry 配置
├── Dockerfile
├── Makefile
└── README.md
```

### 5.2 依赖管理
- 使用 **Poetry** 或 **uv** 进行依赖管理
- 锁定文件 `poetry.lock` 必须提交到版本控制
- 禁止硬编码版本号

### 5.3 代码规范
- **格式化**：使用 `ruff` 或 `black` + `isort`
- **Linting**：使用 `ruff` 或 `flake8`
- **类型检查**：必须使用 `mypy`，所有函数需包含 Type Hints
- **文档字符串**：所有公共模块、类、函数必须包含 Google Style 或 NumPy Style 的 Docstring

**示例代码**
```python
from typing import Optional
from pydantic import BaseModel

class ImageRequest(BaseModel):
    """图像识别请求模型"""
    image_data: str  # Base64 encoded
    prompt: Optional[str] = "Describe this object."
    provider: str = "openai"

async def process_image(request: ImageRequest) -> str:
    """处理图像并返回描述
    
    Args:
        request: 包含图像数据和提示词的请求对象
        
    Returns:
        AI 生成的文本描述
        
    Raises:
        ValueError: 当图像数据无效时
    """
    pass
```

### 5.4 测试规范
- 使用 `pytest` 作为测试框架
- 核心业务逻辑单元测试覆盖率 > 80%
- 测试文件命名：`test_<module>.py`
- 使用 `pytest-asyncio` 支持异步测试
- 使用 `pytest-cov` 生成覆盖率报告

### 5.5 日志规范
- 禁止使用 `print`，全量接入 `structlog` 或 `loguru`
- 统一 `request_id` 追踪
- 记录模型调用耗时
- 规范日志级别：DEBUG, INFO, WARNING, ERROR

### 5.6 配置管理
- 使用 `pydantic-settings` 管理环境变量
- 敏感信息（API Keys）通过 `.env` 文件或环境变量注入
- 严禁硬编码敏感信息

### 5.7 Git Hooks
- 使用 `.pre-commit-config.yaml` 配置 Git hooks
- 提交前自动运行：格式化、Linting、类型检查

---

## 6. 非功能需求

### 6.1 性能
- 首字延迟（TTFB）< 3 秒（网络良好情况下）
- 支持并发请求 > 100 QPS
- 图片压缩上传，降低传输延迟
- 模型调用超时控制
- 采用流式传输优化体验

### 6.2 安全性
- 所有 API 通信必须使用 HTTPS
- API Key 在后端加密存储
- 图片数据处理后立即从内存清除，不持久化存储（除非用户明确同意）
- Token 认证
- Rate Limit 限流
- 防 Prompt 注入策略

### 6.3 兼容性
- iOS 15.0+
- Android 10.0+
- 适配不同屏幕尺寸（包括刘海屏、灵动岛）

### 6.4 可扩展性
- 新增模型提供商时，只需在后端新增 Adapter 类
- 前端无需修改代码

---

## 7. 开发计划

### Phase 1: MVP（原型验证）
- 完成 Python 后端基础架构
- 实现 OpenAI GPT-4V 接入
- 完成 React Native 基础相机页面
- 实现"拍照 → 识别 → 文本显示"流程

### Phase 2: 语音与多模型
- 集成 TTS 服务，实现语音输出
- 完成模型适配层，支持多家厂商
- 支持自定义 API 配置
- 完善 Prompt 配置界面

### Phase 3: 优化与发布
- 性能优化（图片压缩、流式传输）
- 多轮对话支持
- 完成代码审查与测试（覆盖率 > 80%）
- 打包 iOS (.ipa) 和 Android (.apk/.aab)
- 应用商店上架

### Phase 4: 扩展功能（未来规划）
- AR 模式识别
- 情绪陪伴模式
- 社区分享
- 云端对话记录同步
- 本地轻量模型推理

---

## 8. 风险评估

| 风险点 | 描述 | 应对策略 |
| :--- | :--- | :--- |
| API 成本 | 多模态模型调用成本较高 | 支持用户自备 Key；增加缓存；图片压缩传输 |
| 网络延迟 | 语音对话对延迟敏感 | 采用流式传输；边缘节点部署 |
| 隐私合规 | 摄像头数据敏感 | 隐私政策明确；默认不存储图片；支持纯本地模式 |
| 模型幻觉 | AI 识别错误导致对话尴尬 | Prompt 中加入"不确定时请询问用户"；增加用户反馈机制 |
| 审核风险 | 拟人化内容可能违规 | 合规过滤；内容审核机制 |

---

## 9. 附录

### 9.1 pyproject.toml 示例
```toml
[tool.poetry]
name = "pillow-talk-backend"
version = "0.1.0"
description = "Pillow Talk AI Backend"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"
httpx = "^0.26.0"
openai = "^1.10.0"
loguru = "^0.7.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
ruff = "^0.2.0"
mypy = "^1.8.0"
black = "^24.1.0"
isort = "^5.13.0"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 9.2 自定义模型接口规范
```http
POST /v1/vision-chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "image": "base64_encoded_string",
  "prompt": "Describe this image",
  "model": "model_name"
}

Response:
{
  "text": "This is a red apple on a wooden table."
}
```

---

**文档版本**: v1.0  
**创建日期**: 2026-02-26  
**维护团队**: Pillow Talk 开发组
