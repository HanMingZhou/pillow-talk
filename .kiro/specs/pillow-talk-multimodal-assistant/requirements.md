# Requirements Document

## Introduction

Pillow Talk 是一款基于多模态大语言模型（MLLM）的智能视觉语音助手。用户通过移动设备摄像头扫描现实物体，系统利用 AI 进行视觉理解，并根据预设 Prompt 生成自然的语音对话输出。系统由移动端应用（React Native + TypeScript）和后端服务（Python + FastAPI）组成，支持多家云厂商模型及用户自定义模型接入。

## Glossary

- **Mobile_App**: React Native 移动端应用，运行在 iOS 和 Android 设备上
- **Backend_Service**: Python FastAPI 后端服务，处理图像识别和语音合成
- **Camera_Module**: 移动端摄像头模块，负责图像采集和预处理
- **Model_Adapter**: 后端模型适配层，统一不同厂商的多模态模型接口
- **TTS_Service**: 文本转语音服务，将 AI 生成的文本转换为语音
- **Prompt_Engine**: Prompt 管理引擎，组装和管理对话上下文
- **API_Gateway**: 后端 API 网关，处理客户端请求
- **Configuration_Manager**: 配置管理器，管理模型和 TTS 配置
- **Image_Preprocessor**: 图像预处理器，压缩和转换图像格式
- **Audio_Player**: 音频播放器，播放 TTS 生成的语音
- **Conversation_Manager**: 对话管理器，维护多轮对话上下文
- **Authentication_Service**: 认证服务，管理 API 密钥和访问控制
- **Rate_Limiter**: 限流器，控制 API 请求频率
- **Parser**: 解析器，解析模型响应和配置文件
- **Pretty_Printer**: 格式化输出器，格式化数据结构为可读格式

## Requirements

### Requirement 1: 图像采集与预处理

**User Story:** 作为用户，我希望通过移动设备摄像头扫描物体，以便系统能够识别并理解我看到的内容。

#### Acceptance Criteria

1. WHEN THE Mobile_App 启动时，THE Camera_Module SHALL 请求摄像头权限
2. IF 用户拒绝摄像头权限，THEN THE Mobile_App SHALL 显示权限说明并引导用户到设置页面
3. WHEN 摄像头权限被授予时，THE Camera_Module SHALL 显示实时预览画面
4. THE Camera_Module SHALL 支持自动对焦功能
5. WHEN 用户点击拍照按钮时，THE Camera_Module SHALL 在 500 毫秒内捕获图像
6. WHEN 图像被捕获时，THE Image_Preprocessor SHALL 将图像压缩至 1MB 以下
7. WHEN 图像被压缩时，THE Image_Preprocessor SHALL 转换图像为 Base64 编码格式
8. FOR ALL 捕获的图像，压缩后的图像质量 SHALL 保持足够清晰以供模型识别（JPEG 质量 >= 85）

### Requirement 2: 多模态模型配置

**User Story:** 作为用户，我希望能够选择不同的 AI 模型提供商，以便根据我的需求和预算选择最合适的服务。

#### Acceptance Criteria

1. THE Configuration_Manager SHALL 支持以下预设模型：OpenAI GPT-4o、OpenAI GPT-4V、Google Gemini 2.5 Pro、Anthropic Claude 4.5 Sonnet、豆包 doubao-seedance-2-0-260128
2. WHEN 用户选择预设模型时，THE Mobile_App SHALL 显示该模型的配置界面
3. THE Configuration_Manager SHALL 允许用户输入自定义模型的 Base URL、API Key 和 Model Name
4. WHERE 用户配置自定义模型时，THE Configuration_Manager SHALL 支持自定义 HTTP Header 和 Token 认证方式
5. WHEN 用户完成模型配置时，THE Mobile_App SHALL 提供"测试连接"功能
6. WHEN 用户触发测试连接时，THE Backend_Service SHALL 在 10 秒内返回连接测试结果
7. IF 模型连接失败，THEN THE Mobile_App SHALL 显示具体的错误信息和建议解决方案
8. THE Configuration_Manager SHALL 在本地安全存储用户的 API Key（使用设备加密存储）

### Requirement 3: Prompt 管理与定制

**User Story:** 作为用户，我希望能够自定义 AI 的对话风格和人设，以便获得个性化的交互体验。

#### Acceptance Criteria

1. THE Prompt_Engine SHALL 提供至少 5 个内置 Prompt 模板（如博物馆讲解员、可爱宠物、科普专家、毒舌评论家、温柔陪伴者）
2. THE Mobile_App SHALL 允许用户创建和保存自定义 System Prompt
3. WHEN 用户创建自定义 Prompt 时，THE Mobile_App SHALL 提供文本编辑界面，支持最多 2000 个字符
4. THE Prompt_Engine SHALL 支持用户在不同 Prompt 模式之间快速切换
5. WHEN 用户切换 Prompt 模式时，THE Mobile_App SHALL 在 200 毫秒内更新界面显示
6. THE Prompt_Engine SHALL 在发送请求时将 System Prompt 和用户图像组装为符合所选模型格式的消息结构
7. THE Mobile_App SHALL 在本地持久化存储用户的自定义 Prompt 配置

### Requirement 4: 视觉理解与对话生成

**User Story:** 作为用户，我希望系统能够准确识别图像内容并生成自然的对话回复，以便与我进行有意义的交互。

#### Acceptance Criteria

1. WHEN THE Backend_Service 接收到图像和 Prompt 时，THE Model_Adapter SHALL 路由请求到用户选择的模型提供商
2. THE Model_Adapter SHALL 在 5 秒内返回首个文本 token（TTFB < 5 秒）
3. WHERE 模型支持流式输出时，THE Model_Adapter SHALL 使用 Server-Sent Events（SSE）进行流式传输
4. WHEN 模型返回响应时，THE Backend_Service SHALL 记录请求处理延迟到日志系统
5. IF 模型调用超时（> 30 秒），THEN THE Backend_Service SHALL 返回超时错误并建议用户重试
6. IF 模型返回错误响应，THEN THE Backend_Service SHALL 解析错误信息并返回用户友好的错误描述
7. THE Model_Adapter SHALL 支持并发处理至少 100 个请求（QPS >= 100）
8. FOR ALL 模型响应，THE Backend_Service SHALL 验证响应格式的有效性

### Requirement 5: 文本转语音服务

**User Story:** 作为用户，我希望 AI 的回复能够以自然的语音播放，以便获得更沉浸的交互体验。

#### Acceptance Criteria

1. THE TTS_Service SHALL 支持以下语音服务：OpenAI TTS、Google Cloud TTS、Microsoft Azure TTS、Edge TTS、阿里云 TTS
2. WHEN THE Backend_Service 生成文本响应时，THE TTS_Service SHALL 将文本转换为音频格式（MP3 或 AAC）
3. THE TTS_Service SHALL 在 3 秒内生成首个音频片段（首字延迟 < 3 秒）
4. WHERE TTS 服务支持流式输出时，THE TTS_Service SHALL 使用流式传输优化播放延迟
5. THE Audio_Player SHALL 支持男声和女声选项
6. THE Audio_Player SHALL 支持语速调整（0.5x 至 2.0x）
7. WHEN 用户点击暂停按钮时，THE Audio_Player SHALL 在 100 毫秒内暂停播放
8. THE Audio_Player SHALL 支持重播功能
9. THE TTS_Service SHALL 支持中文和英文语音合成
10. WHEN 音频生成完成时，THE Backend_Service SHALL 返回音频文件的 URL 或 Base64 编码数据

### Requirement 6: 多轮对话上下文管理

**User Story:** 作为用户，我希望能够与识别的物体进行连续对话，以便进行更深入的交流。

#### Acceptance Criteria

1. THE Conversation_Manager SHALL 为每个对话会话生成唯一的 conversation_id（UUID 格式）
2. WHEN 用户发起新对话时，THE Conversation_Manager SHALL 创建新的对话上下文
3. WHEN 用户在同一会话中发送后续消息时，THE Conversation_Manager SHALL 保持前序对话历史（最多保留最近 10 轮对话）
4. THE Conversation_Manager SHALL 在组装模型请求时包含对话历史
5. WHEN 对话上下文超过 10 轮时，THE Conversation_Manager SHALL 移除最早的对话记录
6. THE Mobile_App SHALL 允许用户手动结束当前对话并开始新对话
7. THE Conversation_Manager SHALL 在内存中缓存活跃对话上下文，超过 30 分钟无活动的对话 SHALL 被清理

### Requirement 7: 统一 API 接口

**User Story:** 作为移动端开发者，我希望后端提供统一的 API 接口，以便简化客户端集成。

#### Acceptance Criteria

1. THE API_Gateway SHALL 提供 POST /api/v1/chat 端点用于统一对话请求
2. THE API_Gateway SHALL 接受包含以下字段的 JSON 请求：image_base64、system_prompt、provider、custom_config（可选）、conversation_id（可选）、stream（可选）
3. WHEN stream 参数为 true 时，THE API_Gateway SHALL 返回 SSE 格式的流式响应
4. WHEN stream 参数为 false 或未提供时，THE API_Gateway SHALL 返回完整的 JSON 响应
5. THE API_Gateway SHALL 返回包含以下字段的响应：code、message、data（包含 text、audio_url、conversation_id、latency_ms）
6. THE API_Gateway SHALL 提供 POST /api/v1/test-connection 端点用于测试自定义模型连接
7. THE API_Gateway SHALL 提供 GET /api/v1/models 端点返回支持的模型列表
8. THE API_Gateway SHALL 使用 HTTPS 协议进行所有通信
9. FOR ALL API 响应，THE Parser SHALL 验证响应格式符合 OpenAPI 规范
10. FOR ALL API 响应，THE Pretty_Printer SHALL 格式化错误信息为用户友好的格式

### Requirement 8: 模型适配层架构

**User Story:** 作为后端开发者，我希望有统一的模型适配层，以便轻松添加新的模型提供商。

#### Acceptance Criteria

1. THE Model_Adapter SHALL 定义抽象基类 MultimodalInterface，包含 process_image 方法
2. THE Model_Adapter SHALL 实现以下适配器类：OpenAIAdapter、GeminiAdapter、ClaudeAdapter、DoubaoAdapter、CustomAdapter
3. WHEN 添加新模型提供商时，THE Model_Adapter SHALL 只需创建新的适配器类继承 MultimodalInterface
4. THE Model_Adapter SHALL 统一输入格式为：图像数据（Base64）+ Prompt 文本
5. THE Model_Adapter SHALL 统一输出格式为：文本响应字符串
6. WHEN 模型返回非标准格式时，THE Model_Adapter SHALL 转换为统一格式
7. THE Model_Adapter SHALL 处理各厂商的认证方式差异（API Key、Bearer Token、自定义 Header）

### Requirement 9: 安全性与隐私保护

**User Story:** 作为用户，我希望我的图像数据和 API 密钥得到安全保护，以便保护我的隐私和账户安全。

#### Acceptance Criteria

1. THE Backend_Service SHALL 使用 HTTPS 协议进行所有客户端通信
2. THE Authentication_Service SHALL 加密存储用户的 API Key（使用 AES-256 加密）
3. WHEN THE Backend_Service 处理完图像数据时，THE Backend_Service SHALL 立即从内存中清除图像数据
4. THE Backend_Service SHALL NOT 持久化存储用户上传的图像，除非用户明确授权
5. THE Rate_Limiter SHALL 限制单个 IP 地址每分钟最多 60 个请求
6. THE Rate_Limiter SHALL 限制单个 API Key 每分钟最多 100 个请求
7. IF 请求频率超过限制，THEN THE API_Gateway SHALL 返回 HTTP 429 状态码和重试建议
8. THE Backend_Service SHALL 验证所有输入参数，防止注入攻击
9. THE Prompt_Engine SHALL 实施 Prompt 注入防护策略，过滤潜在的恶意指令
10. THE Backend_Service SHALL 记录所有 API 调用日志，包含 request_id、timestamp、user_id、endpoint、status_code

### Requirement 10: Python 项目开发规范

**User Story:** 作为后端开发者，我希望项目遵循 Python 最佳实践，以便保证代码质量和可维护性。

#### Acceptance Criteria

1. THE Backend_Service SHALL 使用 Src Layout 项目结构（代码位于 src/pillow_talk/ 目录）
2. THE Backend_Service SHALL 使用 Poetry 或 uv 进行依赖管理
3. THE Backend_Service SHALL 在 pyproject.toml 中定义所有依赖项和开发工具配置
4. THE Backend_Service SHALL 使用 ruff 或 black 进行代码格式化（行长度 <= 100）
5. THE Backend_Service SHALL 使用 mypy 进行类型检查，所有公共函数 SHALL 包含类型注解
6. THE Backend_Service SHALL 使用 pytest 作为测试框架
7. THE Backend_Service SHALL 达到至少 80% 的测试覆盖率（核心业务逻辑）
8. THE Backend_Service SHALL 使用 structlog 或 loguru 进行日志记录，禁止使用 print 语句
9. THE Backend_Service SHALL 使用 pydantic-settings 管理环境变量和配置
10. THE Backend_Service SHALL 在 Git 提交前自动运行格式化、Linting 和类型检查（使用 pre-commit hooks）
11. FOR ALL 公共模块、类和函数，THE Backend_Service SHALL 包含 Google Style 或 NumPy Style 的文档字符串

### Requirement 11: 移动端用户界面

**User Story:** 作为用户，我希望移动应用界面简洁直观，以便快速完成扫描和对话操作。

#### Acceptance Criteria

1. THE Mobile_App SHALL 提供全屏相机预览界面，底部显示操作栏
2. THE Mobile_App SHALL 在操作栏提供拍照按钮、模型选择按钮、Prompt 选择按钮
3. WHEN 用户拍照后，THE Mobile_App SHALL 显示对话界面，展示 AI 生成的文本
4. THE Mobile_App SHALL 在对话界面显示语音播放波形动画
5. THE Mobile_App SHALL 提供历史记录页面，显示最近 50 次扫描和对话记录
6. WHEN 用户点击历史记录项时，THE Mobile_App SHALL 显示该次对话的详细内容
7. THE Mobile_App SHALL 适配 iOS 15.0+ 和 Android 10.0+ 设备
8. THE Mobile_App SHALL 适配不同屏幕尺寸，包括刘海屏和灵动岛设计
9. THE Mobile_App SHALL 在网络请求期间显示加载指示器
10. WHEN 发生错误时，THE Mobile_App SHALL 显示用户友好的错误提示和重试选项

### Requirement 12: 性能优化

**User Story:** 作为用户，我希望系统响应迅速，以便获得流畅的使用体验。

#### Acceptance Criteria

1. WHEN 网络条件良好时（延迟 < 100ms），THE Backend_Service SHALL 在 3 秒内返回首个文本 token（TTFB < 3 秒）
2. THE Backend_Service SHALL 支持至少 100 QPS 的并发请求处理能力
3. THE Image_Preprocessor SHALL 在 500 毫秒内完成图像压缩和编码
4. THE Backend_Service SHALL 对模型调用设置 30 秒超时限制
5. WHERE 模型和 TTS 服务支持流式传输时，THE Backend_Service SHALL 优先使用流式传输
6. THE Backend_Service SHALL 使用异步 I/O（asyncio）处理所有网络请求
7. THE Backend_Service SHALL 记录每个请求的处理延迟，包含各阶段耗时（图像处理、模型调用、TTS 生成）
8. THE Mobile_App SHALL 在本地缓存最近播放的音频文件（最多 10 个文件）

### Requirement 13: 错误处理与日志

**User Story:** 作为开发者，我希望系统有完善的错误处理和日志记录，以便快速定位和解决问题。

#### Acceptance Criteria

1. THE Backend_Service SHALL 为每个请求生成唯一的 request_id（UUID 格式）
2. THE Backend_Service SHALL 在所有日志中包含 request_id 用于追踪
3. THE Backend_Service SHALL 使用以下日志级别：DEBUG（开发调试）、INFO（正常操作）、WARNING（潜在问题）、ERROR（错误情况）
4. WHEN 模型调用失败时，THE Backend_Service SHALL 记录 ERROR 级别日志，包含错误类型、错误消息、请求参数（脱敏后）
5. THE Backend_Service SHALL 记录每次模型调用的耗时和 token 使用量
6. IF 发生未捕获异常，THEN THE Backend_Service SHALL 记录完整的堆栈跟踪并返回 HTTP 500 错误
7. THE Backend_Service SHALL 定义自定义异常类：ModelConnectionError、TTSServiceError、RateLimitError、AuthenticationError
8. WHEN 发生已知错误时，THE Backend_Service SHALL 抛出相应的自定义异常并返回结构化的错误响应
9. THE Mobile_App SHALL 解析后端返回的错误响应并显示用户友好的错误消息

### Requirement 14: 配置文件解析与验证

**User Story:** 作为开发者，我希望系统能够正确解析和验证配置文件，以便确保配置的正确性。

#### Acceptance Criteria

1. THE Parser SHALL 解析 pyproject.toml 配置文件，加载项目依赖和工具配置
2. THE Parser SHALL 解析 .env 文件，加载环境变量配置
3. WHEN THE Parser 解析配置文件时，THE Parser SHALL 验证必需字段的存在性
4. IF 配置文件格式无效，THEN THE Parser SHALL 返回描述性错误消息，指明错误位置
5. THE Parser SHALL 解析模型 API 响应，提取文本内容
6. FOR ALL 解析操作，THE Parser SHALL 处理异常情况并返回明确的错误信息
7. THE Pretty_Printer SHALL 格式化配置对象为可读的 TOML 格式
8. THE Pretty_Printer SHALL 格式化 API 响应对象为可读的 JSON 格式
9. FOR ALL 有效的配置对象，解析后格式化再解析 SHALL 产生等价的对象（round-trip property）

### Requirement 15: 部署与运维

**User Story:** 作为运维人员，我希望系统易于部署和监控，以便保证服务的稳定运行。

#### Acceptance Criteria

1. THE Backend_Service SHALL 提供 Dockerfile 用于容器化部署
2. THE Backend_Service SHALL 提供 docker-compose.yml 用于本地开发环境搭建
3. THE Backend_Service SHALL 提供健康检查端点 GET /health，返回服务状态
4. WHEN THE Backend_Service 启动时，THE Backend_Service SHALL 在 10 秒内完成初始化并开始接受请求
5. THE Backend_Service SHALL 提供 Makefile，包含常用命令：make install、make test、make lint、make format、make run
6. THE Backend_Service SHALL 在启动时验证所有必需的环境变量是否已设置
7. IF 必需的环境变量缺失，THEN THE Backend_Service SHALL 记录错误并拒绝启动
8. THE Backend_Service SHALL 支持通过环境变量配置日志级别
9. THE Backend_Service SHALL 输出结构化日志（JSON 格式），便于日志聚合系统解析
