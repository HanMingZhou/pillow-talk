# Pillow Talk Desktop

Pillow Talk 的 macOS/Windows/Linux 桌面应用版本。

## 功能特性

- 📷 摄像头实时预览和拍照
- 💬 多轮对话支持
- 🎙️ 实时语音播报（TTS）
- 🤖 支持多个 AI 模型提供商
- 🎨 现代化的用户界面
- 🔧 自定义模型配置

## 系统要求

- macOS 10.13+ / Windows 10+ / Linux
- Python 3.10+（后端服务）
- Node.js 16+（构建桌面应用）

## 开发模式运行

1. 安装依赖：
```bash
cd pillow-talk-desktop
npm install
```

2. 确保后端服务已配置：
```bash
cd ../pillow-talk-backend
# 确保虚拟环境已创建并安装了依赖
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

3. 启动桌面应用（会自动启动后端）：
```bash
cd ../pillow-talk-desktop
npm start
```

## 构建应用

### macOS

```bash
npm run build:mac
```

构建完成后，应用位于 `dist/` 目录：
- `Pillow Talk-{version}.dmg` - DMG 安装包
- `Pillow Talk-{version}-mac.zip` - ZIP 压缩包

### Windows

```bash
npm run build:win
```

### Linux

```bash
npm run build:linux
```

## 打包说明

打包后的应用会包含：
- Electron 运行时
- 前端界面（HTML/CSS/JS）
- 后端服务启动脚本

注意：打包后的应用仍然需要 Python 环境和后端依赖。确保：
1. 后端的 `venv` 目录存在
2. 所有 Python 依赖已安装
3. `.env` 配置文件已正确设置

## 使用说明

1. 启动应用后会自动启动后端服务
2. 点击"启动摄像头"开始使用
3. 拍照后输入问题进行对话
4. 在设置中选择不同的 AI 模型提供商
5. 支持自定义本地部署的模型

## 故障排除

### 后端启动失败

检查：
- Python 虚拟环境是否存在：`pillow-talk-backend/venv/`
- 依赖是否已安装：`pip list`
- `.env` 配置是否正确

### 摄像头无法访问

- macOS：在"系统偏好设置 > 安全性与隐私 > 隐私 > 摄像头"中授权应用
- Windows：在"设置 > 隐私 > 摄像头"中授权应用

### 模型 API 错误

检查：
- API Key 是否正确配置在 `.env` 文件中
- 网络连接是否正常
- API 配额是否充足

## 技术栈

- Electron - 桌面应用框架
- FastAPI - 后端 API 框架
- Python - 后端语言
- HTML/CSS/JavaScript - 前端界面

## 许可证

MIT
