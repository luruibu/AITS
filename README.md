# AI Image Tree System

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

🌳 一个基于AI的创意图像生成树系统，支持多种AI提供商，通过分支探索实现无限创意扩展。

## ✨ 特性

### 🎨 创意激发与商业生成
- � **无限创意探索**: 通过树状分支结构，从单一创意出发，探索数百种变化可能
- 💡 **智能关键词提取**: AI自动分析提示词，提取核心创意元素，生成4个不同方向的分支
- � **商业级图像生成**: 支持商业用途的高质量图像创作，适用于品牌设计、营销素材、产品展示
- 🔄 **迭代优化流程**: 自动评估图像质量，持续优化直到达到商业标准
- � **批量创意生产**: 一次输入，生成完整的创意树，大幅提升创作效率
- 🎨 **风格一致性**: 在保持创意多样性的同时，确保品牌风格的一致性

### 🤖 先进AI技术
- � **Z-image Turbo模型**: 集成最新的Z-image turbo bf16模型，专为快速高质量图像生成优化
  - ⚡ 超快生成速度：9步采样即可生成高质量图像
  - 🎯 精准提示词理解：基于先进的CLIP和UNET架构
  - 💎 商业级品质：支持1536x1536高分辨率输出
  - 🔧 灵活配置：支持自定义采样步数、CFG引导强度等参数
- � **多AI提供商支持**: Ollama (本地) / OpenRouter (云端) / OpenAI (官方) / 自定义API
- 🔄 **动态模型获取**: 实时从API获取最新可用模型列表，支持350+云端模型

### 🔒 隐私与安全
- 🏠 **本地优先**: 支持完全本地部署，数据不离开您的设备
- 🔐 **数据加密**: 所有API密钥和敏感信息采用加密存储
- 🚫 **无数据收集**: 不收集用户创作内容，不上传个人数据
- 🛡️ **离线工作**: 使用Ollama本地模型时，可完全离线运行
- 📝 **透明日志**: 所有网络请求和数据处理过程完全透明
- 🔒 **权限控制**: 细粒度的API访问控制和使用限制

### 🎯 智能化体验
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

本项目集成了最新的Z-image Turbo模型，提供商业级的图像生成能力：

#### Z-image Turbo 模型特性
- **🚀 极速生成**: 采用turbo优化算法，仅需9步采样即可生成高质量图像
- **💎 商业品质**: 支持多种分辨率输出，包括1920×1072宽屏、1072×1920手机竖屏等
- **🎯 精准理解**: 基于先进的CLIP文本编码器，准确理解复杂提示词
- **⚡ 内存优化**: bf16精度优化，降低显存占用，提升生成速度
- **🔧 灵活配置**: 支持自定义采样步数、CFG引导强度、图像尺寸等参数

#### 支持的分辨率
- **预设尺寸**:
  - 512×512 (快速预览)
  - 768×1024 (竖屏标准)
  - 1024×768 (横屏标准)
  - 1024×1024 (方形标准)
  - 1072×1920 (手机竖屏)
  - 1536×1536 (高清方形)
  - 1920×1072 (宽屏显示)
- **自定义尺寸**: 支持256×256到4096×4096范围内的任意尺寸
- **智能预设**: 提供常用尺寸快速设置按钮
- **宽高比计算**: 自动显示宽高比和像素信息

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

### 🎯 应用场景

#### 🎨 创意设计师
- **品牌视觉设计**: 从品牌概念出发，生成多种视觉风格方案
- **营销素材创作**: 快速生成海报、横幅、社交媒体图片
- **产品包装设计**: 探索不同的包装风格和视觉元素
- **UI/UX设计灵感**: 为界面设计提供视觉参考和创意方向

#### 💼 商业用户
- **电商产品图**: 生成商品展示图、场景图、lifestyle图片
- **内容营销**: 为博客、文章、广告创建配图
- **品牌故事**: 通过视觉叙事展现品牌价值和理念
- **市场调研**: 快速生成概念图进行用户测试和反馈收集

#### 🎭 内容创作者
- **社交媒体**: Instagram、微博、小红书等平台的原创配图
- **视频缩略图**: YouTube、B站等视频平台的封面设计
- **文章插图**: 博客、公众号文章的配图创作
- **创意写作**: 为小说、故事提供视觉灵感

#### 🏢 企业团队
- **演示文稿**: PPT、提案、报告的专业配图
- **培训材料**: 企业培训、教育内容的视觉素材
- **团队协作**: 头脑风暴、创意讨论的视觉化工具
- **原型设计**: 产品概念、服务流程的可视化展示

### 基本使用

1. **输入提示词**: 在主界面输入你的创意描述
2. **生成根节点**: 系统会提取关键词并生成初始图像
3. **选择关键词**: 从提取的关键词中选择感兴趣的方向
4. **生成分支**: 系统会基于选中的关键词生成4个分支图像
5. **继续探索**: 可以继续从任何分支节点扩展新的创意方向

### 🎨 创意激发实例

#### 案例1：品牌Logo设计
**输入**: "现代科技公司logo，简约风格，蓝色调"
**生成树结构**:
```
现代科技公司logo
├── 几何图形 → 立体几何、平面几何、抽象几何、动态几何
├── 科技元素 → 电路板、芯片、数据流、网络节点
├── 字体设计 → 未来字体、极简字体、3D字体、发光字体
└── 色彩搭配 → 渐变蓝、深蓝白、蓝绿配色、蓝紫配色
```

#### 案例2：产品包装设计
**输入**: "高端茶叶包装，中国风，礼盒装"
**生成树结构**:
```
高端茶叶包装
├── 传统元素 → 水墨画、书法、印章、古典纹样
├── 材质质感 → 丝绸质感、竹制包装、陶瓷元素、金属装饰
├── 色彩方案 → 墨绿金色、红色系、黑白灰、青花瓷色
└── 结构设计 → 抽屉式、折叠式、圆筒形、多层设计
```

#### 案例3：社交媒体配图
**输入**: "健康生活方式，Instagram风格，温暖色调"
**生成树结构**:
```
健康生活方式
├── 运动场景 → 瑜伽、跑步、健身房、户外运动
├── 健康饮食 → 沙拉、果汁、有机食品、营养搭配
├── 生活环境 → 简约家居、绿植装饰、自然光线、整洁空间
└── 情绪表达 → 微笑、放松、活力、平静
```

### 💼 商业应用价值

#### 提升创作效率
- **传统方式**: 设计师需要数小时构思和制作多个方案
- **AI树状生成**: 10分钟内生成数十个创意方向，效率提升90%

#### 降低创作成本
- **人工成本**: 减少初期创意探索的人力投入
- **时间成本**: 快速验证创意可行性，避免后期大幅修改
- **试错成本**: 低成本探索多种可能性，降低决策风险

#### 激发创意灵感
- **突破思维局限**: AI提供人类可能忽略的创意角度
- **跨领域融合**: 自动组合不同领域的设计元素
- **风格探索**: 快速尝试各种视觉风格和表现手法

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

## 🔒 隐私与安全

### 数据隐私保护

本项目高度重视用户隐私，采用多重保护措施：

#### 🏠 本地优先架构
- **完全本地部署**: 支持使用Ollama在本地运行AI模型，数据不离开您的设备
- **离线工作模式**: 使用本地模型时可完全断网运行，确保创作内容的绝对隐私
- **自主控制**: 用户完全控制数据的存储位置和访问权限

#### 🔐 数据加密与安全
- **API密钥加密**: 所有API密钥采用AES加密存储，防止泄露
- **本地数据库**: 使用SQLite本地数据库，生成历史仅存储在本地
- **无云端同步**: 不会将用户创作内容上传到任何云端服务器
- **安全传输**: 所有网络通信采用HTTPS加密传输

#### 🚫 零数据收集政策
- **不收集个人信息**: 不收集用户姓名、邮箱、设备信息等个人数据
- **不追踪用户行为**: 不使用任何分析工具追踪用户使用习惯
- **不存储创作内容**: 云端AI服务仅用于临时处理，不保存用户的创作内容
- **透明开源**: 所有代码开源，用户可审查隐私保护措施

#### 🛡️ 企业级安全
- **权限控制**: 细粒度的API访问控制和使用限制
- **审计日志**: 完整的操作日志记录，便于安全审计
- **防护机制**: 内置防护措施，防止恶意攻击和数据泄露
- **合规支持**: 符合GDPR、CCPA等主要隐私法规要求

### 推荐安全配置

#### 🏢 企业用户
```bash
# 使用本地Ollama部署，确保数据不出企业网络
# 1. 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. 下载推荐模型
ollama pull gemma3:12b

# 3. 配置仅使用本地服务
# 在config.json中设置：
{
  "ai_provider": {
    "provider_type": "ollama",
    "base_url": "http://localhost:11434"
  }
}
```

#### 🏠 个人用户
- 优先选择本地模型以保护隐私
- 定期清理生成历史和缓存文件
- 使用强密码保护API密钥
- 定期更新软件版本获取安全补丁

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