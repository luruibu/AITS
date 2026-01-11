# 安装指南

## 📋 系统要求

### 基础要求
- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **内存**: 最少 4GB RAM（推荐 8GB+）
- **存储**: 至少 2GB 可用空间

### 外部服务
- **ComfyUI**: 用于图像生成（必需）
- **Ollama**: 用于本地AI模型（可选）

## 🚀 快速安装

### 自动安装（推荐）

1. **下载项目**
```bash
git clone https://github.com/your-username/ai-image-tree.git
cd ai-image-tree
```

2. **运行安装脚本**
```bash
python setup.py
```

3. **启动应用**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# 通用
python start.py
```

## 🔧 手动安装

### 1. 环境准备

#### Python 环境
```bash
# 检查Python版本
python --version  # 应该是 3.8+

# 创建虚拟环境（推荐）
python -m venv ai-image-tree-env

# 激活虚拟环境
# Windows
ai-image-tree-env\Scripts\activate
# Linux/Mac
source ai-image-tree-env/bin/activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置设置

#### 创建配置文件
```bash
cp config.json.example config.json
```

#### 编辑配置文件
打开 `config.json` 并配置以下内容：

```json
{
  "ai_provider": {
    "provider_type": "ollama",  // 或 "openrouter", "openai"
    "base_url": "http://localhost:11434",
    "api_key": null,  // OpenRouter/OpenAI需要
    "model": "llama3.2:latest"
  },
  "comfyui": {
    "url": "http://localhost:8000"
  }
}
```

### 3. 外部服务设置

#### ComfyUI 安装
```bash
# 克隆ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 安装依赖
pip install -r requirements.txt

# 启动ComfyUI
python main.py --listen 0.0.0.0 --port 8000
```

#### Ollama 安装（可选）
```bash
# 下载并安装Ollama
# 访问: https://ollama.ai/download

# 启动Ollama服务
ollama serve

# 下载模型
ollama pull llama3.2:latest
```

### 4. 启动应用
```bash
python app.py
```

访问: http://localhost:8080

## 🐳 Docker 安装（即将支持）

```bash
# 构建镜像
docker build -t ai-image-tree .

# 运行容器
docker run -p 8080:8080 ai-image-tree
```

## 🔍 故障排除

### 常见问题

#### 1. Python版本错误
```
❌ 需要 Python 3.8 或更高版本
```
**解决方案**: 升级Python到3.8+版本

#### 2. 依赖安装失败
```
❌ 依赖安装失败
```
**解决方案**: 
- 检查网络连接
- 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
- 升级pip: `python -m pip install --upgrade pip`

#### 3. ComfyUI连接失败
```
❌ ComfyUI服务不可用
```
**解决方案**:
- 确保ComfyUI正在运行
- 检查端口是否正确（默认8000）
- 检查防火墙设置

#### 4. Ollama连接失败
```
❌ Ollama服务不可用
```
**解决方案**:
- 确保Ollama服务正在运行
- 检查端口是否正确（默认11434）
- 确认模型已下载

### 日志调试

启用调试模式：
```bash
export FLASK_DEBUG=1  # Linux/Mac
set FLASK_DEBUG=1     # Windows
python app.py
```

查看详细日志：
```bash
python app.py --log-level DEBUG
```

## 📞 获取帮助

如果遇到问题：

1. 查看 [FAQ](https://github.com/your-username/ai-image-tree/wiki/FAQ)
2. 搜索 [Issues](https://github.com/your-username/ai-image-tree/issues)
3. 提交新的 [Issue](https://github.com/your-username/ai-image-tree/issues/new)
4. 参与 [Discussions](https://github.com/your-username/ai-image-tree/discussions)

## 🔄 更新

### 更新到最新版本
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 备份数据
```bash
# 备份配置和数据库
cp config.json config.json.backup
cp *.db *.db.backup
```