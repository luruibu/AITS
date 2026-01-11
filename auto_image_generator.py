#!/usr/bin/env python3
"""
自动化图像生成和优化系统
整合 AI 客户端和 ComfyUI，实现提示词优化、图像生成、质量检查的闭环流程
"""

import asyncio
import aiohttp
import json
import base64
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
import hashlib

# 导入新的AI客户端系统
from ai_client import AIClientFactory, AIProviderConfig, AIProviderType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """生成配置"""
    ollama_url: str = "http://localhost:11434"  # 保持向后兼容
    ollama_model: str = "gemma3:4b"  # 保持向后兼容
    comfyui_url: str = "http://localhost:8000"
    max_iterations: int = 5
    quality_threshold: float = 7.0
    output_dir: str = "generated_images"
    # 质量检查设置
    quality_check_enabled: bool = True
    accuracy_check_enabled: bool = True
    skip_quality_evaluation: bool = False  # 完全跳过质量评估
    # ComfyUI 设置
    sampling_steps: int = 9
    cfg_scale: float = 1.0
    image_width: int = 1536
    image_height: int = 1536
    # 新的AI客户端配置
    ai_client: Optional[object] = None  # AI客户端实例
    
@dataclass
class ImageQuality:
    """图像质量评估结果"""
    score: float
    feedback: str
    suggestions: List[str]
    defects_found: List[str] = None  # 发现的缺陷列表
    consistency_issues: List[str] = None  # 一致性问题列表
    original_prompt_accuracy: float = 0.0  # 与原始提示词的匹配度 (0-10)
    
    def __post_init__(self):
        if self.defects_found is None:
            self.defects_found = []
        if self.consistency_issues is None:
            self.consistency_issues = []

# 保持向后兼容的 OllamaClient 类
class OllamaClient:
    """Ollama 客户端 (向后兼容)"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        
        # 创建新的AI客户端
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            name="Ollama",
            base_url=base_url,
            model=model
        )
        self._ai_client = AIClientFactory.create_client(config)
        
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        return await self._ai_client.generate_text(prompt, system_prompt)
    
    async def enhance_prompt(self, original_prompt: str) -> str:
        """优化提示词"""
        return await self._ai_client.enhance_prompt(original_prompt)
    
    async def evaluate_image(self, image_base64: str, original_prompt: str) -> ImageQuality:
        """评估图像质量 - 使用 Ollama 视觉功能"""
        system_prompt = """你是一个专业的AI图像质量评估专家，特别擅长发现AI生成图像的常见问题。

请仔细观察这张图像，重点检查以下方面：

**关键缺陷检查（如发现严重问题，评分不应超过6分）：**
1. 人物解剖结构：手指数量（应为5个）、腿的数量（应为2条）、手臂数量（应为2条）
2. 面部特征：眼睛数量和对称性、鼻子和嘴巴的正常性
3. 物体逻辑：重力违反、透视错误、物理不合理
4. 文字和符号：是否出现乱码或不可读文字
5. 重复元素：异常的重复图案或元素

**质量评估维度：**
1. 解剖准确性 (0-10分) - 人物身体结构是否正确
2. 构图和布局 (0-10分) - 画面组织和视觉平衡
3. 色彩和光线 (0-10分) - 色彩搭配和光影效果
4. 细节和清晰度 (0-10分) - 图像清晰度和细节丰富度
5. 一致性评估 (0-10分) - 风格、光照、色彩、透视、逻辑的一致性
6. 艺术美感 (0-10分) - 整体美学价值
7. 与提示词匹配度 (0-10分) - 是否符合描述要求

**评分标准：**
- 发现严重解剖错误（如多腿、多手臂、手指异常）：最高6分
- 发现中等问题（如轻微透视错误）：最高8分
- 无明显问题：可给8-10分

**一致性评估重点：**
- 风格一致性：整体艺术风格是否统一，不同元素风格是否协调
- 光照一致性：光源方向、强度、阴影是否合理统一
- 色彩一致性：色调、饱和度、色温是否协调
- 透视一致性：视角、比例、远近关系是否统一
- 逻辑一致性：场景元素、时间、空间逻辑是否合理

请返回JSON格式的评估结果：
{
    "score": 总分(0-10),
    "feedback": "详细评价，必须明确指出发现的任何解剖、逻辑或一致性问题",
    "suggestions": ["改进建议1", "改进建议2", ...],
    "defects_found": ["发现的具体缺陷1", "发现的具体缺陷2", ...],
    "consistency_issues": ["一致性问题1", "一致性问题2", ...],
    "original_prompt_accuracy": 原始提示词匹配度评分(0-10),
    "prompt_analysis": {
        "missing_elements": ["原始提示词中缺失的元素"],
        "extra_elements": ["图像中多出的元素"],
        "style_match": "风格匹配度评价"
    }
}"""

        # 使用 Ollama 的视觉 API 格式
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "prompt": f"""请评估这张图像的质量。

**原始提示词**: {original_prompt}

请特别关注图像与原始提示词的匹配度：
1. 是否包含了原始提示词中的所有关键元素？
2. 图像内容是否偏离了原始意图？
3. 是否添加了原始提示词中没有要求的元素？
4. 整体风格和氛围是否符合原始描述？

请按照系统提示的格式返回JSON评估结果。""",
                "system": system_prompt,
                "images": [image_base64],  # Ollama 视觉 API 格式
                "stream": False
            }
            
            try:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # 尝试解析JSON响应
                        try:
                            # 提取JSON部分
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                
                                # 清理JSON字符串，移除控制字符
                                json_str = self._clean_json_string(json_str)
                                logger.debug(f"提取并清理的JSON字符串: {json_str[:200]}...")
                                evaluation = json.loads(json_str)
                                
                                # 确保评分在合理范围内
                                raw_score = evaluation.get("score", 0)
                                final_score = float(raw_score)
                                if final_score > 10:
                                    final_score = final_score / 10  # 如果是百分制，转换为10分制
                                final_score = max(0, min(10, final_score))  # 限制在0-10范围
                                
                                logger.info(f"JSON解析成功 - 原始评分: {raw_score}, 最终评分: {final_score}")
                                
                                return ImageQuality(
                                    score=final_score,
                                    feedback=evaluation.get("feedback", ""),
                                    suggestions=evaluation.get("suggestions", []),
                                    defects_found=evaluation.get("defects_found", []),
                                    consistency_issues=evaluation.get("consistency_issues", []),
                                    original_prompt_accuracy=float(evaluation.get("original_prompt_accuracy", final_score))
                                )
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"JSON解析失败: {e}")
                            logger.debug(f"原始响应文本: {response_text[:500]}...")
                        
                        # 如果无法解析JSON，使用文本分析
                        return self._parse_text_evaluation(response_text)
                    else:
                        raise Exception(f"Ollama 视觉API错误: {response.status}")
            except Exception as e:
                logger.error(f"图像评估失败: {e}")
                # 返回默认评估
                return ImageQuality(
                    score=6.0,
                    feedback="无法进行图像评估，使用默认评分",
                    suggestions=["检查网络连接", "确认模型支持视觉功能"]
                )
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串，移除控制字符和格式问题"""
        import re
        
        # 移除控制字符（保留必要的换行和制表符）
        json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
        
        # 修复常见的JSON格式问题
        # 移除多余的逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 修复引号问题
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # 压缩多余的空白字符
        json_str = re.sub(r'\s+', ' ', json_str)
        
        return json_str.strip()
    
    def _parse_text_evaluation(self, text: str) -> ImageQuality:
        """从文本中解析评估结果"""
        logger.info("使用文本解析模式")
        
        # 尝试从文本中提取评分
        score = 6.0  # 默认评分
        
        # 查找数字评分 - 更全面的模式
        import re
        score_patterns = [
            r'"score"[：:\s]*(\d+(?:\.\d+)?)',  # JSON中的score字段
            r'总分[：:]\s*(\d+(?:\.\d+)?)',
            r'评分[：:]\s*(\d+(?:\.\d+)?)',
            r'分数[：:]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*[分/]10',  # X分/10分格式
            r'(\d+(?:\.\d+)?)\s*/\s*10',   # X/10格式
            r'(\d+(?:\.\d+)?)\s*分',       # X分格式
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    extracted_score = float(match.group(1))
                    if extracted_score > 10:  # 如果是百分制，转换为10分制
                        extracted_score = extracted_score / 10
                    if 0 <= extracted_score <= 10:  # 只接受合理范围的评分
                        score = extracted_score
                        logger.info(f"从文本中提取评分: {score} (模式: {pattern})")
                        break
                except ValueError:
                    continue
        
        # 提取建议
        suggestions = []
        suggestion_keywords = ["建议", "改进", "优化", "提升", "可以", "应该", "尝试"]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in suggestion_keywords):
                # 清理行首的数字、符号等
                clean_line = re.sub(r'^[\d\.\-\*\s\[\]]+', '', line).strip()
                # 移除引号和其他格式字符
                clean_line = re.sub(r'^["\'\`]+|["\'\`]+$', '', clean_line).strip()
                if clean_line and len(clean_line) > 10 and len(clean_line) < 200:
                    suggestions.append(clean_line)
        
        final_score = min(max(score, 0), 10)  # 确保评分在0-10范围内
        logger.info(f"文本解析完成 - 最终评分: {final_score}, 建议数量: {len(suggestions)}")
        
        # 提取缺陷信息
        defects = []
        defect_keywords = ["错误", "缺陷", "问题", "异常", "多出", "缺少", "不正确", "不合理"]
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in defect_keywords):
                clean_line = re.sub(r'^[\d\.\-\*\s\[\]]+', '', line).strip()
                clean_line = re.sub(r'^["\'\`]+|["\'\`]+$', '', clean_line).strip()
                if clean_line and len(clean_line) > 5 and len(clean_line) < 100:
                    defects.append(clean_line)
        
        # 提取一致性问题
        consistency_issues = []
        consistency_keywords = ["不一致", "不协调", "不匹配", "风格混乱", "光照不统一"]
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in consistency_keywords):
                clean_line = re.sub(r'^[\d\.\-\*\s\[\]]+', '', line).strip()
                clean_line = re.sub(r'^["\'\`]+|["\'\`]+$', '', clean_line).strip()
                if clean_line and len(clean_line) > 5 and len(clean_line) < 100:
                    consistency_issues.append(clean_line)
        
        # 尝试提取原始提示词匹配度评分
        prompt_accuracy = final_score  # 默认与总分相同
        accuracy_patterns = [
            r'原始提示词.*?(\d+(?:\.\d+)?)',
            r'匹配度.*?(\d+(?:\.\d+)?)',
            r'准确性.*?(\d+(?:\.\d+)?)'
        ]
        
        for pattern in accuracy_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    extracted_accuracy = float(match.group(1))
                    if extracted_accuracy > 10:
                        extracted_accuracy = extracted_accuracy / 10
                    if 0 <= extracted_accuracy <= 10:
                        prompt_accuracy = extracted_accuracy
                        break
                except ValueError:
                    continue
        
        return ImageQuality(
            score=final_score,
            feedback=text,
            suggestions=suggestions[:3],  # 最多3个建议
            defects_found=defects[:3],    # 最多3个缺陷
            consistency_issues=consistency_issues[:3],  # 最多3个一致性问题
            original_prompt_accuracy=prompt_accuracy
        )

class ComfyUIClient:
    """ComfyUI 客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def create_workflow(self, prompt_text: str, seed: int, sampling_steps: int = 9, cfg_scale: float = 1.0, width: int = 1536, height: int = 1536) -> Dict:
        """创建工作流"""
        # 生成唯一的文件名前缀
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_prefix = f"gen_{timestamp}_{seed}"
        
        return {
            # CLIP 加载器
            '39': {
                'class_type': 'CLIPLoader',
                'inputs': {
                    'clip_name': 'qwen_3_4b.safetensors',
                    'type': 'lumina2',
                    'device': 'default',
                },
            },
            # VAE 加载器
            '40': {
                'class_type': 'VAELoader',
                'inputs': {
                    'vae_name': 'ae.safetensors',
                },
            },
            # 空 Latent 图像
            '41': {
                'class_type': 'EmptySD3LatentImage',
                'inputs': {
                    'width': width,
                    'height': height,
                    'batch_size': 1,
                },
            },
            # 条件零化
            '42': {
                'class_type': 'ConditioningZeroOut',
                'inputs': {
                    'conditioning': ['45', 0],
                },
            },
            # VAE 解码
            '43': {
                'class_type': 'VAEDecode',
                'inputs': {
                    'samples': ['44', 0],
                    'vae': ['40', 0],
                },
            },
            # K 采样器
            '44': {
                'class_type': 'KSampler',
                'inputs': {
                    'seed': seed,
                    'steps': sampling_steps,
                    'cfg': cfg_scale,
                    'sampler_name': 'res_multistep',
                    'scheduler': 'simple',
                    'denoise': 1,
                    'model': ['47', 0],
                    'positive': ['45', 0],
                    'negative': ['42', 0],
                    'latent_image': ['41', 0],
                },
            },
            # CLIP 文本编码
            '45': {
                'class_type': 'CLIPTextEncode',
                'inputs': {
                    'text': prompt_text,
                    'clip': ['39', 0],
                },
            },
            # UNET 加载器
            '46': {
                'class_type': 'UNETLoader',
                'inputs': {
                    'unet_name': 'z_image_turbo_bf16.safetensors',
                    'weight_dtype': 'default',
                },
            },
            # 模型采样
            '47': {
                'class_type': 'ModelSamplingAuraFlow',
                'inputs': {
                    'shift': 3,
                    'model': ['46', 0],
                },
            },
            # 保存图像
            '9': {
                'class_type': 'SaveImage',
                'inputs': {
                    'filename_prefix': unique_prefix,
                    'images': ['43', 0],
                },
            },
        }
    
    async def submit_workflow(self, workflow: Dict) -> str:
        """提交工作流"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "prompt": workflow,
                "client_id": f"client_{int(time.time())}_{random.randint(1000, 9999)}"
            }
            
            async with session.post(f"{self.base_url}/prompt", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["prompt_id"]
                else:
                    raise Exception(f"ComfyUI API error: {response.status}")
    
    async def get_workflow_status(self, prompt_id: str) -> Dict:
        """获取工作流状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get(prompt_id, {})
                else:
                    return {}
    
    async def wait_for_completion(self, prompt_id: str, max_wait: int = 300) -> bool:
        """等待工作流完成"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = await self.get_workflow_status(prompt_id)
            
            if status.get("status", {}).get("completed"):
                return True
            elif status.get("status", {}).get("status_str") == "error":
                error_msg = "Unknown error"
                messages = status.get("status", {}).get("messages", [])
                for msg in messages:
                    if msg[0] == "execution_error":
                        error_msg = f"{msg[1].get('exception_type', 'Error')}: {msg[1].get('exception_message', 'Unknown')}"
                        break
                raise Exception(f"Workflow failed: {error_msg}")
            
            await asyncio.sleep(5)
        
        raise Exception("Workflow timeout")
    
    async def get_generated_image(self, prompt_id: str) -> bytes:
        """获取生成的图像"""
        status = await self.get_workflow_status(prompt_id)
        outputs = status.get("outputs", {})
        
        # 找到图像输出
        image_info = None
        for node_id, node_output in outputs.items():
            if "images" in node_output and node_output["images"]:
                image_info = node_output["images"][0]
                break
        
        if not image_info:
            raise Exception("No image found in outputs")
        
        # 下载图像
        async with aiohttp.ClientSession() as session:
            params = {
                "filename": image_info["filename"],
                "subfolder": image_info["subfolder"],
                "type": image_info["type"]
            }
            
            async with session.get(f"{self.base_url}/view", params=params) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download image: {response.status}")

class AutoImageGenerator:
    """自动化图像生成器"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        
        # 支持新的AI客户端系统
        if hasattr(config, 'ai_client') and config.ai_client:
            # 使用传入的AI客户端
            self.ai_client = config.ai_client
            logger.info(f"使用传入的AI客户端: {type(self.ai_client).__name__}")
        else:
            # 向后兼容：创建OllamaClient
            self.ollama = OllamaClient(config.ollama_url, config.ollama_model)
            self.ai_client = self.ollama._ai_client  # 使用内部的AI客户端
            logger.info(f"创建Ollama客户端: {config.ollama_url}, 模型: {config.ollama_model}")
        
        self.comfyui = ComfyUIClient(config.comfyui_url)
        
        # 创建输出目录
        Path(config.output_dir).mkdir(exist_ok=True)
    
    async def generate_optimized_image(self, initial_prompt: str) -> Tuple[bytes, str, float]:
        """生成优化的图像"""
        current_prompt = initial_prompt
        best_image = None
        best_score = 0.0
        best_prompt = initial_prompt
        
        logger.info(f"开始自动化图像生成流程，初始提示词: {initial_prompt}")
        
        for iteration in range(self.config.max_iterations):
            logger.info(f"=== 第 {iteration + 1} 轮迭代 ===")
            
            # 1. 优化提示词
            if iteration > 0:
                logger.info("正在优化提示词...")
                current_prompt = await self.ai_client.enhance_prompt(current_prompt)
                logger.info(f"优化后的提示词: {current_prompt}")
            
            # 2. 生成图像
            logger.info("正在生成图像...")
            seed = random.randint(1, 4294967295)
            workflow = self.comfyui.create_workflow(
                current_prompt, 
                seed,
                self.config.sampling_steps,
                self.config.cfg_scale,
                self.config.image_width,
                self.config.image_height
            )
            
            try:
                prompt_id = await self.comfyui.submit_workflow(workflow)
                logger.info(f"工作流已提交，ID: {prompt_id}")
                
                await self.comfyui.wait_for_completion(prompt_id)
                image_data = await self.comfyui.get_generated_image(prompt_id)
                logger.info("图像生成完成")
                
                # 3. 评估图像质量
                if self.config.skip_quality_evaluation:
                    logger.info("跳过图像质量评估 (已禁用)")
                    # 使用默认质量评估结果
                    quality = ImageQuality(
                        score=8.0,
                        feedback="质量评估已禁用，使用默认评分",
                        suggestions=[],
                        defects_found=[],
                        consistency_issues=[],
                        original_prompt_accuracy=8.0
                    )
                else:
                    logger.info("正在评估图像质量...")
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    quality_result = await self.ai_client.evaluate_image(image_base64, current_prompt)
                    
                    # 创建ImageQuality对象
                    quality = ImageQuality(
                        score=quality_result['score'],
                        feedback=quality_result['feedback'],
                        suggestions=quality_result['suggestions'],
                        defects_found=quality_result['defects_found'],
                        consistency_issues=quality_result['consistency_issues'],
                        original_prompt_accuracy=quality_result['original_prompt_accuracy']
                    )
                
                logger.info(f"图像质量评分: {quality.score}/10")
                logger.info(f"原始提示词匹配度: {quality.original_prompt_accuracy}/10")
                
                # 显示发现的缺陷
                if quality.defects_found:
                    logger.warning(f"发现 {len(quality.defects_found)} 个缺陷:")
                    for i, defect in enumerate(quality.defects_found, 1):
                        logger.warning(f"  {i}. {defect}")
                else:
                    logger.info("未发现明显缺陷")
                
                # 显示一致性问题
                if quality.consistency_issues:
                    logger.warning(f"发现 {len(quality.consistency_issues)} 个一致性问题:")
                    for i, issue in enumerate(quality.consistency_issues, 1):
                        logger.warning(f"  {i}. {issue}")
                
                # 检查原始提示词匹配度
                if quality.original_prompt_accuracy < 7.0:
                    logger.warning(f"原始提示词匹配度较低 ({quality.original_prompt_accuracy}/10)，可能偏离了原始意图")
                elif quality.original_prompt_accuracy >= 9.0:
                    logger.info("原始提示词匹配度优秀，完全符合原始意图")
                
                logger.info(f"评价: {quality.feedback}")
                
                # 4. 保存当前迭代的图像
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
                prompt_hash = hashlib.md5(initial_prompt.encode('utf-8')).hexdigest()[:8]
                current_filename = f"iter{iteration + 1}_{timestamp}_{prompt_hash}_score{quality.score:.1f}.png"
                current_filepath = Path(self.config.output_dir) / current_filename
                with open(current_filepath, 'wb') as f:
                    f.write(image_data)
                logger.info(f"保存当前图像: {current_filepath}")
                
                # 5. 更新最佳结果
                if quality.score > best_score:
                    best_image = image_data
                    best_score = quality.score
                    best_prompt = current_prompt
                    
                    # 创建最佳图像的符号链接或副本
                    best_filename = f"BEST_{timestamp}_{prompt_hash}_score{quality.score:.1f}.png"
                    best_filepath = Path(self.config.output_dir) / best_filename
                    with open(best_filepath, 'wb') as f:
                        f.write(image_data)
                    logger.info(f"更新最佳图像: {best_filepath}")
                
                # 6. 检查是否达到质量标准
                if self.config.skip_quality_evaluation:
                    # 如果跳过质量评估，直接完成生成
                    logger.info("质量评估已禁用，生成完成！")
                    break
                else:
                    # 根据配置检查质量和准确度
                    quality_ok = True
                    accuracy_ok = True
                    
                    if self.config.quality_check_enabled:
                        quality_ok = quality.score >= self.config.quality_threshold
                    
                    if self.config.accuracy_check_enabled:
                        accuracy_ok = quality.original_prompt_accuracy >= 7.0  # 匹配度阈值
                    
                    # 构建状态消息
                    status_parts = []
                    if self.config.quality_check_enabled:
                        status_parts.append(f"质量: {quality.score:.1f}/{self.config.quality_threshold}")
                    if self.config.accuracy_check_enabled:
                        status_parts.append(f"匹配度: {quality.original_prompt_accuracy:.1f}/7.0")
                    
                    if quality_ok and accuracy_ok:
                        logger.info(f"达到标准 ({', '.join(status_parts)})，生成完成！")
                        break
                    elif not self.config.quality_check_enabled and not self.config.accuracy_check_enabled:
                        logger.info("质量和准确度检查均已禁用，生成完成！")
                        break
                    else:
                        failed_checks = []
                        if self.config.quality_check_enabled and not quality_ok:
                            failed_checks.append(f"质量不足 ({quality.score:.1f}/{self.config.quality_threshold})")
                        if self.config.accuracy_check_enabled and not accuracy_ok:
                            failed_checks.append(f"匹配度不足 ({quality.original_prompt_accuracy:.1f}/7.0)")
                        
                        if failed_checks:
                            logger.warning(f"{', '.join(failed_checks)}，继续优化...")
                        else:
                            logger.info("所有启用的检查都已通过，生成完成！")
                            break
                
                # 7. 根据建议调整提示词
                if iteration < self.config.max_iterations - 1 and not self.config.skip_quality_evaluation:
                    # 根据匹配度问题进行针对性优化
                    if self.config.accuracy_check_enabled and quality.original_prompt_accuracy < 7.0:
                        logger.info("匹配度不足，重新强调原始提示词要素...")
                        # 重新强调原始提示词的关键元素
                        current_prompt = f"{initial_prompt}, highly detailed, accurate representation"
                    elif quality.suggestions:
                        suggestions_text = "、".join(quality.suggestions[:3])  # 取前3个建议
                        current_prompt = f"{current_prompt}, {suggestions_text}"
                        logger.info(f"根据建议调整提示词: {suggestions_text}")
                    else:
                        # 通用优化
                        current_prompt = await self.ai_client.enhance_prompt(current_prompt)
                elif iteration < self.config.max_iterations - 1 and self.config.skip_quality_evaluation:
                    # 如果跳过质量评估，只进行基本的提示词优化
                    logger.info("跳过质量评估，进行基本提示词优化...")
                    current_prompt = await self.ai_client.enhance_prompt(current_prompt)
                
            except Exception as e:
                logger.error(f"第 {iteration + 1} 轮生成失败: {e}")
                continue
        
        logger.info(f"自动化生成完成！最佳评分: {best_score}/10")
        return best_image, best_prompt, best_score
    
    async def batch_generate(self, prompts: List[str]) -> List[Tuple[str, bytes, str, float]]:
        """批量生成图像"""
        results = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"处理第 {i + 1}/{len(prompts)} 个提示词")
            try:
                image, final_prompt, score = await self.generate_optimized_image(prompt)
                results.append((prompt, image, final_prompt, score))
            except Exception as e:
                logger.error(f"处理提示词 '{prompt}' 失败: {e}")
                results.append((prompt, None, prompt, 0.0))
        
        return results

async def main():
    """主函数"""
    # 配置
    config = GenerationConfig(
        max_iterations=3,
        quality_threshold=7.5,
        output_dir="auto_generated_images"
    )
    
    # 创建生成器
    generator = AutoImageGenerator(config)
    
    # 测试提示词
    test_prompts = [
        "一个美丽的中国女孩，穿着传统汉服",
        "未来科技城市的夜景",
        "森林中的小木屋，阳光透过树叶"
    ]
    
    # 批量生成
    results = await generator.batch_generate(test_prompts)
    
    # 输出结果
    print("\n=== 生成结果汇总 ===")
    for original, image, final_prompt, score in results:
        status = "成功" if image else "失败"
        print(f"原始提示词: {original}")
        print(f"最终提示词: {final_prompt}")
        print(f"质量评分: {score}/10")
        print(f"状态: {status}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())