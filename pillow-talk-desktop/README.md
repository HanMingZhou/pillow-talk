# Pillow Talk Desktop

Pillow Talk 的 macOS 桌面应用版本 - 多模态 AI 助手

## 快速开始

### 1. 安装

```bash
./install.sh
```

这会自动：
- 检查系统依赖（Node.js、Python）
- 安装前端依赖
- 创建后端虚拟环境
- 安装后端依赖

### 2. 运行

```bash
npm start
```

应用会自动启动后端服务并打开桌面窗口。

### 3. 构建安装包

```bash
./build-mac.sh
```

生成的 `.dmg` 文件位于 `dist/` 目录。

## 功能特性

- 📷 实时摄像头预览
- 💬 流式对话输出
- 🎙️ 逐句语音播报
- 🤖 支持多个 AI 模型（豆包、千问、GLM、Gemini、OpenAI）
- 🔧 支持自定义本地模型（Ollama、LM Studio 等）
- 🎨 高端视觉设计（毛玻璃效果、渐变动画）

## 使用说明

1. 点击 📷 启动摄像头
2. 输入问题后按回车（自动捕获画面）
3. 查看流式输出和语音播报
4. 点击 ⚙️ 打开设置面板配置模型

## 系统要求

- macOS 10.13+
- Python 3.10+
- Node.js 16+

## 故障排除

**后端启动失败**
- 检查 `../pillow-talk-backend/venv/` 是否存在
- 检查 `../pillow-talk-backend/.env` 配置是否正确

**摄像头无法访问**
- 在"系统偏好设置 > 安全性与隐私 > 摄像头"中授权

**模型 API 错误**
- 检查 `.env` 中的 API Key 是否正确
- 检查网络连接

## 技术栈

- Electron - 桌面框架
- FastAPI - 后端 API
- Python - 后端语言
- HTML/CSS/JS - 前端界面

## 许可证

MIT
