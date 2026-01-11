# ComfyUI 集成说明

本文档详细说明了 AI Image Tree 项目与 ComfyUI 的集成方式和工作原理。

## 🏗️ 架构概览

```
AI Image Tree 应用
       ↓
AutoImageGenerator (auto_image_generator.py)
       ↓
ComfyUIClient 类
       ↓ HTTP API
ComfyUI 服务器 (localhost:8000)
       ↓
工作流执行 (comfyui_workflow.json)
       ↓
生成的图像文件
```

## 🔧 核心组件

### 1. ComfyUIClient 类

位于 `auto_image_generator.py` 中，负责与 ComfyUI API 通信：

```python
class ComfyUIClient:
    def __init__(self, base_url: str)
    def create_workflow(self, prompt_text: str, seed: int, ...) -> Dict
    async def submit_workflow(self, workflow: Dict) -> str
    async def wait_for_completion(self, prompt_id: str, max_wait: int = 300) -> bool
    async def get_generated_image(self, prompt_id: str) -> bytes
```

#### 主要方法说明：

- **create_workflow()**: 根据提示词创建 ComfyUI 工作流 JSON
- **submit_workflow()**: 提交工作流到 ComfyUI API，返回 prompt_id
- **wait_for_completion()**: 轮询检查工作流执行状态
- **get_generated_image()**: 下载生成的图像数据

### 2. 工作流定义 (comfyui_workflow.json)

定义了完整的图像生成管道：

```json
{
  "39": {"class_type": "CLIPLoader", ...},      // CLIP 文本编码器
  "40": {"class_type": "VAELoader", ...},       // VAE 编码器/解码器
  "41": {"class_type": "EmptySD3LatentImage", ...}, // 空白 Latent 图像
  "44": {"class_type": "KSampler", ...},        // 主采样器
  "46": {"class_type": "UNETLoader", ...},      // UNET 模型
  "47": {"class_type": "ModelSamplingAuraFlow", ...}, // 采样配置
  "9":  {"class_type": "SaveImage", ...}       // 图像保存
}
```

#### 节点连接关系：

```
提示词 → CLIP编码(39) → 正向条件(45)
                              ↓
空Latent(41) → K采样器(44) → VAE解码(43) → 保存图像(9)
                ↑
UNET模型(46) → 采样配置(47)
```

### 3. 集成到主应用

在 `app.py` 中的集成：

```python
from auto_image_generator import AutoImageGenerator, GenerationConfig

# 创建配置
generation_config = create_generation_config()
generator = AutoImageGenerator(generation_config)

# 在路由中使用
@app.route('/api/generate_image', methods=['POST'])
async def generate_image():
    # 使用 generator 生成图像
    image_data, final_prompt, score = await generator.generate_optimized_image(prompt)
```

## 🔄 工作流程

### 1. 图像生成流程

```
1. 用户输入提示词
   ↓
2. AutoImageGenerator.generate_optimized_image()
   ↓
3. AI客户端优化提示词 (可选)
   ↓
4. ComfyUIClient.create_workflow() 创建工作流
   ↓
5. ComfyUIClient.submit_workflow() 提交到 ComfyUI
   ↓
6. ComfyUIClient.wait_for_completion() 等待完成
   ↓
7. ComfyUIClient.get_generated_image() 获取图像
   ↓
8. AI客户端评估图像质量 (可选)
   ↓
9. 返回图像数据和元信息
```

### 2. API 通信流程

```
POST /prompt
{
  "prompt": {工作流JSON},
  "client_id": "唯一客户端ID"
}
↓ 返回
{
  "prompt_id": "工作流执行ID"
}

GET /history/{prompt_id}
↓ 返回执行状态和结果

GET /view?filename=xxx&subfolder=xxx&type=xxx
↓ 返回图像文件数据
```

## 📋 必需模型文件

ComfyUI 需要以下模型文件才能正常工作：

| 模型类型 | 文件名 | 路径 | 大小 |
|---------|--------|------|------|
| UNET | z_image_turbo_bf16.safetensors | models/unet/ | ~23.8GB |
| CLIP | qwen_3_4b.safetensors | models/clip/ | ~8.2GB |
| VAE | ae.safetensors | models/vae/ | ~335MB |

## ⚙️ 配置参数

### GenerationConfig 参数

```python
@dataclass
class GenerationConfig:
    comfyui_url: str = "http://localhost:8000"  # ComfyUI 服务地址
    sampling_steps: int = 9                     # 采样步数
    cfg_scale: float = 1.0                      # CFG 引导强度
    image_width: int = 1536                     # 图像宽度
    image_height: int = 1536                    # 图像高度
    max_iterations: int = 5                     # 最大优化迭代次数
    quality_threshold: float = 7.0              # 质量阈值
    skip_quality_evaluation: bool = False       # 跳过质量评估
```

### 工作流参数映射

| 配置参数 | 工作流节点 | 节点参数 |
|---------|-----------|----------|
| prompt_text | 节点45 | inputs.text |
| seed | 节点44 | inputs.seed |
| sampling_steps | 节点44 | inputs.steps |
| cfg_scale | 节点44 | inputs.cfg |
| image_width | 节点41 | inputs.width |
| image_height | 节点41 | inputs.height |

## 🧪 测试和验证

### 1. 连接测试

```bash
python test_comfyui_connection.py
```

检查项目：
- ComfyUI API 连接状态
- 工作流文件格式验证
- 必需节点类型检查
- 模型文件存在性 (可选)

### 2. 生成测试

```bash
python test_image_generation.py
```

测试项目：
- AI 客户端功能
- 完整图像生成流程
- 文件保存和输出

### 3. 手动验证

1. 访问 ComfyUI Web 界面: http://localhost:8000
2. 加载 `comfyui_workflow.json` 工作流
3. 修改提示词并手动执行
4. 检查生成结果

## 🔧 故障排除

### 常见问题

#### 1. 连接失败
```
❌ ComfyUI 连接失败: Connection refused
```
**解决方案**:
- 确保 ComfyUI 正在运行
- 检查端口配置 (默认 8000)
- 验证防火墙设置

#### 2. 工作流执行失败
```
❌ Workflow failed: Model file not found
```
**解决方案**:
- 检查模型文件是否存在
- 验证文件路径和名称
- 重新下载损坏的模型

#### 3. 内存不足
```
❌ CUDA out of memory
```
**解决方案**:
- 降低图像分辨率
- 使用 `--lowvram` 启动参数
- 减少批处理大小

#### 4. 节点类型错误
```
❌ Unknown node type: XXX
```
**解决方案**:
- 更新 ComfyUI 到最新版本
- 安装缺失的自定义节点
- 检查工作流兼容性

### 调试技巧

1. **启用详细日志**:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查 ComfyUI 日志**:
   查看 ComfyUI 控制台输出的错误信息

3. **验证工作流 JSON**:
   使用 JSON 验证器检查格式

4. **测试单个节点**:
   在 ComfyUI 界面中逐个测试节点

## 🚀 性能优化

### 1. ComfyUI 优化

```bash
# 高性能模式
python main.py --gpu-only --highvram

# 低显存模式  
python main.py --lowvram --cpu-offload

# 启用模型卸载
python main.py --normalvram
```

### 2. 应用层优化

- 使用连接池减少 HTTP 开销
- 实现图像缓存机制
- 并行处理多个请求
- 优化工作流参数

### 3. 模型优化

- 使用量化模型减少显存占用
- 选择适合的模型精度 (fp16/bf16)
- 启用模型编译优化

## 📚 扩展开发

### 1. 自定义工作流

要创建新的工作流：

1. 在 ComfyUI 界面中设计工作流
2. 导出为 JSON 文件
3. 修改 `ComfyUIClient.create_workflow()` 方法
4. 更新参数映射关系

### 2. 添加新节点类型

```python
def create_custom_workflow(self, ...):
    return {
        "new_node_id": {
            "class_type": "CustomNodeType",
            "inputs": {
                "param1": value1,
                "param2": ["other_node_id", 0]
            }
        }
    }
```

### 3. 集成其他模型

修改工作流中的模型加载节点：

```json
{
  "46": {
    "class_type": "UNETLoader",
    "inputs": {
      "unet_name": "your_custom_model.safetensors"
    }
  }
}
```

## 📄 相关文档

- [ComfyUI 官方文档](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI API 参考](https://github.com/comfyanonymous/ComfyUI/blob/master/server.py)
- [COMFYUI_SETUP.md](COMFYUI_SETUP.md) - 安装指南
- [README.md](README.md) - 项目总览

---

💡 **提示**: 如果遇到问题，请先运行测试脚本进行诊断，然后查看相关日志信息。