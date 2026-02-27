# Implementation Plan: Pillow Talk 多模态助手

## Overview

本实现计划将 Pillow Talk 多模态助手从设计转化为可执行的代码。系统采用 Python 后端（FastAPI）+ React Native 移动端架构，支持多家云厂商的多模态模型和 TTS 服务。实现将遵循 Src Layout 项目结构，使用 Poetry 进行依赖管理，并严格遵循 Python 最佳实践。

实现策略：
1. 首先搭建项目基础架构和配置
2. 实现核心业务逻辑层（对话管理、Prompt 引擎、图像预处理）
3. 实现模型适配层和 TTS 服务层
4. 实现 API 网关和中间件
5. 添加安全和限流功能
6. 完善日志和错误处理
7. 配置部署环境

## Tasks

- [x] 1. 项目初始化与基础配置
  - 创建 Src Layout 项目结构（src/pillow_talk/ 目录）
  - 使用 Poetry 初始化项目，配置 pyproject.toml
  - 添加核心依赖：FastAPI、uvicorn、pydantic、pydantic-settings、httpx、structlog
  - 添加开发工具依赖：pytest、ruff、mypy、pre-commit
  - 创建 .env.example 文件，定义所有环境变量
  - 创建 .gitignore 文件
  - 配置 ruff 和 mypy 在 pyproject.toml 中
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.8, 10.9_


- [x] 2. 配置管理和数据模型
  - [x] 2.1 实现配置管理模块（src/pillow_talk/config.py）
    - 使用 pydantic-settings 创建 Settings 类
    - 定义所有配置项：应用配置、服务器配置、安全配置、限流配置、对话配置、图像处理配置、模型配置、TTS 配置、日志配置
    - 实现从 .env 文件加载配置
    - 添加配置验证逻辑
    - _Requirements: 10.9_

  - [x] 2.2 实现请求和响应数据模型（src/pillow_talk/models/）
    - 创建 request.py：定义 ChatRequest、TestConnectionRequest、CustomModelConfig、ModelProvider 枚举
    - 创建 response.py：定义 ChatResponse、ChatData、TestConnectionResponse、ModelsResponse、ErrorResponse
    - 创建 config.py：定义 Message、Conversation、RequestMetrics
    - 为所有模型添加 Pydantic 验证器
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.9, 7.10_

  - [ ]* 2.3 编写数据模型单元测试
    - 测试请求模型的验证逻辑（无效 Base64、URL 格式等）
    - 测试响应模型的序列化
    - 测试配置模型的环境变量加载
    - _Requirements: 10.6_

- [-] 3. 工具模块实现
  - [x] 3.1 实现日志系统（src/pillow_talk/utils/logger.py）
    - 使用 structlog 配置结构化日志
    - 实现 setup_logger 函数，支持 JSON 格式输出
    - 实现 RequestLogger 类，提供 log_request、log_response、log_error 方法
    - 支持通过环境变量配置日志级别
    - _Requirements: 10.8, 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 3.2 实现自定义异常类（src/pillow_talk/utils/exceptions.py）
    - 定义 ModelConnectionError、ModelTimeoutError、ModelAPIError
    - 定义 TTSServiceError
    - 定义 RateLimitError、AuthenticationError
    - 为每个异常添加错误码和建议消息
    - _Requirements: 13.7, 13.8_

  - [x] 3.3 实现解析器和格式化器（src/pillow_talk/utils/parser.py）
    - 实现 Parser 类：parse_toml、parse_json、parse_env 方法
    - 实现 PrettyPrinter 类：format_json、format_toml、format_error 方法
    - 实现错误建议生成函数
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 7.10_

  - [ ]* 3.4 编写工具模块单元测试
    - 测试日志记录功能
    - 测试异常类的错误消息
    - 测试解析器对有效和无效输入的处理
    - 测试格式化器的输出格式
    - _Requirements: 10.6_


- [-] 4. 核心业务逻辑层
  - [x] 4.1 实现图像预处理器（src/pillow_talk/core/image.py）
    - 实现 ImagePreprocessor 类
    - 实现 process 方法：压缩图像至 1MB 以下，保持 JPEG 质量 >= 85
    - 实现 validate_image 方法：验证图像格式
    - 处理 RGBA 到 RGB 的转换
    - 实现 Base64 编码
    - 确保处理时间 < 500ms
    - _Requirements: 1.6, 1.7, 1.8, 12.3_

  - [ ]* 4.2 编写图像预处理器单元测试
    - 测试图像压缩功能
    - 测试格式转换（RGBA -> RGB）
    - 测试 Base64 编码
    - 测试无效图像的处理
    - _Requirements: 1.6, 1.7, 1.8_

  - [x] 4.3 实现 Prompt 引擎（src/pillow_talk/core/prompt.py）
    - 实现 PromptTemplate 数据模型
    - 实现 PromptEngine 类
    - 定义 5 个内置 Prompt 模板：博物馆讲解员、可爱宠物、科普专家、毒舌评论家、温柔陪伴者
    - 实现 get_template、list_templates 方法
    - 实现 build_messages 方法：组装 System Prompt、对话历史和图像
    - _Requirements: 3.1, 3.4, 3.6_

  - [ ]* 4.4 编写 Prompt 引擎单元测试
    - 测试内置模板的获取
    - 测试消息组装逻辑
    - 测试对话历史的正确包含
    - _Requirements: 3.1, 3.4, 3.6_

  - [x] 4.5 实现对话管理器（src/pillow_talk/core/conversation.py）
    - 实现 Message 和 Conversation 数据模型
    - 实现 ConversationManager 类
    - 实现 create_conversation 方法：生成 UUID 格式的 conversation_id
    - 实现 add_message 方法：添加消息到历史，保持最近 10 轮对话
    - 实现 get_history 方法：获取对话历史
    - 实现 cleanup_expired 方法：清理超过 30 分钟无活动的对话
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

  - [ ]* 4.6 编写对话管理器单元测试
    - 测试对话创建和 ID 生成
    - 测试消息添加和历史限制（最多 10 轮）
    - 测试过期对话清理
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

- [ ] 5. Checkpoint - 核心业务逻辑验证
  - 运行所有核心模块的单元测试
  - 确保图像预处理、Prompt 引擎、对话管理器功能正常
  - 如有问题，请向用户反馈


- [-] 6. 模型适配层实现
  - [x] 6.1 实现模型适配器基类（src/pillow_talk/adapters/base.py）
    - 定义 MultimodalInterface 抽象基类
    - 定义 process_image 抽象方法：接受图像、Prompt、对话历史，返回文本或流式响应
    - 定义 test_connection 抽象方法
    - 添加类型注解和文档字符串
    - _Requirements: 8.1, 8.4, 8.5_

  - [x] 6.2 实现 OpenAI 适配器（src/pillow_talk/adapters/openai.py）
    - 实现 OpenAIAdapter 类，继承 MultimodalInterface
    - 实现 process_image 方法：支持 GPT-4V 和 GPT-4o
    - 实现流式响应处理（_stream_response）
    - 实现完整响应处理（_complete_response）
    - 实现 test_connection 方法
    - 使用 httpx.AsyncClient 进行异步请求
    - 设置 30 秒超时
    - _Requirements: 2.1, 4.1, 4.2, 4.3, 8.2, 8.7, 12.4, 12.6_

  - [x] 6.3 实现 Gemini 适配器（src/pillow_talk/adapters/gemini.py）


    - 实现 GeminiAdapter 类，继承 MultimodalInterface
    - 适配 Google Gemini API 格式
    - 实现流式和非流式响应处理
    - 实现 test_connection 方法
    - _Requirements: 2.1, 4.1, 8.2, 8.6, 8.7_



  - [ ] 6.4 实现 Claude 适配器（src/pillow_talk/adapters/claude.py）
    - 实现 ClaudeAdapter 类，继承 MultimodalInterface
    - 适配 Anthropic Claude API 格式
    - 实现流式和非流式响应处理
    - 实现 test_connection 方法
    - _Requirements: 2.1, 4.1, 8.2, 8.6, 8.7_

  - [x] 6.5 实现豆包适配器（src/pillow_talk/adapters/doubao.py）
    - 实现 DoubaoAdapter 类，继承 MultimodalInterface
    - 适配字节豆包 API 格式
    - 实现流式和非流式响应处理



    - 实现 test_connection 方法
    - _Requirements: 2.1, 4.1, 8.2, 8.6, 8.7_

  - [ ] 6.6 实现自定义模型适配器（src/pillow_talk/adapters/custom.py）
    - 实现 CustomAdapter 类，继承 MultimodalInterface
    - 支持自定义 Base URL、API Key、Model Name
    - 支持自定义 HTTP Header
    - 实现流式和非流式响应处理
    - 实现 test_connection 方法
    - _Requirements: 2.3, 2.4, 8.2, 8.3, 8.6, 8.7_

  - [x] 6.7 实现模型适配器工厂（src/pillow_talk/adapters/__init__.py）
    - 实现 ModelAdapterFactory 类
    - 实现 create_adapter 方法：根据 provider 创建对应的适配器实例
    - 处理不支持的 provider 错误
    - _Requirements: 8.3_

  - [ ]* 6.8 编写模型适配器单元测试
    - 测试各适配器的消息格式转换
    - 测试流式响应解析
    - 测试错误处理（连接失败、超时、API 错误）
    - 测试工厂模式的适配器创建
    - _Requirements: 4.5, 4.6, 8.6_


- [ ] 7. TTS 服务层实现
  - [x] 7.1 实现 TTS 服务基类（src/pillow_talk/tts/base.py）

    - 定义 TTSInterface 抽象基类
    - 定义 synthesize 抽象方法：接受文本、语音类型、语速、语言，返回音频数据
    - 添加类型注解和文档字符串
    - _Requirements: 5.2_



  - [ ] 7.2 实现 OpenAI TTS 服务（src/pillow_talk/tts/openai_tts.py）
    - 实现 OpenAITTSService 类，继承 TTSInterface
    - 实现 synthesize 方法：调用 OpenAI TTS API
    - 支持男声和女声选项
    - 支持语速调整（0.5x - 2.0x）
    - 返回 MP3 格式音频
    - 设置 10 秒超时


    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 5.10_

  - [ ] 7.3 实现 Google TTS 服务（src/pillow_talk/tts/google_tts.py）
    - 实现 GoogleTTSService 类，继承 TTSInterface


    - 适配 Google Cloud TTS API
    - 支持中文和英文语音合成
    - _Requirements: 5.1, 5.9_



  - [ ] 7.4 实现 Azure TTS 服务（src/pillow_talk/tts/azure_tts.py）
    - 实现 AzureTTSService 类，继承 TTSInterface
    - 适配 Microsoft Azure TTS API
    - 支持中文和英文语音合成


    - _Requirements: 5.1, 5.9_

  - [ ] 7.5 实现 Edge TTS 服务（src/pillow_talk/tts/edge_tts.py）
    - 实现 EdgeTTSService 类，继承 TTSInterface


    - 适配 Edge TTS API
    - 支持中文和英文语音合成
    - _Requirements: 5.1, 5.9_

  - [ ] 7.6 实现阿里云 TTS 服务（src/pillow_talk/tts/ali_tts.py）
    - 实现 AliTTSService 类，继承 TTSInterface
    - 适配阿里云 TTS API
    - 支持中文和英文语音合成
    - _Requirements: 5.1, 5.9_

  - [ ] 7.7 实现 TTS 服务工厂（src/pillow_talk/tts/__init__.py）
    - 实现 TTSServiceFactory 类
    - 实现 create_service 方法：根据 provider 创建对应的 TTS 服务实例
    - 处理不支持的 provider 错误
    - _Requirements: 5.1_

  - [ ]* 7.8 编写 TTS 服务单元测试
    - 测试各 TTS 服务的音频生成


    - 测试语音类型和语速参数
    - 测试错误处理
    - 测试工厂模式的服务创建
    - _Requirements: 5.2, 5.3, 5.5, 5.6_



- [ ] 8. Checkpoint - 适配层验证
  - 运行所有适配器和 TTS 服务的单元测试
  - 确保模型适配器和 TTS 服务功能正常
  - 如有问题，请向用户反馈


- [ ] 9. 安全和限流服务
  - [ ] 9.1 实现认证服务（src/pillow_talk/services/auth.py）
    - 实现 AuthenticationService 类
    - 使用 Fernet（AES-256）实现 encrypt_api_key 和 decrypt_api_key 方法
    - 实现 validate_request 方法：验证 API Key
    - 从环境变量加载加密密钥
    - _Requirements: 9.2, 9.8_

  - [ ] 9.2 实现限流服务（src/pillow_talk/services/rate_limit.py）
    - 实现 RateLimiter 类，使用滑动窗口算法
    - 实现 check_rate_limit 方法：检查 IP 和 API Key 的请求频率
    - 限制单个 IP 每分钟最多 60 个请求
    - 限制单个 API Key 每分钟最多 100 个请求
    - 实现 cleanup_expired 方法：清理过期记录
    - 使用 asyncio.Lock 保证线程安全
    - _Requirements: 9.5, 9.6, 9.7_

  - [ ]* 9.3 编写安全服务单元测试
    - 测试 API Key 加密和解密
    - 测试限流逻辑（正常请求、超限请求）
    - 测试滑动窗口的正确性
    - _Requirements: 9.2, 9.5, 9.6_

- [x] 10. API 网关和路由
  - [x] 10.1 实现 API 依赖注入（src/pillow_talk/api/dependencies.py）
    - 实现 get_settings 依赖：返回应用配置
    - 实现 get_logger 依赖：返回日志记录器
    - 实现 get_conversation_manager 依赖：返回对话管理器单例
    - 实现 get_auth_service 依赖：返回认证服务单例
    - 实现 get_rate_limiter 依赖：返回限流器单例
    - 实现 get_request_id 依赖：生成唯一的 request_id（UUID）
    - _Requirements: 13.1_

  - [x] 10.2 实现中间件（src/pillow_talk/api/middleware.py）
    - 实现请求日志中间件：记录所有请求和响应
    - 实现 CORS 中间件：配置允许的来源
    - 实现异常处理中间件：捕获未处理的异常并返回标准错误响应
    - 实现请求追踪中间件：为每个请求添加 request_id
    - _Requirements: 9.1, 13.1, 13.2, 13.6_

  - [x] 10.3 实现 API 路由（src/pillow_talk/api/routes.py）
    - 实现 POST /api/v1/chat 端点
      - 接受 ChatRequest，返回 ChatResponse 或 SSE 流
      - 调用认证服务验证请求
      - 调用限流器检查请求频率
      - 调用图像预处理器处理图像
      - 调用对话管理器获取或创建对话
      - 调用 Prompt 引擎组装消息
      - 调用模型适配器处理图像
      - 调用 TTS 服务生成音频
      - 记录请求指标（各阶段耗时）
      - 处理流式和非流式响应
    - 实现 POST /api/v1/test-connection 端点
      - 接受 TestConnectionRequest，返回 TestConnectionResponse
      - 创建临时适配器并测试连接
      - 记录连接延迟
    - 实现 GET /api/v1/models 端点
      - 返回支持的模型列表
    - 实现 GET /health 端点
      - 返回服务健康状态
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 15.3_

  - [ ]* 10.4 编写 API 路由集成测试
    - 测试 /api/v1/chat 端点（流式和非流式）
    - 测试 /api/v1/test-connection 端点
    - 测试 /api/v1/models 端点
    - 测试错误处理（无效请求、超限、超时）
    - 测试认证和限流
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_


- [x] 11. FastAPI 应用入口
  - [x] 11.1 实现应用主入口（src/pillow_talk/main.py）
    - 创建 FastAPI 应用实例
    - 配置 CORS 中间件
    - 注册所有路由
    - 注册中间件（日志、异常处理、请求追踪）
    - 实现启动事件：初始化日志、验证环境变量、启动后台任务（清理过期对话和限流记录）
    - 实现关闭事件：清理资源
    - 配置 OpenAPI 文档
    - _Requirements: 7.8, 15.4, 15.6, 15.7_

  - [ ]* 11.2 编写应用启动测试
    - 测试应用启动和关闭流程
    - 测试环境变量验证
    - 测试健康检查端点
    - _Requirements: 15.4, 15.6, 15.7_

- [ ] 12. 部署配置
  - [x] 12.1 创建 Dockerfile
    - 使用 Python 3.11+ 基础镜像
    - 安装 Poetry
    - 复制项目文件并安装依赖
    - 配置工作目录和入口点
    - 暴露 8000 端口
    - _Requirements: 15.1_

  - [x] 12.2 创建 docker-compose.yml
    - 配置后端服务
    - 配置环境变量
    - 配置端口映射
    - 配置卷挂载（日志目录）
    - _Requirements: 15.2_

  - [x] 12.3 创建 Makefile
    - 添加 make install 命令：安装依赖
    - 添加 make test 命令：运行测试
    - 添加 make lint 命令：运行 ruff 检查


    - 添加 make format 命令：运行 ruff 格式化
    - 添加 make type-check 命令：运行 mypy 类型检查
    - 添加 make run 命令：启动开发服务器
    - 添加 make docker-build 命令：构建 Docker 镜像
    - 添加 make docker-run 命令：运行 Docker 容器
    - _Requirements: 15.5_

  - [x] 12.4 配置 pre-commit hooks
    - 创建 .pre-commit-config.yaml
    - 配置 ruff 格式化和 linting
    - 配置 mypy 类型检查
    - 配置 pytest 测试
    - _Requirements: 10.10_

  - [x] 12.5 创建 README.md
    - 添加项目简介
    - 添加功能特性列表
    - 添加快速开始指南
    - 添加 API 文档链接
    - 添加配置说明
    - 添加部署指南
    - 添加开发指南

- [ ] 13. Checkpoint - 完整系统测试
  - 运行所有单元测试和集成测试
  - 使用 make lint 检查代码质量
  - 使用 make type-check 检查类型注解
  - 确保测试覆盖率 >= 80%
  - 如有问题，请向用户反馈


- [ ] 14. 文档和最终优化
  - [ ] 14.1 添加代码文档字符串
    - 为所有公共模块、类和函数添加 Google Style 文档字符串
    - 确保所有公共 API 都有清晰的文档
    - _Requirements: 10.11_

  - [ ] 14.2 性能优化验证
    - 验证图像处理时间 < 500ms
    - 验证 TTFB < 5 秒（网络条件良好时 < 3 秒）
    - 验证 TTS 首字延迟 < 3 秒
    - 验证系统支持 100 QPS 并发
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 14.3 安全性检查
    - 验证所有通信使用 HTTPS
    - 验证 API Key 加密存储
    - 验证图像数据不持久化
    - 验证输入参数验证和注入防护
    - 验证 Prompt 注入防护
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.8, 9.9_

  - [ ] 14.4 日志和监控验证
    - 验证所有日志包含 request_id
    - 验证日志级别正确使用
    - 验证错误日志包含堆栈跟踪
    - 验证请求指标记录完整
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ] 14.5 创建示例配置文件
    - 更新 .env.example，包含所有必需的环境变量
    - 添加配置说明注释
    - 提供示例值
    - _Requirements: 15.6, 15.7_

- [ ] 15. 最终验收测试
  - 使用 Docker 部署完整系统
  - 测试所有 API 端点的功能
  - 测试多个模型提供商的集成
  - 测试多个 TTS 服务的集成
  - 测试流式和非流式响应
  - 测试多轮对话功能
  - 测试错误处理和恢复
  - 测试限流和认证
  - 验证日志输出格式
  - 确保所有需求得到满足

## Notes

- 任务标记 `*` 的为可选任务（主要是测试相关），可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，便于追溯
- Checkpoint 任务用于阶段性验证，确保增量开发的正确性
- 建议按顺序执行任务，因为后续任务依赖前面任务的输出
- 所有代码必须包含类型注解和文档字符串
- 所有公共 API 必须有单元测试
- 核心业务逻辑必须达到 80% 以上的测试覆盖率

## Implementation Guidelines

1. **代码风格**：严格遵循 PEP 8，使用 ruff 进行格式化和 linting
2. **类型注解**：所有公共函数必须包含完整的类型注解，使用 mypy 进行类型检查
3. **异步编程**：所有 I/O 操作使用 asyncio 和 httpx 进行异步处理
4. **错误处理**：使用自定义异常类，提供清晰的错误消息和建议
5. **日志记录**：使用 structlog 记录结构化日志，禁止使用 print 语句
6. **测试**：使用 pytest 编写测试，使用 pytest-asyncio 测试异步代码
7. **依赖注入**：使用 FastAPI 的依赖注入系统管理服务实例
8. **配置管理**：使用 pydantic-settings 管理环境变量和配置
9. **安全性**：所有敏感数据加密存储，所有输入参数验证
10. **性能**：关注响应时间和并发能力，使用异步 I/O 和流式传输优化性能


---

## React Native 移动端实现

### 移动端概述

移动端采用 React Native + TypeScript 架构，支持 iOS 15.0+ 和 Android 10.0+ 设备。实现将遵循 React Native 最佳实践，使用 Expo 或原生模块进行摄像头和音频功能集成。

移动端实现策略：
1. 首先搭建项目基础架构和导航
2. 实现摄像头功能和图像处理
3. 实现 API 客户端和状态管理
4. 实现对话界面和音频播放
5. 实现配置管理和模型选择
6. 实现 Prompt 管理和定制
7. 实现历史记录功能
8. 添加错误处理和加载状态
9. 优化性能和用户体验

## 移动端任务

- [x] 16. React Native 项目初始化
  - 使用 React Native CLI 或 Expo 初始化项目
  - 配置 TypeScript 支持
  - 添加核心依赖：react-navigation、axios、react-native-camera（或 expo-camera）、react-native-sound（或 expo-av）、@react-native-async-storage/async-storage
  - 配置 ESLint 和 Prettier
  - 创建项目目录结构（src/screens、src/components、src/services、src/hooks、src/types、src/utils）
  - 配置 iOS 和 Android 权限（摄像头、麦克风）
  - _Requirements: 11.7_


- [x] 17. 类型定义和数据模型
  - [x] 17.1 创建 TypeScript 类型定义（src/types/index.ts）
    - 定义 ModelProvider 枚举
    - 定义 ChatRequest、ChatResponse、ChatData 接口
    - 定义 CustomModelConfig、TestConnectionRequest、TestConnectionResponse 接口
    - 定义 PromptTemplate、ModelInfo 接口
    - 定义 ConversationHistory、Message 接口
    - 定义 AppConfig、TTSConfig 接口
    - _Requirements: 7.2, 7.3, 7.5, 3.1, 2.1_

  - [ ]* 17.2 编写类型定义单元测试
    - 测试类型推断和类型安全
    - _Requirements: 11.7_

- [x] 18. API 客户端实现
  - [x] 18.1 实现 API 客户端基础类（src/services/api.ts）
    - 创建 ApiClient 类，使用 axios 进行 HTTP 请求
    - 配置 baseURL、timeout（30 秒）、headers
    - 实现请求拦截器：添加认证 token、request_id
    - 实现响应拦截器：统一错误处理、日志记录
    - 实现重试逻辑（最多 3 次）
    - _Requirements: 7.8, 9.1, 13.1_


  - [x] 18.2 实现对话 API 方法（src/services/chatService.ts）
    - 实现 sendChatRequest 方法：发送图像和 Prompt 到后端
    - 实现 sendStreamingChatRequest 方法：处理 SSE 流式响应
    - 实现 testConnection 方法：测试模型连接
    - 实现 getModels 方法：获取支持的模型列表
    - 处理网络错误和超时
    - _Requirements: 7.1, 7.2, 7.3, 7.6, 7.7, 4.3_

  - [ ]* 18.3 编写 API 客户端单元测试
    - 测试请求和响应处理
    - 测试错误处理和重试逻辑
    - 测试流式响应解析
    - Mock axios 进行测试
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 19. 配置管理和本地存储
  - [x] 19.1 实现配置管理服务（src/services/configService.ts）
    - 使用 AsyncStorage 实现配置持久化
    - 实现 saveModelConfig 方法：保存模型配置
    - 实现 loadModelConfig 方法：加载模型配置
    - 实现 savePromptTemplate 方法：保存自定义 Prompt
    - 实现 loadPromptTemplates 方法：加载 Prompt 模板
    - 实现 encryptApiKey 和 decryptApiKey 方法：使用设备加密存储 API Key
    - _Requirements: 2.8, 3.7, 9.2_


  - [x] 19.2 实现历史记录服务（src/services/historyService.ts）
    - 实现 saveConversation 方法：保存对话记录
    - 实现 loadConversations 方法：加载最近 50 次对话
    - 实现 deleteConversation 方法：删除指定对话
    - 实现 clearHistory 方法：清空所有历史记录
    - 使用 AsyncStorage 持久化存储
    - _Requirements: 11.5, 11.6_

  - [ ]* 19.3 编写配置管理单元测试
    - 测试配置的保存和加载
    - 测试 API Key 加密和解密
    - 测试历史记录的 CRUD 操作
    - Mock AsyncStorage 进行测试
    - _Requirements: 2.8, 3.7_

- [x] 20. Checkpoint - 基础服务验证
  - 运行所有基础服务的单元测试
  - 确保 API 客户端、配置管理、历史记录服务功能正常
  - 如有问题，请向用户反馈

- [x] 21. 摄像头功能实现
  - [x] 21.1 实现摄像头组件（src/components/CameraView.tsx）
    - 使用 react-native-camera 或 expo-camera
    - 实现全屏相机预览
    - 实现自动对焦功能
    - 实现拍照按钮和拍照功能
    - 在 500 毫秒内捕获图像
    - 处理摄像头权限请求
    - 显示权限说明和引导
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1_


  - [x] 21.2 实现图像预处理工具（src/utils/imageProcessor.ts）
    - 实现 compressImage 函数：压缩图像至 1MB 以下
    - 实现 convertToBase64 函数：转换图像为 Base64 编码
    - 使用 react-native-image-resizer 或类似库
    - 确保处理时间 < 500ms
    - 保持图像质量（JPEG 质量 >= 85）
    - _Requirements: 1.6, 1.7, 1.8, 12.3_

  - [ ]* 21.3 编写摄像头功能单元测试
    - 测试图像压缩功能
    - 测试 Base64 编码
    - 测试权限处理
    - _Requirements: 1.6, 1.7, 1.8_

- [x] 22. 导航和路由
  - [x] 22.1 实现导航结构（src/navigation/AppNavigator.tsx）
    - 使用 react-navigation 配置导航
    - 创建 Stack Navigator
    - 定义路由：CameraScreen、ChatScreen、SettingsScreen、HistoryScreen、PromptEditorScreen
    - 配置导航动画和过渡效果
    - 适配刘海屏和灵动岛设计
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.8_

  - [x] 22.2 实现底部操作栏组件（src/components/ActionBar.tsx）
    - 显示拍照按钮、模型选择按钮、Prompt 选择按钮
    - 实现按钮点击事件处理
    - 适配不同屏幕尺寸
    - _Requirements: 11.2_


- [x] 23. 对话界面实现
  - [x] 23.1 实现对话屏幕（src/screens/ChatScreen.tsx）
    - 显示 AI 生成的文本内容
    - 实现消息列表滚动
    - 显示用户拍摄的图像缩略图
    - 实现"继续对话"和"新对话"按钮
    - 显示加载指示器
    - 处理错误状态和重试选项


    - _Requirements: 11.3, 11.9, 11.10, 6.6_

  - [x] 23.2 实现流式文本显示组件（src/components/StreamingText.tsx）
    - 实时显示流式文本 token
    - 实现打字机效果动画


    - 支持文本滚动
    - _Requirements: 4.3_

  - [x] 23.3 实现音频播放组件（src/components/AudioPlayer.tsx）
    - 使用 react-native-sound 或 expo-av
    - 显示语音播放波形动画
    - 实现播放、暂停、重播按钮
    - 在 100 毫秒内响应暂停操作



    - 显示播放进度
    - 支持语速调整（0.5x - 2.0x）
    - _Requirements: 5.5, 5.6, 5.7, 5.8, 11.4_

  - [ ]* 23.4 编写对话界面单元测试
    - 测试消息显示和滚动
    - 测试音频播放控制
    - 测试错误处理
    - _Requirements: 11.3, 11.4_


- [ ] 24. 模型配置界面
  - [ ] 24.1 实现设置屏幕（src/screens/SettingsScreen.tsx）
    - 显示预设模型列表：OpenAI GPT-4o、GPT-4V、Gemini 2.5 Pro、Claude 4.5 Sonnet、豆包
    - 实现模型选择功能
    - 显示当前选中的模型
    - 提供"添加自定义模型"入口
    - _Requirements: 2.1, 2.2, 11.2_



  - [ ] 24.2 实现模型配置表单（src/components/ModelConfigForm.tsx）
    - 输入字段：Base URL、API Key、Model Name
    - 支持自定义 HTTP Header
    - 实现表单验证
    - 实现"测试连接"按钮


    - 在 10 秒内返回测试结果
    - 显示连接成功或失败消息
    - 显示具体错误信息和建议
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ] 24.3 实现 TTS 配置组件（src/components/TTSConfigForm.tsx）
    - 选择 TTS 提供商：OpenAI、Google、Azure、Edge、阿里云
    - 选择语音类型（男声/女声）
    - 调整语速（0.5x - 2.0x）
    - 保存 TTS 配置
    - _Requirements: 5.1, 5.5, 5.6_

  - [ ]* 24.4 编写模型配置界面单元测试
    - 测试表单验证
    - 测试连接测试功能


    - 测试配置保存
    - _Requirements: 2.3, 2.4, 2.5, 2.6_


- [ ] 25. Checkpoint - UI 组件验证
  - 运行所有 UI 组件的单元测试
  - 在 iOS 和 Android 模拟器上测试界面显示


  - 确保摄像头、对话界面、配置界面功能正常
  - 如有问题，请向用户反馈

- [ ] 26. Prompt 管理功能
  - [ ] 26.1 实现 Prompt 选择器（src/components/PromptSelector.tsx）
    - 显示内置 Prompt 模板列表：博物馆讲解员、可爱宠物、科普专家、毒舌评论家、温柔陪伴者
    - 显示自定义 Prompt 列表
    - 实现 Prompt 快速切换
    - 在 200 毫秒内更新界面
    - 提供"创建自定义 Prompt"入口
    - _Requirements: 3.1, 3.4, 3.5_


  - [x] 26.2 实现 Prompt 编辑器（src/screens/PromptEditorScreen.tsx）

    - 提供文本编辑界面
    - 支持最多 2000 个字符
    - 显示字符计数
    - 实现保存和取消按钮
    - 验证 Prompt 内容
    - 本地持久化存储
    - _Requirements: 3.2, 3.3, 3.7_


  - [ ]* 26.3 编写 Prompt 管理单元测试
    - 测试 Prompt 切换功能
    - 测试自定义 Prompt 创建和保存
    - 测试字符限制验证
    - _Requirements: 3.2, 3.3, 3.4, 3.5_


- [ ] 27. 历史记录功能
  - [ ] 27.1 实现历史记录屏幕（src/screens/HistoryScreen.tsx）
    - 显示最近 50 次扫描和对话记录
    - 显示每条记录的缩略图、时间戳、摘要
    - 实现列表滚动和下拉刷新
    - 实现点击查看详情功能
    - 实现删除单条记录功能
    - 实现清空所有历史记录功能


    - _Requirements: 11.5, 11.6_

  - [ ] 27.2 实现历史详情组件（src/components/HistoryDetail.tsx）
    - 显示完整的对话内容
    - 显示原始图像



    - 显示使用的模型和 Prompt
    - 支持重播音频
    - 提供"继续对话"选项
    - _Requirements: 11.6_

  - [ ]* 27.3 编写历史记录单元测试
    - 测试历史记录的加载和显示
    - 测试删除功能
    - 测试详情查看
    - _Requirements: 11.5, 11.6_

- [ ] 28. 状态管理
  - [ ] 28.1 实现全局状态管理（src/store/index.ts）
    - 使用 React Context 或 Redux/Zustand
    - 定义全局状态：currentModel、currentPrompt、conversationId、isLoading、error



    - 实现状态更新 actions
    - 实现状态持久化（AsyncStorage）
    - _Requirements: 2.2, 3.4, 6.1_




  - [ ] 28.2 实现自定义 Hooks（src/hooks/）
    - 实现 useCamera Hook：管理摄像头状态和权限
    - 实现 useChat Hook：管理对话状态和 API 调用

    - 实现 useAudioPlayer Hook：管理音频播放状态
    - 实现 useConfig Hook：管理配置状态
    - 实现 useHistory Hook：管理历史记录状态
    - _Requirements: 1.1, 4.1, 5.7, 2.2, 11.5_

  - [ ]* 28.3 编写状态管理单元测试
    - 测试状态更新逻辑
    - 测试自定义 Hooks
    - 测试状态持久化
    - _Requirements: 2.2, 3.4, 6.1_

- [ ] 29. 错误处理和用户反馈
  - [ ] 29.1 实现错误处理工具（src/utils/errorHandler.ts）
    - 定义错误类型枚举
    - 实现 parseApiError 函数：解析后端错误响应
    - 实现 getUserFriendlyMessage 函数：转换为用户友好的错误消息
    - 实现错误日志记录
    - _Requirements: 13.9, 11.10_

  - [ ] 29.2 实现加载和错误组件（src/components/）
    - 实现 LoadingIndicator 组件：显示加载动画
    - 实现 ErrorMessage 组件：显示错误消息和重试按钮
    - 实现 Toast 组件：显示临时提示消息
    - 适配不同屏幕尺寸
    - _Requirements: 11.9, 11.10_


  - [ ]* 29.3 编写错误处理单元测试
    - 测试错误解析逻辑
    - 测试用户友好消息生成
    - 测试错误组件显示
    - _Requirements: 13.9, 11.10_

- [ ] 30. Checkpoint - 完整功能测试
  - 运行所有移动端单元测试
  - 在 iOS 和 Android 设备上进行端到端测试
  - 测试完整的用户流程：拍照 -> 识别 -> 语音播放 -> 多轮对话
  - 测试错误场景和边界情况
  - 如有问题，请向用户反馈

- [x] 31. 性能优化
  - [x] 31.1 实现图像缓存（src/utils/imageCache.ts）
    - 缓存最近拍摄的图像（最多 10 张）
    - 实现 LRU 缓存策略
    - 自动清理过期缓存
    - _Requirements: 12.8_

  - [x] 31.2 实现音频缓存（src/utils/audioCache.ts）
    - 缓存最近播放的音频文件（最多 10 个）
    - 实现 LRU 缓存策略
    - 自动清理过期缓存
    - _Requirements: 12.8_

  - [ ] 31.3 优化列表渲染性能


    - 使用 FlatList 的 virtualization 功能
    - 实现 memo 和 useMemo 优化组件渲染
    - 优化图像加载和显示
    - _Requirements: 11.5, 12.8_


  - [ ]* 31.4 性能测试和验证
    - 验证图像处理时间 < 500ms
    - 验证界面响应时间 < 200ms
    - 验证音频暂停响应 < 100ms
    - 使用 React Native Performance Monitor 监控性能
    - _Requirements: 1.5, 3.5, 5.7, 12.3_

- [x] 32. 安全性实现





  - [ ] 32.1 实现 API Key 安全存储（src/utils/secureStorage.ts）
    - 使用 react-native-keychain 或 expo-secure-store
    - 实现 saveApiKey 和 getApiKey 方法
    - 使用设备加密存储（AES-256）


    - _Requirements: 2.8, 9.2_

  - [ ] 32.2 实现 HTTPS 通信验证
    - 配置 axios 使用 HTTPS
    - 实现证书固定（可选）
    - 验证所有 API 请求使用 HTTPS
    - _Requirements: 7.8, 9.1_






  - [ ]* 32.3 安全性测试
    - 测试 API Key 加密存储
    - 测试 HTTPS 通信
    - 测试敏感数据不在日志中泄露
    - _Requirements: 2.8, 9.1, 9.2_

- [ ] 33. 国际化和本地化
  - [ ] 33.1 实现多语言支持（src/i18n/）
    - 使用 react-i18next 或 react-native-localize
    - 创建中文和英文语言包
    - 实现语言切换功能
    - 翻译所有界面文本和错误消息
    - _Requirements: 5.9, 11.10_


  - [ ]* 33.2 本地化测试
    - 测试中英文切换
    - 测试所有文本的翻译完整性
    - _Requirements: 5.9_

- [ ] 34. 主屏幕和相机集成
  - [ ] 34.1 实现主屏幕（src/screens/CameraScreen.tsx）
    - 集成 CameraView 组件
    - 集成 ActionBar 组件
    - 实现拍照后的导航逻辑
    - 显示当前选中的模型和 Prompt
    - 实现设置和历史记录入口
    - _Requirements: 11.1, 11.2_

  - [ ] 34.2 实现完整的拍照到对话流程
    - 拍照 -> 图像预处理 -> 发送请求 -> 显示响应 -> 播放音频
    - 处理每个步骤的加载状态
    - 处理每个步骤的错误情况
    - 实现流式响应的实时显示
    - _Requirements: 1.5, 1.6, 1.7, 4.1, 4.3, 5.2_

  - [ ]* 34.3 集成测试
    - 测试完整的用户流程
    - 测试不同模型和 Prompt 的组合
    - 测试网络异常情况
    - _Requirements: 1.5, 4.1, 4.3_

- [ ] 35. Checkpoint - 移动端完整测试
  - 在真实 iOS 设备上测试（iOS 15.0+）
  - 在真实 Android 设备上测试（Android 10.0+）
  - 测试不同屏幕尺寸和分辨率

  - 测试刘海屏和灵动岛适配
  - 测试所有功能的完整性
  - 验证性能指标
  - 如有问题，请向用户反馈


- [ ] 36. 移动端文档和配置
  - [ ] 36.1 创建移动端 README.md
    - 添加项目简介
    - 添加功能特性列表
    - 添加开发环境设置指南
    - 添加构建和运行指南（iOS 和 Android）
    - 添加配置说明
    - 添加故障排除指南

  - [ ] 36.2 配置 iOS 构建
    - 配置 Info.plist 权限说明
    - 配置 App Icons 和 Launch Screen
    - 配置 Bundle Identifier
    - 配置签名和证书
    - _Requirements: 11.7_




  - [ ] 36.3 配置 Android 构建
    - 配置 AndroidManifest.xml 权限
    - 配置 App Icons 和 Splash Screen
    - 配置 Package Name
    - 配置签名密钥
    - _Requirements: 11.7_

  - [ ] 36.4 创建环境配置文件
    - 创建 .env.example 文件
    - 定义 API_BASE_URL、DEFAULT_MODEL、DEFAULT_TTS_PROVIDER 等环境变量
    - 添加配置说明注释
    - _Requirements: 7.8_

- [ ] 37. 最终集成和验收测试
  - 部署后端服务到测试环境
  - 配置移动端连接到测试环境
  - 测试完整的端到端流程
  - 测试所有模型提供商的集成
  - 测试所有 TTS 服务的集成
  - 测试多轮对话功能
  - 测试历史记录功能
  - 测试自定义 Prompt 功能
  - 测试错误处理和恢复
  - 验证性能指标（TTFB < 5 秒、图像处理 < 500ms、音频暂停 < 100ms）
  - 验证安全性（HTTPS、API Key 加密）
  - 确保所有移动端需求得到满足


## 移动端实现指南

1. **技术选型**：
   - 推荐使用 Expo 进行快速开发，或使用 React Native CLI 获得更多原生控制
   - 使用 TypeScript 确保类型安全
   - 使用 React Navigation 5+ 进行导航管理
   - 使用 Axios 进行 HTTP 请求
   - 使用 AsyncStorage 或 MMKV 进行本地存储

2. **代码风格**：
   - 遵循 React Native 最佳实践
   - 使用函数组件和 Hooks
   - 使用 ESLint 和 Prettier 保持代码一致性
   - 所有组件和函数必须包含 TypeScript 类型注解
   - 使用有意义的变量和函数命名

3. **组件设计**：
   - 遵循单一职责原则
   - 创建可复用的 UI 组件
   - 使用 React.memo 优化性能
   - 避免过度嵌套

4. **状态管理**：
   - 优先使用 React Context 和 Hooks
   - 对于复杂状态可以考虑 Redux Toolkit 或 Zustand
   - 避免 prop drilling

5. **测试**：
   - 使用 Jest 和 React Native Testing Library
   - 编写单元测试覆盖核心逻辑
   - 使用 Detox 进行 E2E 测试（可选）

6. **性能优化**：
   - 使用 FlatList 的 virtualization
   - 实现图像和音频缓存
   - 避免不必要的重新渲染
   - 使用 React DevTools Profiler 分析性能

7. **安全性**：
   - 使用 react-native-keychain 或 expo-secure-store 存储敏感数据
   - 所有 API 请求使用 HTTPS
   - 不在日志中记录敏感信息
   - 实现证书固定（生产环境）

8. **用户体验**：
   - 提供清晰的加载状态
   - 提供友好的错误消息
   - 实现流畅的动画和过渡
   - 适配不同屏幕尺寸和设备
   - 支持深色模式（可选）

9. **调试和监控**：
   - 使用 React Native Debugger
   - 集成 Sentry 或类似工具进行错误监控（可选）
   - 实现日志记录系统
   - 使用 Flipper 进行网络和性能调试

10. **发布准备**：
    - 配置 App Icons 和 Splash Screens
    - 优化 Bundle 大小
    - 配置 Code Push 进行热更新（可选）
    - 准备 App Store 和 Google Play 发布材料
