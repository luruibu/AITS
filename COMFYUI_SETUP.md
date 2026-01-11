# ComfyUI 安装和配置指南

本项目需要 ComfyUI 作为图像生成后端。本指南将帮助你完成 ComfyUI 的安装和配置。

## 📋 系统要求

- **GPU**: NVIDIA GPU (推荐 8GB+ VRAM)
- **内存**: 16GB+ RAM
- **存储**: 20GB+ 可用空间
- **Python**: 3.8+ (推荐 3.8-3.11，3.12+ 可能需要额外配置)

## 🚀 快速安装

### 方法一：自动安装脚本

我们提供了自动安装脚本来简化安装过程：

```bash
# Windows
python install_comfyui.py

# Linux/Mac
python3 install_comfyui.py
```

### 方法二：手动安装

#### 1. 克隆 ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
```

#### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 下载必需模型

创建模型目录结构：
```
ComfyUI/
├── models/
│   ├── checkpoints/
│   ├── clip/
│   ├── unet/
│   └── vae/
```

**必需模型文件**：

1. **UNET 模型** (放在 `models/unet/`)
   - 文件名: `z_image_turbo_bf16.safetensors`
   - 下载链接: [Hugging Face](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/flux1-schnell.safetensors)

2. **CLIP 模型** (放在 `models/clip/`)
   - 文件名: `qwen_3_4b.safetensors`
   - 下载链接: [Hugging Face](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct/blob/main/model.safetensors)

3. **VAE 模型** (放在 `models/vae/`)
   - 文件名: `ae.safetensors`
   - 下载链接: [Hugging Face](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/ae.safetensors)

#### 4. 启动 ComfyUI

```bash
# 启动 ComfyUI 服务器
python main.py --listen 0.0.0.0 --port 8000

# 如果需要指定GPU
python main.py --listen 0.0.0.0 --port 8000 --gpu-only
```

## 🔧 配置验证

### 1. 导入工作流

1. 在浏览器中访问 ComfyUI: `http://localhost:8000`
2. 点击 "Load" 按钮
3. 选择项目根目录下的 `comfyui_workflow.json` 文件
4. 工作流应该成功加载，没有红色错误节点

### 2. 连接测试

使用项目提供的测试脚本验证 ComfyUI 配置：

```bash
# 测试 ComfyUI 连接和工作流兼容性
python test_comfyui_connection.py

# 测试完整的图像生成流程
python test_image_generation.py
```

### 3. 手动测试生成

1. 在 "CLIP Text Encode" 节点中输入测试提示词
2. 点击 "Queue Prompt" 按钮
3. 等待图像生成完成
4. 检查输出图像质量

### 4. API 测试

使用以下命令测试 ComfyUI API：

```bash
curl -X GET http://localhost:8000/system_stats
```

应该返回系统状态信息。

## 🛠️ 故障排除

### 常见问题

#### 1. 模型文件未找到
```
Error: Model file not found
```
**解决方案**: 
- 检查模型文件是否在正确的目录
- 确认文件名完全匹配
- 重新下载损坏的模型文件

#### 2. GPU 内存不足
```
CUDA out of memory
```
**解决方案**:
- 降低图像分辨率 (1024x1024 或 512x512)
- 减少批处理大小
- 使用 `--lowvram` 参数启动

#### 3. 端口被占用
```
Address already in use
```
**解决方案**:
- 更改端口: `python main.py --port 8001`
- 或终止占用端口的进程

#### 4. 依赖冲突
```
Package conflicts detected
```
**解决方案**:
- 使用虚拟环境
- 更新 pip: `pip install --upgrade pip`
- 重新安装依赖

### 性能优化

#### GPU 优化
```bash
# 高性能模式
python main.py --gpu-only --highvram

# 低显存模式
python main.py --lowvram --cpu-offload

# CPU 模式（无GPU）
python main.py --cpu
```

#### 内存优化
```bash
# 启用模型卸载
python main.py --normalvram

# 启用注意力优化
python main.py --use-split-cross-attention
```

## 🔗 与 AI Image Tree 集成

### 1. 配置连接

在 AI Image Tree 项目的 `config.json` 中设置：

```json
{
  "comfyui": {
    "url": "http://localhost:8000",
    "sampling_steps": 9,
    "cfg_scale": 1.0,
    "image_size": "1536x1536"
  }
}
```

### 2. 测试连接

启动 AI Image Tree 应用后，在系统设置中测试 ComfyUI 连接。

### 3. 自定义工作流

如果需要修改工作流：

1. 在 ComfyUI 界面中编辑工作流
2. 导出为 JSON 文件
3. 更新 `auto_image_generator.py` 中的 `create_workflow` 方法

## 📚 进阶配置

### 自定义模型

要使用其他模型，请：

1. 下载兼容的模型文件
2. 放置在相应的 `models/` 子目录中
3. 更新工作流中的模型名称
4. 重启 ComfyUI

### 批量处理

对于批量图像生成，可以调整：

```json
{
  "batch_size": 4,
  "queue_size": 10
}
```

### 远程部署

要在远程服务器上部署 ComfyUI：

```bash
# 启动时绑定到所有接口
python main.py --listen 0.0.0.0 --port 8000

# 配置防火墙允许端口 8000
# 更新 AI Image Tree 配置中的 ComfyUI URL
```

## 🆘 获取帮助

如果遇到问题：

1. 查看 [ComfyUI 官方文档](https://github.com/comfyanonymous/ComfyUI)
2. 检查 [ComfyUI Issues](https://github.com/comfyanonymous/ComfyUI/issues)
3. 在 AI Image Tree 项目中提交 Issue

## 📄 许可证

ComfyUI 使用 GPL-3.0 许可证。请确保遵守相关许可证条款。