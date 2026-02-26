# Pillow Talk Backend

多模态智能视觉语音助手后端服务

## 功能特性

- 🖼️ **图像识别**：支持多模态大语言模型进行视觉理解
- 🤖 **多模型支持**：
  - OpenAI GPT-4V/4o
  - 阿里云千问（Qwen）视觉模型
  - 字节跳动豆包（Doubao）视觉模型
  - 智谱 AI GLM-4V 系列视觉模型
  - Google Gemini 多模态模型
  - Anthropic Claude（待实现）
- 💬 **多轮对话**：支持上下文保持的连续对话
- 🎭 **Prompt 模板**：内置多种人设模板（博物馆讲解员、可爱宠物、科普专家等）
- 🔒 **安全可靠**：API Key 加密存储、限流保护、输入验证
- ⚡ **高性能**：异步 I/O、流式传输、智能缓存
- 📊 **可观测性**：结构化日志、请求追踪、性能指标

## 快速开始

### 环境要求

- Python 3.11+
- Poetry 或 uv

### 安装依赖

```bash
# 使用 Poetry（推荐）
poetry install

# 如果需要豆包支持，安装额外依赖
poetry install -E ark

# 如果需要智谱 GLM 支持
poetry install -E glm

# 如果需要 Gemini 支持
poetry install -E gemini

# 或使用 pip
pip install -e .
pip install volcengine-python-sdk[ark]  # 豆包支持
pip install zai-sdk  # GLM 支持
pip install google-genai  # Gemini 支持
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必需的环境变量
```

必需配置：
- `ENCRYPTION_KEY`: 加密密钥（生产环境必须修改）

可选配置（根据使用的模型提供商）：
- `OPENAI_API_KEY`: OpenAI API Key
- `DOUBAO_API_KEY`: 豆包 API Key（ARK_API_KEY）
- `GLM_API_KEY`: 智谱 GLM API Key
- `GEMINI_API_KEY`: Google Gemini API Key
- `GOOGLE_API_KEY`: 千问 API Key（DASHSCOPE_API_KEY）或 Google API Key

### 运行服务

```bash
# 开发模式
make run

# 或直接使用 uvicorn
uvicorn pillow_talk.main:app --reload
```

服务将在 http://localhost:8000 启动

### API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 健康检查
```
GET /health
```

### 获取模型列表
```
GET /api/v1/models
```

### 测试模型连接
```
POST /api/v1/test-connection
```

### 对话接口
```
POST /api/v1/chat
```

请求示例：
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "system_prompt": "你是一个博学的博物馆讲解员",
  "provider": "openai",  // 可选：openai, doubao, qwen
  "stream": false,
  "tts_enabled": true
}
```

支持的模型提供商：
- `openai`: OpenAI GPT-4V/4o
- `doubao`: 字节跳动豆包视觉模型
- `qwen`: 阿里云千问视觉模型
- `glm`: 智谱 AI GLM-4V 系列视觉模型
- `gemini`: Google Gemini 多模态模型

## 开发指南

### 代码格式化

```bash
make format
```

### 代码检查

```bash
make lint
```

### 类型检查

```bash
make type-check
```

### 运行测试

```bash
make test
```

### 测试覆盖率

```bash
make coverage
```

## 项目结构

```
pillow-talk-backend/
├── src/
│   └── pillow_talk/
│       ├── __init__.py
│       ├── main.py              # FastAPI 应用入口
│       ├── config.py            # 配置管理
│       ├── api/                 # API 路由
│       ├── core/                # 核心业务逻辑
│       ├── adapters/            # 模型适配器
│       ├── tts/                 # TTS 服务
│       ├── models/              # 数据模型
│       ├── services/            # 服务层
│       └── utils/               # 工具函数
├── tests/                       # 测试代码
├── pyproject.toml              # Poetry 配置
├── Dockerfile                  # Docker 配置
└── README.md
```

## Docker 部署

### 构建镜像

```bash
make docker-build
```

### 运行容器

```bash
make docker-run
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/pillow-talk/backend
- 问题反馈: https://github.com/pillow-talk/backend/issues
