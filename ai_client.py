#!/usr/bin/env python3
"""
通用AI客户端系统
支持多种AI服务：Ollama、OpenRouter、OpenAI兼容API等
"""

import asyncio
import aiohttp
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AIProviderType(Enum):
    """AI服务提供商类型"""
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"

@dataclass
class AIProviderConfig:
    """AI服务提供商配置"""
    provider_type: AIProviderType
    name: str
    base_url: str
    api_key: Optional[str] = None
    model: str = ""
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    extra_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}

class BaseAIClient(ABC):
    """AI客户端基类"""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        pass
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表 - 子类可以重写"""
        return []
    
    async def enhance_prompt(self, original_prompt: str) -> str:
        """优化提示词"""
        system_prompt = """你是一个专业的AI图像生成提示词优化专家。
你的任务是将用户的简单描述转换为详细、具体、能生成高质量图像的提示词。

优化原则：
1. 添加具体的视觉细节（颜色、光线、构图等）
2. 包含艺术风格和技术参数
3. 使用专业的摄影和艺术术语
4. 保持提示词简洁但信息丰富
5. 确保描述清晰、无歧义

请直接返回优化后的英文提示词，不要添加额外说明。"""

        prompt = f"请优化以下图像生成提示词：{original_prompt}"
        return await self.generate_text(prompt, system_prompt)
    
    async def evaluate_image(self, image_base64: str, original_prompt: str):
        """评估图像质量 - 基类方法，子类可以重写"""
        # 默认返回一个基本的质量评估
        return {
            'score': 8.0,
            'feedback': '图像质量评估功能未实现',
            'suggestions': [],
            'defects_found': [],
            'consistency_issues': [],
            'original_prompt_accuracy': 8.0
        }

class OllamaClient(BaseAIClient):
    """Ollama客户端"""
    
    async def get_available_models(self) -> List[str]:
        """获取Ollama可用模型列表"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model in data.get('models', []):
                            model_name = model.get('name', '')
                            if model_name and model_name not in models:
                                models.append(model_name)
                        return sorted(models)
                    else:
                        logger.warning(f"获取Ollama模型列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {e}")
            return []
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                }
                
                # 添加额外参数
                if self.config.extra_params:
                    payload["options"].update(self.config.extra_params)
                
                async with session.post(f"{self.config.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception(f"Ollama API timeout after {self.config.timeout}s")
        except Exception as e:
            logger.error(f"Ollama client error: {e}")
            raise
    
    async def evaluate_image(self, image_base64: str, original_prompt: str):
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

请返回JSON格式的评估结果：
{
    "score": 总分(0-10),
    "feedback": "详细评价",
    "suggestions": ["改进建议1", "改进建议2"],
    "defects_found": ["发现的具体缺陷1", "发现的具体缺陷2"],
    "consistency_issues": ["一致性问题1", "一致性问题2"],
    "original_prompt_accuracy": 原始提示词匹配度评分(0-10)
}"""

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                payload = {
                    "model": self.config.model,
                    "prompt": f"""请评估这张图像的质量。

**原始提示词**: {original_prompt}

请特别关注图像与原始提示词的匹配度，按照系统提示的格式返回JSON评估结果。""",
                    "system": system_prompt,
                    "images": [image_base64],  # Ollama 视觉 API 格式
                    "stream": False
                }
                
                async with session.post(f"{self.config.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # 尝试解析JSON响应
                        try:
                            import json
                            import re
                            
                            # 提取JSON部分
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                
                                # 清理JSON字符串
                                json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
                                evaluation = json.loads(json_str)
                                
                                # 确保评分在合理范围内
                                raw_score = evaluation.get("score", 0)
                                final_score = float(raw_score)
                                if final_score > 10:
                                    final_score = final_score / 10
                                final_score = max(0, min(10, final_score))
                                
                                return {
                                    'score': final_score,
                                    'feedback': evaluation.get("feedback", ""),
                                    'suggestions': evaluation.get("suggestions", []),
                                    'defects_found': evaluation.get("defects_found", []),
                                    'consistency_issues': evaluation.get("consistency_issues", []),
                                    'original_prompt_accuracy': float(evaluation.get("original_prompt_accuracy", final_score))
                                }
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"JSON解析失败: {e}")
                        
                        # 如果无法解析JSON，返回默认评估
                        return {
                            'score': 7.0,
                            'feedback': f'图像质量评估完成，但响应格式解析失败: {response_text[:100]}...',
                            'suggestions': [],
                            'defects_found': [],
                            'consistency_issues': [],
                            'original_prompt_accuracy': 7.0
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama vision API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Ollama image evaluation error: {e}")
            # 返回默认评估结果
            return {
                'score': 7.0,
                'feedback': f'图像质量评估失败: {str(e)}',
                'suggestions': [],
                'defects_found': [],
                'consistency_issues': [],
                'original_prompt_accuracy': 7.0
            }

class OpenRouterClient(BaseAIClient):
    """OpenRouter客户端"""
    
    async def get_available_models(self) -> List[str]:
        """获取OpenRouter可用模型列表"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                headers = {
                    "Authorization": f"Bearer {self.config.api_key}" if self.config.api_key else "",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/yourusername/ai-image-tree",
                    "X-Title": "AI Image Tree System"
                }
                
                async with session.get(f"{self.config.base_url}/api/v1/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model in data.get('data', []):
                            model_id = model.get('id', '')
                            if model_id:
                                models.append(model_id)
                        return sorted(models)
                    else:
                        logger.warning(f"获取OpenRouter模型列表失败: HTTP {response.status}")
                        # 返回默认模型列表
                        return [
                            "anthropic/claude-3.5-sonnet",
                            "openai/gpt-4o",
                            "openai/gpt-4o-mini",
                            "google/gemini-pro-1.5",
                            "meta-llama/llama-3.1-70b-instruct",
                            "mistralai/mistral-7b-instruct"
                        ]
        except Exception as e:
            logger.error(f"获取OpenRouter模型列表失败: {e}")
            # 返回默认模型列表
            return [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "openai/gpt-4o-mini",
                "google/gemini-pro-1.5",
                "meta-llama/llama-3.1-70b-instruct",
                "mistralai/mistral-7b-instruct"
            ]
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/yourusername/ai-image-tree",
                    "X-Title": "AI Image Tree System"
                }
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "stream": False
                }
                
                # 添加额外参数
                if self.config.extra_params:
                    payload.update(self.config.extra_params)
                
                async with session.post(f"{self.config.base_url}/api/v1/chat/completions", 
                                      json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception(f"OpenRouter API timeout after {self.config.timeout}s")
        except Exception as e:
            logger.error(f"OpenRouter client error: {e}")
            raise

class OpenAICompatibleClient(BaseAIClient):
    """OpenAI兼容API客户端（支持各种兼容OpenAI格式的服务）"""
    
    async def get_available_models(self) -> List[str]:
        """获取OpenAI兼容API可用模型列表"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                headers = {
                    "Content-Type": "application/json"
                }
                
                # 如果有API密钥，添加认证头
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                async with session.get(f"{self.config.base_url}/v1/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model in data.get('data', []):
                            model_id = model.get('id', '')
                            if model_id:
                                models.append(model_id)
                        return sorted(models)
                    else:
                        logger.warning(f"获取OpenAI兼容API模型列表失败: HTTP {response.status}")
                        # 如果是OpenAI官方API，返回已知模型
                        if "api.openai.com" in self.config.base_url:
                            return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
                        else:
                            return ["custom-model"]
        except Exception as e:
            logger.error(f"获取OpenAI兼容API模型列表失败: {e}")
            # 如果是OpenAI官方API，返回已知模型
            if "api.openai.com" in self.config.base_url:
                return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            else:
                return ["custom-model"]
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                headers = {
                    "Content-Type": "application/json"
                }
                
                # 如果有API密钥，添加认证头
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "stream": False
                }
                
                # 添加额外参数
                if self.config.extra_params:
                    payload.update(self.config.extra_params)
                
                async with session.post(f"{self.config.base_url}/v1/chat/completions", 
                                      json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenAI Compatible API error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception(f"OpenAI Compatible API timeout after {self.config.timeout}s")
        except Exception as e:
            logger.error(f"OpenAI Compatible client error: {e}")
            raise

class AIClientFactory:
    """AI客户端工厂"""
    
    @staticmethod
    def create_client(config: AIProviderConfig) -> BaseAIClient:
        """根据配置创建对应的AI客户端"""
        if config.provider_type == AIProviderType.OLLAMA:
            return OllamaClient(config)
        elif config.provider_type == AIProviderType.OPENROUTER:
            return OpenRouterClient(config)
        elif config.provider_type == AIProviderType.OPENAI:
            return OpenAICompatibleClient(config)
        elif config.provider_type == AIProviderType.OPENAI_COMPATIBLE:
            return OpenAICompatibleClient(config)
        else:
            raise ValueError(f"Unsupported AI provider type: {config.provider_type}")

# 预定义的服务配置模板
PROVIDER_TEMPLATES = {
    "ollama": {
        "name": "Ollama",
        "provider_type": "ollama",  # 使用字符串而不是枚举
        "base_url": "http://localhost:11434",
        "api_key": None,
        "models": ["ministral-3:latest", "llama3.2:latest", "qwen2.5:latest", "gemma3:12b"]
    },
    "openrouter": {
        "name": "OpenRouter",
        "provider_type": "openrouter",  # 使用字符串而不是枚举
        "base_url": "https://openrouter.ai",
        "api_key": "your-openrouter-api-key",
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mistral-7b-instruct"
        ]
    },
    "openai": {
        "name": "OpenAI",
        "provider_type": "openai",  # 使用字符串而不是枚举
        "base_url": "https://api.openai.com",
        "api_key": "your-openai-api-key",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    },
    "custom_openai": {
        "name": "Custom OpenAI Compatible",
        "provider_type": "openai_compatible",  # 使用字符串而不是枚举
        "base_url": "http://localhost:8000",
        "api_key": None,
        "models": ["custom-model"]
    }
}

def get_provider_template(provider_key: str) -> Dict:
    """获取服务提供商模板"""
    return PROVIDER_TEMPLATES.get(provider_key, {})

def list_available_providers() -> List[str]:
    """列出可用的服务提供商"""
    return list(PROVIDER_TEMPLATES.keys())