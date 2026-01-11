# AI Image Tree System

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

🌳 一个基于AI的创意图像生成树系统，支持多种AI提供商，通过分支探索实现无限创意扩展。

## ✨ 特性

- 🤖 **多AI提供商支持**: Ollama (本地) / OpenRouter (云端) / OpenAI (官方) / 自定义API
- 🌐 **动态模型获取**: 实时从API获取最新可用模型列表
- 🎨 **智能化界面**: 根据提供商类型自动调整配置界面
- 🌳 **树状生成**: 基于关键词的分支探索和创意扩展
- 🔄 **质量控制**: 可配置的图像质量评估和自动重试
- 💾 **持久化存储**: SQLite数据库存储生成历史和设置
- 📱 **响应式Web界面**: 现代化的用户界面设计
- 🌍 **多语言支持**: 中英文界面，支持语言切换

## 🚀 快速开始

### 环境要求

- Python 3.8+
- ComfyUI (用于图像生成)
- Ollama (可选，用于本地AI模型)

> 📖 详细安装说明请查看 [INSTALL.md](INSTALL.md)
> 🎨 ComfyUI 安装指南请查看 [COMFYUI_SETUP.md](COMFYUI_SETUP.md)

### 安装步骤

#### 方法一：自动安装（推荐）

1. **克隆项目**
```bash
git clone https://github.com/your-username/ai-image-tree.git
cd ai-image-tree
```

2. **自动安装 ComfyUI**
```bash
python install_comfyui.py
```

3. **运行安装脚本**
```bash
python setup.py
```

4. **配置设置**
编辑 `config.json` 文件，配置你的AI服务地址和API密钥

5. **启动服务**
```bash
# 启动 ComfyUI (新终端窗口)
./start_comfyui.sh  # Linux/Mac
# 或
start_comfyui.bat   # Windows

# 启动 AI Image Tree
python start.py
```

#### 方法二：手动安装

1. **克隆项目**
```bash
git clone https://github.com/your-username/ai-image-tree.git
cd ai-image-tree
```

2. **安装 ComfyUI**
```bash
# 参考 COMFYUI_SETUP.md 手动安装 ComfyUI
# 或使用自动脚本
python install_comfyui.py
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置设置**
```bash
cp config.json.example config.json
# 编辑 config.json 配置你的AI服务
```

5. **启动应用**
```bash
# 启动 ComfyUI (端口 8000)
cd ComfyUI
python main.py --listen 0.0.0.0 --port 8000

# 启动 AI Image Tree (新终端，端口 8080)
cd ..
python app.py
```

5. **访问界面**
打开浏览器访问: http://localhost:8080

### 快速启动

#### Windows 用户
双击 `start.bat` 文件，或在命令行运行：
```cmd
start.bat
```

#### Linux/Mac 用户
在终端运行：
```bash
chmod +x start.sh
./start.sh
```

#### 通用方式
```bash
python start.py
```

## 🔧 配置说明

### AI提供商配置

系统支持多种AI提供商，在Web界面的系统设置中可以切换：

#### Ollama (本地)
- 无需API密钥
- 支持本地部署的各种开源模型
- 默认地址: `http://localhost:11434`

#### OpenRouter (云端)
- 需要API密钥 (从 [OpenRouter](https://openrouter.ai) 获取)
- 支持350+个云端模型
- 包括Claude、GPT-4、Gemini等

#### OpenAI (官方)
- 需要API密钥 (从 [OpenAI](https://openai.com) 获取)
- 支持GPT-4o、GPT-4o-mini等官方模型

#### 自定义API
- 支持任何OpenAI兼容的API服务
- 可配置自定义地址和认证

### ComfyUI配置

确保ComfyUI正在运行并可访问:
- 默认地址: `http://localhost:8000`
- 支持自定义采样步数、CFG引导强度等参数

#### 测试 ComfyUI 连接

使用测试脚本验证 ComfyUI 配置：

```bash
# 测试默认地址 (localhost:8000)
python test_comfyui_connection.py

# 测试自定义地址
python test_comfyui_connection.py http://192.168.100.249:8000
```

测试脚本会检查：
- ComfyUI API 连接状态
- 工作流文件兼容性
- 必需模型文件是否存在

## 📖 使用指南

### 基本使用

1. **输入提示词**: 在主界面输入你的创意描述
2. **生成根节点**: 系统会提取关键词并生成初始图像
3. **选择关键词**: 从提取的关键词中选择感兴趣的方向
4. **生成分支**: 系统会基于选中的关键词生成4个分支图像
5. **继续探索**: 可以继续从任何分支节点扩展新的创意方向

### 高级功能

- **系统设置**: 配置AI提供商、模型参数、质量控制等
- **模型切换**: 实时切换不同的AI模型
- **质量控制**: 启用图像质量评估和自动重试
- **历史管理**: 查看和管理之前的生成树
- **语言切换**: 中英文界面切换，支持多语言

## 🛠️ 开发

### 项目结构

```
ai-image-tree/
├── app.py                 # 主应用程序
├── ai_client.py          # AI客户端系统
├── auto_image_generator.py # 图像生成器
├── database.py           # 数据库操作
├── i18n_utils.py         # 国际化工具
├── start.py              # 启动脚本
├── setup.py              # 安装脚本
├── install_comfyui.py    # ComfyUI 自动安装脚本
├── test_comfyui_connection.py # ComfyUI 连接测试脚本
├── test_image_generation.py # 图像生成测试脚本
├── comfyui_workflow.json # ComfyUI 工作流定义
├── config.json.example   # 配置文件模板
├── requirements.txt      # Python依赖
├── i18n/                 # 多语言翻译文件
│   ├── zh_CN.json       # 中文翻译
│   ├── en_US.json       # 英文翻译
│   └── ja_JP.json       # 日文翻译
├── static/js/            # 前端JavaScript
│   └── i18n.js          # 前端国际化支持
├── templates/            # Web模板
│   └── simple_index.html
├── generated_images/     # 生成的图像（自动创建）
├── web_generated_images/ # Web生成的图像（自动创建）
├── COMFYUI_SETUP.md     # ComfyUI 安装指南
├── COMFYUI_INTEGRATION.md # ComfyUI 集成技术文档
├── INSTALL.md           # 详细安装指南
├── README_EN.md         # 英文版项目文档
├── LICENSE              # 开源许可证
├── CONTRIBUTING.md      # 贡献指南
└── README.md            # 项目文档
```

## 📁 项目文件

| 文件/目录 | 说明 |
|-----------|------|
| `app.py` | 主应用程序 |
| `ai_client.py` | AI客户端系统 |
| `auto_image_generator.py` | 图像生成器 |
| `database.py` | 数据库操作 |
| `i18n_utils.py` | 国际化工具类 |
| `setup.py` | 自动安装脚本 |
| `start.py` | 启动脚本 |
| `start.bat` | Windows启动脚本 |
| `start.sh` | Linux/Mac启动脚本 |
| `install_comfyui.py` | ComfyUI 自动安装脚本 |
| `test_comfyui_connection.py` | ComfyUI 连接测试脚本 |
| `test_image_generation.py` | 图像生成测试脚本 |
| `comfyui_workflow.json` | ComfyUI 工作流定义文件 |
| `config.json.example` | 配置文件模板 |
| `requirements.txt` | Python依赖列表 |
| `i18n/` | 多语言翻译文件目录 |
| `static/js/` | 前端JavaScript文件 |
| `templates/` | Web模板目录 |
| `COMFYUI_SETUP.md` | ComfyUI 详细安装指南 |
| `COMFYUI_INTEGRATION.md` | ComfyUI 集成技术文档 |
| `INSTALL.md` | 详细安装指南 |
| `README_EN.md` | 英文版项目文档 |
| `CONTRIBUTING.md` | 贡献指南 |
| `CHANGELOG.md` | 更新日志 |
| `LICENSE` | 开源许可证 |

### 核心组件

- **AI客户端系统** (`ai_client.py`): 统一的多提供商AI接口
- **图像生成器** (`auto_image_generator.py`): 图像生成和质量控制
- **数据库层** (`database.py`): 数据持久化和管理
- **国际化系统** (`i18n_utils.py`): 多语言支持系统
- **Web界面** (`app.py` + `templates/`): Flask Web应用

### 扩展开发

系统采用模块化设计，易于扩展：

- **添加新的AI提供商**: 继承`BaseAIClient`类
- **自定义质量评估**: 修改`ImageQuality`评估逻辑
- **界面定制**: 修改HTML模板和CSS样式
- **添加新语言**: 在`i18n/`目录创建翻译文件

## 🚀 部署

### 开发环境
```bash
python app.py  # 默认运行在 localhost:8080
```

### 生产环境
```bash
# 使用 Gunicorn (推荐)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app

# 使用 uWSGI
pip install uwsgi
uwsgi --http :8080 --wsgi-file app.py --callable app
```

### Docker 部署（即将支持）
```bash
docker build -t ai-image-tree .
docker run -p 8080:8080 ai-image-tree
```

## 🔒 安全注意事项

- 🔑 妥善保管API密钥，不要提交到版本控制
- 🌐 生产环境建议使用HTTPS
- 🛡️ 配置适当的防火墙规则
- 📝 定期备份数据库和配置文件

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的图像生成后端
- [Ollama](https://ollama.ai/) - 本地AI模型运行环境
- [OpenRouter](https://openrouter.ai/) - 云端AI模型API服务
- [Flask](https://flask.palletsprojects.com/) - Web框架

## 📞 支持

如果你遇到问题或有建议，请：

- 提交 [Issue](https://github.com/your-username/ai-image-tree/issues)
- 参与 [Discussions](https://github.com/your-username/ai-image-tree/discussions)

---

⭐ 如果这个项目对你有帮助，请给个星标支持！