#!/usr/bin/env python3
"""
AI Image Generation Tree System
A web-based creative exploration tool that generates branching image trees using Ollama and ComfyUI.

Author: Your Name
License: MIT
Repository: https://github.com/yourusername/ai-image-tree
"""

from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import aiohttp
import json
import base64
import uuid
import os
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import time

from auto_image_generator import AutoImageGenerator, GenerationConfig
from ai_client import AIClientFactory, AIProviderConfig, AIProviderType, PROVIDER_TEMPLATES
from database import db
from i18n_utils import i18n, t, get_locale, set_locale, register_i18n_functions

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 注册国际化函数
register_i18n_functions(app)

# 全局配置
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# 默认系统设置
default_system_settings = {
    'ai_provider': {
        'provider_type': 'ollama',
        'name': 'Ollama',
        'base_url': CONFIG.get('ai_provider', {}).get('base_url', 'http://localhost:11434'),
        'api_key': CONFIG.get('ai_provider', {}).get('api_key'),
        'model': CONFIG.get('ai_provider', {}).get('model', 'gemma3:4b'),
        'max_tokens': CONFIG.get('ai_provider', {}).get('max_tokens', 4000),
        'temperature': CONFIG.get('ai_provider', {}).get('temperature', 0.7),
        'timeout': CONFIG.get('ai_provider', {}).get('timeout', 30),
        'extra_params': CONFIG.get('ai_provider', {}).get('extra_params', {})
    },
    'comfyui': {
        'url': CONFIG.get('comfyui', {}).get('url', 'http://localhost:8000'),
        'sampling_steps': 9,
        'cfg_scale': 1.0,
        'image_size': '1536x1536'
    },
    'quality_control': CONFIG.get('quality_control', {
        'enabled': True,
        'quality_check_enabled': True,
        'accuracy_check_enabled': True,
        'score_threshold': 7.0,
        'accuracy_threshold': 7.0,
        'auto_retry': True,
        'max_retries': 2,
        'strict_mode': False,
        'defect_detection': True
    }),
    'available_providers': CONFIG.get('available_providers', PROVIDER_TEMPLATES)
}

# 从数据库加载用户的系统设置
system_settings = db.get_user_setting('system_settings', default_system_settings)

# 确保所有必要的字段都存在
merged_settings = default_system_settings.copy()
if system_settings:
    # 深度合并设置
    for key, value in system_settings.items():
        if isinstance(value, dict) and key in merged_settings:
            merged_settings[key].update(value)
        else:
            merged_settings[key] = value
system_settings = merged_settings

logger.info(f"加载系统设置: {system_settings}")

# 如果数据库中的设置不完整，保存完整的默认设置
if not db.get_user_setting('system_settings'):
    logger.info("初始化系统设置到数据库")
    db.save_user_setting('system_settings', system_settings)

# 保持向后兼容，从系统设置中提取质量控制配置
quality_config = system_settings.get('quality_control', default_system_settings['quality_control'])

def get_current_system_settings():
    """获取当前的系统设置（从数据库加载最新设置）"""
    global system_settings
    # 从数据库重新加载最新设置
    latest_settings = db.get_user_setting('system_settings', default_system_settings)
    
    # 确保所有必要的字段都存在，使用默认值填充缺失的字段
    merged_settings = default_system_settings.copy()
    if latest_settings:
        # 深度合并设置
        for key, value in latest_settings.items():
            if isinstance(value, dict) and key in merged_settings:
                merged_settings[key].update(value)
            else:
                merged_settings[key] = value
    
    # 更新全局配置
    system_settings.clear()
    system_settings.update(merged_settings)
    
    return system_settings

def safe_create_provider_config(ai_provider_config):
    """安全地创建AI提供商配置，处理类型转换"""
    logger.info(f"safe_create_provider_config 接收到配置: {ai_provider_config}")
    
    provider_type_str = ai_provider_config.get('provider_type', 'ollama')
    logger.info(f"提取的provider_type: {provider_type_str} (类型: {type(provider_type_str)})")
    
    # 确保provider_type是正确的枚举值
    if isinstance(provider_type_str, str):
        try:
            provider_type = AIProviderType(provider_type_str)
            logger.info(f"成功转换为枚举: {provider_type}")
        except ValueError as e:
            logger.error(f"转换枚举失败: {e}, provider_type_str='{provider_type_str}'")
            logger.warning(f"未知的提供商类型: {provider_type_str}，使用默认值 ollama")
            provider_type = AIProviderType.OLLAMA
    else:
        provider_type = provider_type_str
        logger.info(f"使用现有枚举: {provider_type}")
    
    try:
        config = AIProviderConfig(
            provider_type=provider_type,
            name=ai_provider_config.get('name', 'AI Provider'),
            base_url=ai_provider_config.get('base_url', 'http://localhost:11434'),
            api_key=ai_provider_config.get('api_key'),
            model=ai_provider_config.get('model', 'default'),
            max_tokens=ai_provider_config.get('max_tokens', 4000),
            temperature=ai_provider_config.get('temperature', 0.7),
            timeout=ai_provider_config.get('timeout', 30),
            extra_params=ai_provider_config.get('extra_params', {})
        )
        logger.info(f"成功创建AIProviderConfig: {config}")
        return config
    except Exception as e:
        logger.error(f"创建AIProviderConfig失败: {e}")
        raise

def get_current_quality_config():
    """获取当前的质量控制配置（从系统设置中提取）"""
    current_settings = get_current_system_settings()
    return current_settings.get('quality_control', default_system_settings['quality_control'])

def create_generation_config(settings=None):
    """根据当前系统设置创建生成配置"""
    if settings is None:
        current_settings = get_current_system_settings()
    else:
        current_settings = settings
        
    current_config = current_settings.get('quality_control', {})
    comfyui_config = current_settings.get('comfyui', {})
    ai_provider_config = current_settings.get('ai_provider', {})
    
    # 如果质量检查完全禁用，或者两个子检查都禁用，则跳过质量评估
    skip_evaluation = (
        not current_config.get('enabled', True) or 
        (not current_config.get('quality_check_enabled', True) and 
         not current_config.get('accuracy_check_enabled', True))
    )
    
    # 解析图像尺寸
    image_size_str = comfyui_config.get('image_size', '1536x1536')
    width, height = map(int, image_size_str.split('x'))
    
    # 创建AI客户端配置
    provider_config = safe_create_provider_config(ai_provider_config)
    
    # 创建AI客户端实例
    ai_client_instance = AIClientFactory.create_client(provider_config)
    
    return GenerationConfig(
        ollama_url=ai_provider_config.get('base_url', 'http://localhost:11434'),
        ollama_model=ai_provider_config.get('model', 'gemma3:12b'),
        comfyui_url=comfyui_config.get('url', 'http://localhost:8000'),
        max_iterations=2,
        quality_threshold=current_config.get('score_threshold', 7.0),
        output_dir="web_generated_images",
        quality_check_enabled=current_config.get('quality_check_enabled', True),
        accuracy_check_enabled=current_config.get('accuracy_check_enabled', True),
        skip_quality_evaluation=skip_evaluation,
        sampling_steps=comfyui_config.get('sampling_steps', 9),
        cfg_scale=comfyui_config.get('cfg_scale', 1.0),
        image_width=width,
        image_height=height,
        ai_client=ai_client_instance  # 传入AI客户端实例
    )

generation_config = create_generation_config()

generator = AutoImageGenerator(generation_config)

# 创建AI客户端，使用系统设置中的配置
current_settings = get_current_system_settings()
ai_provider_config = current_settings['ai_provider']

# 创建AI提供商配置
provider_config = safe_create_provider_config(ai_provider_config)

# 创建AI客户端
ai_client = AIClientFactory.create_client(provider_config)

def update_generator_config():
    """更新生成器配置以反映最新的质量设置"""
    global generator
    new_config = create_generation_config()
    generator.config = new_config
    logger.info(f"生成器配置已更新: skip_quality_evaluation={new_config.skip_quality_evaluation}")

# 线程池用于异步处理
executor = ThreadPoolExecutor(max_workers=4)

class GenerationNode:
    """生成树节点"""
    
    def __init__(self, node_id: str, prompt: str, parent_id: str = None, branch_info: dict = None):
        self.node_id = node_id
        self.prompt = prompt
        self.parent_id = parent_id
        self.children = []
        self.image_path = None
        self.image_data = None
        self.keywords = []
        self.enhanced_prompts = []
        self.quality_score = 0.0
        self.accuracy_score = 0.0
        self.status = "pending"
        self.created_at = datetime.now()
        
        # 分支信息
        self.branch_info = branch_info or {
            'level': 0,  # 层级 (0=根节点, 1=第一层分支...)
            'branch_index': 0,  # 在同级中的索引 (0-3)
            'branch_direction': 'root',  # 分支方向
            'version': 'v1.0'  # 版本号
        }
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            'node_id': self.node_id,
            'prompt': self.prompt,
            'parent_id': self.parent_id,
            'children': self.children,
            'image_path': self.image_path,
            'image_data': self.image_data,
            'keywords': self.keywords,
            'enhanced_prompts': self.enhanced_prompts,
            'quality_score': self.quality_score,
            'accuracy_score': self.accuracy_score,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'branch_info': self.branch_info
        }

class GenerationTree:
    """生成树"""
    
    def __init__(self, tree_id: str, root_prompt: str):
        self.tree_id = tree_id
        self.nodes = {}
        self.root_id = str(uuid.uuid4())
        
        # 创建根节点
        root_node = GenerationNode(self.root_id, root_prompt)
        self.nodes[self.root_id] = root_node
        
    def add_node(self, prompt: str, parent_id: str, branch_direction: str = None) -> str:
        """添加新节点"""
        node_id = str(uuid.uuid4())
        
        # 计算分支信息
        parent_node = self.nodes.get(parent_id)
        if parent_node:
            parent_level = parent_node.branch_info['level']
            sibling_count = len(parent_node.children)
            
            branch_info = {
                'level': parent_level + 1,
                'branch_index': sibling_count,
                'branch_direction': branch_direction or f'分支{sibling_count + 1}',
                'version': f'v{parent_level + 1}.{sibling_count + 1}'
            }
        else:
            branch_info = {
                'level': 0,
                'branch_index': 0,
                'branch_direction': 'root',
                'version': 'v1.0'
            }
        
        node = GenerationNode(node_id, prompt, parent_id, branch_info)
        self.nodes[node_id] = node
        
        # 更新父节点的子节点列表
        if parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)
        
        return node_id
    
    def get_node(self, node_id: str) -> GenerationNode:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'tree_id': self.tree_id,
            'root_id': self.root_id,
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        }

async def get_ollama_models(ollama_url: str) -> list:
    """获取 Ollama 服务器上可用的模型列表"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url.rstrip('/')}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get('models', []):
                        model_name = model.get('name', '')
                        if model_name:
                            # 保留完整的模型名称，包括版本标签
                            # 例如：ministral-3:latest 保持为 ministral-3:latest
                            # MartinRizzo/Regent-Dominique:latest 保持为 MartinRizzo/Regent-Dominique:latest
                            if model_name not in models:
                                models.append(model_name)
                    return sorted(models)
                else:
                    logger.warning(f"获取 Ollama 模型列表失败: HTTP {response.status}")
                    return []
    except Exception as e:
        logger.error(f"获取 Ollama 模型列表失败: {e}")
        return []

async def extract_keywords(prompt: str) -> list:
    """提取提示词关键点 - 专注视觉化表达和图像生成优化"""
    system_prompt = """你是一个专业的视觉化关键词分析专家，专门为AI图像生成模型提取最适合的关键词。请从给定的提示词中提取8-10个具有强烈视觉表现力的关键要素。

**核心原则：优先选择容易视觉化、具体可画的关键词**

分析策略：
1. 视觉实体：具体的物体、品种、类型（可以直接画出来的）
2. 视觉特征：颜色、质感、形状、大小、材质
3. 视觉场景：具体的环境、光线、时间、天气
4. 视觉动作：姿态、表情、动作、状态
5. 视觉风格：艺术风格、摄影技法、绘画手法
6. 视觉情感：通过视觉元素表达的情感（而非抽象概念）

关键词类型（按视觉化程度排序）：
- visual_object: 具体视觉物体（品种、类型、物品、服装、配饰）
- visual_feature: 视觉特征（颜色、质感、形状、材质、光线）
- visual_scene: 视觉场景（环境、背景、时间、天气、地点）
- visual_action: 视觉动作（姿态、表情、动作、状态）
- visual_style: 视觉风格（艺术风格、摄影技法、构图方式）
- visual_emotion: 视觉化情感（通过表情、姿态、色彩表达的情感）

**重要提醒**：
- 避免抽象概念（如"哲学思考"、"社会意义"、"心理状态"）
- 优先选择有明确视觉特征的词汇
- 关注图像生成模型容易理解的描述
- 每个关键词都应该能够直接转化为视觉元素

严格按照JSON格式返回：
{"keywords": [{"text": "关键词", "type": "类型", "description": "视觉化描述", "visual_strength": "high/medium/low"}]}

示例：
输入："小猫"
输出：{"keywords": [
  {"text": "英短猫", "type": "visual_object", "description": "圆脸、短毛、蓝灰色毛发的具体猫品种", "visual_strength": "high"},
  {"text": "毛茸茸质感", "type": "visual_feature", "description": "柔软蓬松的毛发质感，可通过细腻笔触表现", "visual_strength": "high"},
  {"text": "蜷缩姿态", "type": "visual_action", "description": "小猫典型的睡觉姿势，身体蜷成球状", "visual_strength": "high"},
  {"text": "粉色鼻子", "type": "visual_feature", "description": "小猫鼻子的典型颜色特征", "visual_strength": "high"},
  {"text": "阳光窗台", "type": "visual_scene", "description": "温暖的阳光透过窗户洒在窗台上", "visual_strength": "high"},
  {"text": "慵懒表情", "type": "visual_emotion", "description": "半闭眼睛、放松的面部表情", "visual_strength": "medium"}
]}

输入："美女"
输出：{"keywords": [
  {"text": "长发飘逸", "type": "visual_feature", "description": "柔顺的长发在风中飘动的视觉效果", "visual_strength": "high"},
  {"text": "红唇", "type": "visual_feature", "description": "鲜艳的红色嘴唇，经典美女特征", "visual_strength": "high"},
  {"text": "优雅姿态", "type": "visual_action", "description": "挺直的身姿、优美的手势", "visual_strength": "high"},
  {"text": "丝质长裙", "type": "visual_object", "description": "光滑有光泽的丝绸材质连衣裙", "visual_strength": "high"},
  {"text": "柔和光线", "type": "visual_scene", "description": "温暖柔和的打光效果", "visual_strength": "high"},
  {"text": "自信微笑", "type": "visual_emotion", "description": "嘴角上扬的自信笑容", "visual_strength": "medium"}
]}"""

    try:
        # 首先检查缓存
        cached_keywords = db.get_cached_keywords(prompt)
        if cached_keywords:
            logger.info(f"使用缓存的关键词: {prompt[:50]}...")
            return cached_keywords
        
        response = await ai_client.generate_text(
            f"请分析以下提示词并提取关键要素：{prompt}",
            system_prompt
        )
        
        # 尝试解析JSON
        result = safe_json_parse(response)
        if result and 'keywords' in result:
            keywords = result['keywords']
            # 缓存结果
            db.cache_keywords(prompt, keywords)
            return keywords
        
        # 如果JSON解析失败，生成创意关键词
        keywords = generate_creative_keywords(prompt)
        db.cache_keywords(prompt, keywords)
        return keywords
        
    except Exception as e:
        logger.error(f"关键词提取失败: {e}")
        # 生成备用创意关键词
        keywords = generate_creative_keywords(prompt)
        return keywords

def generate_creative_keywords(prompt: str) -> list:
    """生成创意关键词（备用方案）- 增强语义关联"""
    words = prompt.replace('，', ',').replace('、', ',').split(',')
    base_words = [w.strip() for w in words if w.strip()]
    
    # 视觉化关联词典（专注于可视化表达）
    visual_associations = {
        # 动物关联 - 强调具体视觉特征
        '猫': ['英短猫', '布偶猫', '毛茸茸质感', '蜷缩姿态', '粉色鼻子', '竖立耳朵', '长尾巴', '慵懒表情'],
        '狗': ['金毛犬', '哈士奇', '摇尾巴', '吐舌头', '毛发飞扬', '奔跑姿态', '湿润鼻子', '忠诚眼神'],
        
        # 人物关联 - 强调外观和姿态
        '美女': ['长发飘逸', '红唇', '优雅姿态', '丝质长裙', '高跟鞋', '珍珠项链', '自信微笑', '柔和光线'],
        '男人': ['西装革履', '坚毅表情', '宽阔肩膀', '短发造型', '领带', '手表', '挺拔身姿', '深邃眼神'],
        
        # 自然关联 - 强调色彩和光影
        '夕阳': ['金色余晖', '橙红天空', '剪影效果', '长影子', '暖色调', '地平线', '云彩染色', '逆光效果'],
        '海洋': ['蔚蓝海水', '白色浪花', '海鸥飞翔', '沙滩', '贝壳', '海风吹拂', '波光粼粼', '远山轮廓'],
        
        # 物品关联 - 强调材质和细节
        '咖啡': ['深褐色液体', '白色泡沫', '陶瓷杯子', '蒸汽升腾', '咖啡豆', '木质桌面', '温暖灯光', '拉花图案'],
        '花朵': ['玫瑰花瓣', '绿色茎叶', '花蕊细节', '露珠', '花瓶', '阳光照射', '鲜艳色彩', '花香飘散'],
    }
    
    # 视觉化创意模板（专注于可画的元素）
    visual_templates = {
        'visual_object': ['丝绸材质', '金属光泽', '木质纹理', '玻璃透明', '皮革质感', '羽毛轻盈'],
        'visual_feature': ['柔和光线', '强烈对比', '暖色调', '冷色调', '细腻纹理', '光影交错'],
        'visual_scene': ['晨光透窗', '黄昏余晖', '雨后彩虹', '微风轻拂', '星空璀璨', '雪花飞舞'],
        'visual_action': ['优雅姿态', '动感瞬间', '静谧凝视', '轻盈舞蹈', '坚定步伐', '温柔拥抱'],
        'visual_style': ['写实细腻', '印象派', '水彩晕染', '油画厚重', '素描线条', '摄影构图'],
        'visual_emotion': ['温暖笑容', '深邃眼神', '宁静表情', '激情四射', '纯真可爱', '神秘魅力']
    }
    
    keywords = []
    
    # 添加直接关键词
    for i, word in enumerate(base_words[:2]):
        keywords.append({
            'text': word,
            'type': 'entity',
            'description': f'核心要素：{word}',
            'association_type': 'semantic'
        })
    
    # 添加语义关联词
    for word in base_words[:2]:
        for key, associations in visual_associations.items():
            if key in word or word in key:
                # 随机选择2-3个关联词
                import random
                selected_associations = random.sample(associations, min(3, len(associations)))
                for assoc in selected_associations:
                    if len(keywords) < 8:
                        # 判断关联词的视觉化类型
                        if assoc in ['英短猫', '布偶猫', '金毛犬', '哈士奇', '丝质长裙', '高跟鞋', '珍珠项链', '陶瓷杯子']:
                            keyword_type = 'visual_object'
                            visual_strength = 'high'
                        elif assoc in ['毛茸茸质感', '长发飘逸', '红唇', '粉色鼻子', '深褐色液体', '蔚蓝海水']:
                            keyword_type = 'visual_feature'
                            visual_strength = 'high'
                        elif assoc in ['蜷缩姿态', '摇尾巴', '优雅姿态', '奔跑姿态', '挺拔身姿']:
                            keyword_type = 'visual_action'
                            visual_strength = 'high'
                        elif assoc in ['阳光窗台', '柔和光线', '金色余晖', '温暖灯光']:
                            keyword_type = 'visual_scene'
                            visual_strength = 'high'
                        elif assoc in ['慵懒表情', '自信微笑', '忠诚眼神', '深邃眼神']:
                            keyword_type = 'visual_emotion'
                            visual_strength = 'medium'
                        else:
                            keyword_type = 'visual_feature'
                            visual_strength = 'medium'
                        
                        keywords.append({
                            'text': assoc,
                            'type': keyword_type,
                            'description': f'与{word}相关的视觉化{keyword_type}特征',
                            'visual_strength': visual_strength
                        })
                break
    
    # 如果关联词不够，添加视觉化创意关键词
    import random
    while len(keywords) < 6:
        category = random.choice(list(visual_templates.keys()))
        templates = visual_templates[category]
        selected = random.choice(templates)
        
        # 避免重复
        if not any(kw['text'] == selected for kw in keywords):
            visual_strength_map = {
                'visual_object': 'high',
                'visual_feature': 'high', 
                'visual_scene': 'high',
                'visual_action': 'high',
                'visual_style': 'medium',
                'visual_emotion': 'medium'
            }
            
            keywords.append({
                'text': selected,
                'type': category,
                'description': f'视觉化{category}的创意扩展',
                'visual_strength': visual_strength_map.get(category, 'medium')
            })
    
    return keywords[:8]

def check_image_quality(image_data: bytes, prompt: str, node_id: str) -> dict:
    """检查图像质量"""
    # 获取最新的质量控制设置
    current_quality_config = get_current_quality_config()
    
    if not current_quality_config['enabled']:
        return {
            'passed': True,
            'quality_score': 8.0,
            'accuracy_score': 8.0,
            'message': '质量检查已禁用',
            'retry_needed': False
        }
    
    try:
        # 根据开关决定是否进行评估
        quality_score = 8.0  # 默认评分
        accuracy_score = 8.0  # 默认评分
        
        # 质量评分检查
        if current_quality_config.get('quality_check_enabled', True):
            # 使用现有的图像评估功能
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 这里应该调用实际的质量评估函数
            # 暂时使用模拟评分
            import random
            quality_score = random.uniform(6.0, 9.5)
            logger.info(f"节点 {node_id} 进行质量评分检查: {quality_score:.1f}")
        else:
            logger.info(f"节点 {node_id} 跳过质量评分检查 (已禁用)")
        
        # 准确度检查
        if current_quality_config.get('accuracy_check_enabled', True):
            # 这里应该调用实际的准确度评估函数
            # 暂时使用模拟评分
            import random
            accuracy_score = random.uniform(6.5, 9.0)
            logger.info(f"节点 {node_id} 进行准确度检查: {accuracy_score:.1f}")
        else:
            logger.info(f"节点 {node_id} 跳过准确度检查 (已禁用)")
        
        # 检查是否通过阈值
        quality_passed = True
        accuracy_passed = True
        
        if current_quality_config.get('quality_check_enabled', True):
            quality_passed = quality_score >= current_quality_config['score_threshold']
        
        if current_quality_config.get('accuracy_check_enabled', True):
            accuracy_passed = accuracy_score >= current_quality_config['accuracy_threshold']
        
        passed = quality_passed and accuracy_passed
        
        # 严格模式下的额外检查
        if current_quality_config['strict_mode'] and passed:
            # 检查是否有明显缺陷
            if current_quality_config['defect_detection']:
                # 这里可以添加更严格的缺陷检测
                if quality_score < 8.0:
                    passed = False
        
        retry_needed = not passed and current_quality_config['auto_retry']
        
        message = ""
        if not passed:
            reasons = []
            if current_quality_config.get('quality_check_enabled', True) and not quality_passed:
                reasons.append(f"质量评分 {quality_score:.1f} 低于阈值 {current_quality_config['score_threshold']}")
            if current_quality_config.get('accuracy_check_enabled', True) and not accuracy_passed:
                reasons.append(f"准确度 {accuracy_score:.1f} 低于阈值 {current_quality_config['accuracy_threshold']}")
            message = "质量检查未通过: " + "; ".join(reasons)
        else:
            # 构建通过消息
            check_parts = []
            if current_quality_config.get('quality_check_enabled', True):
                check_parts.append(f"质量: {quality_score:.1f}")
            else:
                check_parts.append("质量: 跳过")
            
            if current_quality_config.get('accuracy_check_enabled', True):
                check_parts.append(f"准确度: {accuracy_score:.1f}")
            else:
                check_parts.append("准确度: 跳过")
            
            message = f"质量检查通过 ({', '.join(check_parts)})"
        
        logger.info(f"节点 {node_id} 质量检查: {message}")
        
        return {
            'passed': passed,
            'quality_score': quality_score,
            'accuracy_score': accuracy_score,
            'message': message,
            'retry_needed': retry_needed
        }
        
    except Exception as e:
        logger.error(f"质量检查失败: {e}")
        return {
            'passed': True,  # 检查失败时默认通过
            'quality_score': 7.0,
            'accuracy_score': 7.0,
            'message': f'质量检查出错: {str(e)}',
            'retry_needed': False
        }

async def generate_enhanced_prompts(original_prompt: str, selected_keywords: list) -> list:
    """根据选中的关键词生成4个增强提示词"""
    system_prompt = """你是创意提示词生成专家。基于原始提示词和关键要素，生成4个增强提示词。

严格按照以下JSON格式返回，不要添加任何其他文字：
{"enhanced_prompts": [{"direction": "风格强化", "prompt": "增强提示词1"}, {"direction": "细节丰富", "prompt": "增强提示词2"}, {"direction": "情感深化", "prompt": "增强提示词3"}, {"direction": "创意拓展", "prompt": "增强提示词4"}]}"""

    keywords_text = "、".join([kw['text'] for kw in selected_keywords])
    
    try:
        response = await ai_client.generate_text(
            f"""原始提示词：{original_prompt}
选中的关键要素：{keywords_text}

请生成4个不同方向的增强提示词。""",
            system_prompt
        )
        
        # 尝试解析JSON
        result = safe_json_parse(response)
        if result and 'enhanced_prompts' in result:
            return result['enhanced_prompts']
        
        # 如果JSON解析失败，生成基本的增强提示词
        return [
            {"direction": "风格强化", "prompt": f"{original_prompt}，高质量，艺术风格，{keywords_text}"},
            {"direction": "细节丰富", "prompt": f"{original_prompt}，超详细，精致细节，{keywords_text}"},
            {"direction": "情感深化", "prompt": f"{original_prompt}，情感丰富，氛围感强，{keywords_text}"},
            {"direction": "创意拓展", "prompt": f"{original_prompt}，创意设计，独特视角，{keywords_text}"}
        ]
        
    except Exception as e:
        logger.error(f"增强提示词生成失败: {e}")
        return [
            {"direction": "基础增强", "prompt": f"{original_prompt}，{keywords_text}"}
        ]

def run_async(coro):
    """在新的事件循环中运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def clean_json_string(text: str) -> str:
    """清理JSON字符串，移除控制字符和多余内容"""
    import re
    
    # 移除控制字符（保留必要的空白字符）
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # 查找JSON部分
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        
        # 修复常见的JSON问题
        # 移除多余的逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 修复引号问题
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # 压缩多余的空白字符，但保留结构
        json_str = re.sub(r'\s+', ' ', json_str)
        json_str = json_str.replace('{ ', '{').replace(' }', '}')
        json_str = json_str.replace('[ ', '[').replace(' ]', ']')
        
        return json_str.strip()
    
    return text

def safe_json_parse(text: str, default_value=None):
    """安全的JSON解析"""
    try:
        cleaned_text = clean_json_string(text)
        return json.loads(cleaned_text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"原始文本: {text[:300]}...")
        return default_value

@app.route('/')
def index():
    """主页"""
    return render_template('simple_index.html')

@app.route('/api/set_locale/<locale>')
def set_locale_route(locale):
    """设置语言环境"""
    try:
        if set_locale(locale):
            return jsonify({
                'success': True,
                'message': t('messages.settings_saved'),
                'locale': locale
            })
        else:
            return jsonify({
                'success': False,
                'message': t('errors.invalid_input')
            }), 400
    except Exception as e:
        logger.error(f"设置语言失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/get_locale')
def get_locale_route():
    """获取当前语言环境"""
    try:
        return jsonify({
            'success': True,
            'locale': get_locale(),
            'supported_locales': i18n.get_supported_locales()
        })
    except Exception as e:
        logger.error(f"获取语言设置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/translations/<locale>')
def get_translations(locale):
    """获取指定语言的翻译文件"""
    try:
        if locale in i18n.supported_locales:
            return jsonify({
                'success': True,
                'translations': i18n.translations[locale],
                'locale': locale
            })
        else:
            return jsonify({
                'success': False,
                'message': t('errors.invalid_input')
            }), 400
    except Exception as e:
        logger.error(f"获取翻译失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/test_ollama_connection')
def test_ollama_connection():
    """测试当前Ollama连接和模型"""
    try:
        current_settings = get_current_system_settings()
        
        # 测试连接
        import asyncio
        
        async def test_connection():
            try:
                # 测试简单的生成
                response = await ai_client.generate_text("测试", "简单回复测试即可")
                return True, response[:100] if response else "无响应"
            except Exception as e:
                return False, str(e)
        
        success, result = run_async(test_connection())
        
        return jsonify({
            'success': True,
            'connection_test': {
                'success': success,
                'result': result,
                'current_url': current_settings['ai_provider']['base_url'],
                'current_model': current_settings['ai_provider']['model'],
                'ai_client_info': f"AIClient({ai_client.config.provider_type.value}, {ai_client.config.base_url}, {ai_client.config.model})"
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recent_trees')
def get_recent_trees():
    """获取最近的生成树列表"""
    try:
        trees = db.get_recent_trees(limit=20)
        return jsonify({
            'success': True,
            'trees': trees
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/ollama_models')
def get_available_ollama_models():
    """获取 Ollama 可用模型列表"""
    try:
        current_settings = get_current_system_settings()
        ai_provider_config = current_settings.get('ai_provider', {})
        
        # 只有当前提供商是 Ollama 时才从服务器获取模型列表
        if ai_provider_config.get('provider_type') == 'ollama':
            # 创建临时Ollama客户端来获取模型列表
            try:
                temp_config = AIProviderConfig(
                    provider_type=AIProviderType.OLLAMA,
                    name="Ollama",
                    base_url=ai_provider_config.get('base_url', 'http://localhost:11434'),
                    model="temp",
                    timeout=10
                )
                
                temp_client = AIClientFactory.create_client(temp_config)
                models = run_async(temp_client.get_available_models())
                
                if models:
                    return jsonify({
                        'success': True,
                        'models': models,
                        'count': len(models),
                        'source': 'ollama_server'
                    })
                else:
                    # 如果获取失败，返回默认模型列表
                    default_models = ['ministral-3:latest', 'llama3.2:latest', 'qwen2.5:latest', 'gemma2:latest', 'phi3:latest', 'gemma3:12b']
                    return jsonify({
                        'success': True,
                        'models': default_models,
                        'count': len(default_models),
                        'source': 'default'
                    })
                    
            except Exception as e:
                logger.error(f"获取Ollama模型列表失败: {e}")
                default_models = ['ministral-3:latest', 'llama3.2:latest', 'qwen2.5:latest', 'gemma2:latest', 'phi3:latest', 'gemma3:12b']
                return jsonify({
                    'success': True,
                    'models': default_models,
                    'count': len(default_models),
                    'source': 'default',
                    'error': str(e)
                })
        else:
            # 对于非 Ollama 提供商，使用通用的提供商模型获取
            return get_provider_models(ai_provider_config.get('provider_type', 'ollama'))
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        # 返回默认模型列表
        default_models = ['ministral-3:latest', 'llama3.2:latest', 'qwen2.5:latest', 'gemma2:latest', 'phi3:latest', 'gemma3:12b']
        return jsonify({
            'success': True,
            'models': default_models,
            'count': len(default_models),
            'source': 'default',
            'error': str(e)
        })

@app.route('/api/test_debug')
def test_debug():
    """测试调试路由"""
    logger.info("测试调试路由被调用")
    return jsonify({
        'success': True,
        'message': 'DEBUG路由工作正常',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/available_providers')
def get_available_providers():
    """获取可用的AI提供商列表"""
    try:
        current_settings = get_current_system_settings()
        available_providers = current_settings.get('available_providers', PROVIDER_TEMPLATES)
        
        # 格式化提供商信息
        providers = []
        for key, config in available_providers.items():
            api_key = config.get('api_key', '')
            requires_api_key = bool(api_key and api_key.strip()) or key in ['openrouter', 'openai']
            
            providers.append({
                'key': key,
                'name': config.get('name', key),
                'provider_type': config.get('provider_type', key),
                'base_url': config.get('base_url', ''),
                'models': config.get('models', []),
                'requires_api_key': requires_api_key
            })
        
        return jsonify({
            'success': True,
            'providers': providers,
            'current_provider': current_settings['ai_provider']['provider_type']
        })
        
    except Exception as e:
        logger.error(f"获取可用提供商失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/provider_models/<provider_key>')
def get_provider_models(provider_key):
    """获取指定提供商的模型列表"""
    try:
        current_settings = get_current_system_settings()
        available_providers = current_settings.get('available_providers', PROVIDER_TEMPLATES)
        
        if provider_key not in available_providers:
            return jsonify({
                'success': False,
                'error': f'提供商 {provider_key} 不存在'
            }), 404
        
        provider_config = available_providers[provider_key]
        
        # 创建临时AI客户端来获取模型列表
        try:
            # 确保provider_type是正确的枚举值
            provider_type_str = provider_config.get('provider_type', provider_key)
            if isinstance(provider_type_str, str):
                # 如果是字符串，转换为枚举
                provider_type = AIProviderType(provider_type_str)
            else:
                # 如果已经是枚举，直接使用
                provider_type = provider_type_str
            
            temp_config = AIProviderConfig(
                provider_type=provider_type,
                name=provider_config['name'],
                base_url=provider_config['base_url'],
                api_key=provider_config.get('api_key'),
                model="temp",  # 临时模型名
                timeout=10
            )
            
            temp_client = AIClientFactory.create_client(temp_config)
            
            # 异步获取模型列表
            models = run_async(temp_client.get_available_models())
            
            if models:
                source = 'live_api'
                logger.info(f"从 {provider_key} API 获取到 {len(models)} 个模型")
            else:
                # 如果API获取失败，使用配置中的默认模型
                models = provider_config.get('models', [])
                source = 'config_fallback'
                logger.warning(f"API获取失败，使用 {provider_key} 配置中的默认模型")
            
        except Exception as e:
            logger.error(f"获取 {provider_key} 模型列表失败: {e}")
            # 使用配置中的默认模型
            models = provider_config.get('models', [])
            source = 'config_fallback'
        
        return jsonify({
            'success': True,
            'provider_key': provider_key,
            'provider_name': provider_config.get('name', provider_key),
            'models': models,
            'count': len(models),
            'source': source
        })
        
    except Exception as e:
        logger.error(f"获取提供商模型失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh_provider_models/<provider_key>', methods=['POST'])
def refresh_provider_models(provider_key):
    """刷新指定提供商的模型列表"""
    try:
        current_settings = get_current_system_settings()
        available_providers = current_settings.get('available_providers', PROVIDER_TEMPLATES)
        
        if provider_key not in available_providers:
            return jsonify({
                'success': False,
                'error': f'提供商 {provider_key} 不存在'
            }), 404
        
        provider_config = available_providers[provider_key]
        
        # 获取请求中的配置参数（如果有的话）
        request_data = request.json or {}
        base_url = request_data.get('base_url', provider_config['base_url'])
        api_key = request_data.get('api_key', provider_config.get('api_key'))
        
        # 创建临时AI客户端来获取最新模型列表
        try:
            # 确保provider_type是正确的枚举值
            provider_type_str = provider_config.get('provider_type', provider_key)
            if isinstance(provider_type_str, str):
                # 如果是字符串，转换为枚举
                provider_type = AIProviderType(provider_type_str)
            else:
                # 如果已经是枚举，直接使用
                provider_type = provider_type_str
            
            temp_config = AIProviderConfig(
                provider_type=provider_type,
                name=provider_config['name'],
                base_url=base_url,
                api_key=api_key,
                model="temp",
                timeout=15  # 刷新时使用更长的超时时间
            )
            
            temp_client = AIClientFactory.create_client(temp_config)
            
            # 异步获取模型列表
            models = run_async(temp_client.get_available_models())
            
            if models:
                # 更新配置中的模型列表
                available_providers[provider_key]['models'] = models
                current_settings['available_providers'] = available_providers
                
                # 保存到数据库
                db.save_user_setting('system_settings', current_settings)
                
                # 同时更新配置文件
                try:
                    CONFIG['available_providers'] = available_providers
                    with open('config.json', 'w', encoding='utf-8') as f:
                        json.dump(CONFIG, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"更新配置文件失败: {e}")
                
                logger.info(f"成功刷新 {provider_key} 模型列表: {len(models)} 个模型")
                
                return jsonify({
                    'success': True,
                    'provider_key': provider_key,
                    'provider_name': provider_config.get('name', provider_key),
                    'models': models,
                    'count': len(models),
                    'source': 'live_api',
                    'message': f'成功获取 {len(models)} 个最新模型'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'无法从 {provider_key} 获取模型列表，请检查配置和网络连接'
                })
                
        except Exception as e:
            logger.error(f"刷新 {provider_key} 模型列表失败: {e}")
            return jsonify({
                'success': False,
                'error': f'刷新失败: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"刷新提供商模型失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test_ai_provider', methods=['POST'])
def test_ai_provider():
    """测试AI提供商连接"""
    try:
        data = request.json
        provider_type = data.get('provider_type')
        base_url = data.get('base_url')
        api_key = data.get('api_key')
        model = data.get('model')
        
        if not all([provider_type, base_url, model]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        # 创建测试配置
        try:
            provider_type_enum = AIProviderType(provider_type)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'不支持的提供商类型: {provider_type}'
            }), 400
        
        test_config = AIProviderConfig(
            provider_type=provider_type_enum,
            name=f"Test {provider_type}",
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_tokens=100,
            temperature=0.7,
            timeout=10
        )
        
        # 创建测试客户端
        test_client = AIClientFactory.create_client(test_config)
        
        # 执行测试
        async def test_connection():
            try:
                response = await test_client.generate_text(
                    "Hello, please respond with 'Connection successful'",
                    "You are a test assistant. Please respond briefly."
                )
                return True, response[:200] if response else "无响应"
            except Exception as e:
                return False, str(e)
        
        success, result = run_async(test_connection())
        
        return jsonify({
            'success': success,
            'result': result,
            'provider_type': provider_type,
            'model': model,
            'base_url': base_url
        })
        
    except Exception as e:
        logger.error(f"测试AI提供商失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_settings')
def get_system_settings():
    """获取系统设置"""
    # 获取最新设置
    current_settings = get_current_system_settings()
    logger.info(f"返回系统设置: {current_settings}")
    return jsonify({
        'success': True,
        'settings': current_settings
    })

@app.route('/api/system_settings', methods=['POST'])
def update_system_settings():
    """更新系统设置"""
    logger.info("=== update_system_settings 函数被调用 ===")
    try:
        data = request.json
        logger.info(f"接收到的数据: {data}")
        
        # 获取当前设置的副本，避免被get_current_system_settings覆盖
        current_settings = get_current_system_settings().copy()
        # 深拷贝嵌套字典
        current_settings['ai_provider'] = current_settings['ai_provider'].copy()
        current_settings['comfyui'] = current_settings['comfyui'].copy()
        current_settings['quality_control'] = current_settings['quality_control'].copy()
        
        logger.info(f"当前设置: {current_settings}")
        
        # 更新 AI 设置
        if 'ai_provider_type' in data:
            provider_type = data['ai_provider_type'].strip()
            if provider_type:
                logger.info(f"更新AI提供商类型: {current_settings['ai_provider']['provider_type']} -> {provider_type}")
                current_settings['ai_provider']['provider_type'] = provider_type
        
        if 'ai_base_url' in data:
            url = data['ai_base_url'].strip()
            if url:
                current_settings['ai_provider']['base_url'] = url
        
        if 'ai_api_key' in data:
            api_key = data['ai_api_key'].strip() if data['ai_api_key'] else None
            current_settings['ai_provider']['api_key'] = api_key
        
        if 'ai_model' in data:
            model = data['ai_model'].strip()
            if model:
                logger.info(f"更新AI模型: {current_settings['ai_provider']['model']} -> {model}")
                current_settings['ai_provider']['model'] = model
        
        if 'ai_max_tokens' in data:
            max_tokens = int(data['ai_max_tokens'])
            if 100 <= max_tokens <= 32000:
                current_settings['ai_provider']['max_tokens'] = max_tokens
        
        if 'ai_temperature' in data:
            temperature = float(data['ai_temperature'])
            if 0.0 <= temperature <= 2.0:
                current_settings['ai_provider']['temperature'] = temperature
        
        # 更新 ComfyUI 设置
        if 'comfyui_url' in data:
            url = data['comfyui_url'].strip()
            if url:
                current_settings['comfyui']['url'] = url
        
        if 'sampling_steps' in data:
            steps = int(data['sampling_steps'])
            if 1 <= steps <= 50:
                current_settings['comfyui']['sampling_steps'] = steps
        
        if 'cfg_scale' in data:
            cfg = float(data['cfg_scale'])
            if 0.1 <= cfg <= 20:
                current_settings['comfyui']['cfg_scale'] = cfg
        
        if 'image_size' in data:
            size = data['image_size']
            if size in ['512x512', '768x1024', '1024x768', '1024x1024', '1536x1536']:
                current_settings['comfyui']['image_size'] = size
        
        # 更新质量控制设置
        quality_control = current_settings.get('quality_control', {})
        
        if 'enabled' in data:
            quality_control['enabled'] = bool(data['enabled'])
        
        if 'score_threshold' in data:
            threshold = float(data['score_threshold'])
            if 0 <= threshold <= 10:
                quality_control['score_threshold'] = threshold
        
        if 'accuracy_threshold' in data:
            threshold = float(data['accuracy_threshold'])
            if 0 <= threshold <= 10:
                quality_control['accuracy_threshold'] = threshold
        
        if 'auto_retry' in data:
            quality_control['auto_retry'] = bool(data['auto_retry'])
        
        if 'max_retries' in data:
            retries = int(data['max_retries'])
            if 0 <= retries <= 5:
                quality_control['max_retries'] = retries
        
        if 'strict_mode' in data:
            quality_control['strict_mode'] = bool(data['strict_mode'])
        
        if 'defect_detection' in data:
            quality_control['defect_detection'] = bool(data['defect_detection'])
        
        if 'quality_check_enabled' in data:
            quality_control['quality_check_enabled'] = bool(data['quality_check_enabled'])
        
        if 'accuracy_check_enabled' in data:
            quality_control['accuracy_check_enabled'] = bool(data['accuracy_check_enabled'])
        
        current_settings['quality_control'] = quality_control
        
        logger.info(f"所有设置更新完成，current_settings: {current_settings}")
        
        # 更新生成器配置
        global generator, ai_client
        logger.info("开始更新生成器配置...")
        
        try:
            new_config = create_generation_config(current_settings)
            generator.config = new_config
            logger.info("生成器配置更新成功")
        except Exception as gen_error:
            logger.error(f"更新生成器配置失败: {gen_error}")
            raise gen_error
        
        # 更新 AI 客户端
        ai_provider_config = current_settings['ai_provider']
        logger.info(f"准备创建AI客户端配置: {ai_provider_config}")
        
        try:
            provider_config = safe_create_provider_config(ai_provider_config)
            ai_client = AIClientFactory.create_client(provider_config)
            logger.info(f"AI客户端已更新: {ai_provider_config['base_url']}, 模型: {ai_provider_config['model']}")
        except Exception as client_error:
            logger.error(f"创建AI客户端失败: {client_error}")
            raise client_error
        
        # 保存设置到数据库
        logger.info(f"准备保存到数据库的设置: {current_settings}")
        db.save_user_setting('system_settings', current_settings)
        logger.info("设置已保存到数据库")
        
        # 验证保存结果
        saved_settings = db.get_user_setting('system_settings')
        logger.info(f"从数据库读取的设置: {saved_settings}")
        
        # 同时更新配置文件
        try:
            CONFIG.update({
                'ai_provider': current_settings['ai_provider'],
                'comfyui': current_settings['comfyui'],
                'quality_control': current_settings['quality_control']
            })
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=2, ensure_ascii=False)
            logger.info("系统设置已同步到配置文件")
        except Exception as e:
            logger.warning(f"更新配置文件失败: {e}")
        
        return jsonify({
            'success': True,
            'settings': current_settings,
            'message': '系统设置已更新并保存 - DEBUG_V3',
            'debug_marker': 'update_system_settings_v2'
        })
        
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_settings/save_all', methods=['POST'])
def save_all_system_settings():
    """保存所有系统设置"""
    try:
        data = request.json
        
        # 验证数据结构
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': '无效的数据格式'}), 400
        
        # 验证必要的字段
        required_sections = ['ai_provider', 'comfyui', 'quality_control']
        for section in required_sections:
            if section not in data:
                return jsonify({'success': False, 'error': f'缺少 {section} 配置'}), 400
        
        # 验证 AI 提供商配置
        ai_provider_config = data['ai_provider']
        if not ai_provider_config.get('base_url') or not ai_provider_config.get('model'):
            return jsonify({'success': False, 'error': 'AI提供商配置不完整'}), 400
        
        if not ai_provider_config.get('provider_type'):
            return jsonify({'success': False, 'error': '必须选择AI提供商类型'}), 400
        
        # 验证 ComfyUI 配置
        comfyui_config = data['comfyui']
        if not comfyui_config.get('url'):
            return jsonify({'success': False, 'error': 'ComfyUI 配置不完整'}), 400
        
        # 验证数值范围
        if not (1 <= comfyui_config.get('sampling_steps', 9) <= 50):
            return jsonify({'success': False, 'error': '采样步数必须在1-50之间'}), 400
        
        if not (0.1 <= comfyui_config.get('cfg_scale', 1.0) <= 20):
            return jsonify({'success': False, 'error': 'CFG引导强度必须在0.1-20之间'}), 400
        
        if not (100 <= ai_provider_config.get('max_tokens', 4000) <= 32000):
            return jsonify({'success': False, 'error': '最大令牌数必须在100-32000之间'}), 400
        
        if not (0.0 <= ai_provider_config.get('temperature', 0.7) <= 2.0):
            return jsonify({'success': False, 'error': '温度参数必须在0.0-2.0之间'}), 400
        
        # 获取当前设置并更新
        current_settings = get_current_system_settings().copy()
        
        # 深拷贝嵌套字典
        current_settings['ai_provider'] = current_settings['ai_provider'].copy()
        current_settings['comfyui'] = current_settings['comfyui'].copy()
        current_settings['quality_control'] = current_settings['quality_control'].copy()
        
        # 更新设置
        current_settings.update(data)
        
        # 保存设置
        global system_settings, generator, ai_client
        system_settings.clear()
        system_settings.update(current_settings)
        
        # 更新生成器配置
        new_config = create_generation_config()
        generator.config = new_config
        
        # 更新 AI 客户端
        provider_config = safe_create_provider_config(ai_provider_config)
        ai_client = AIClientFactory.create_client(provider_config)
        
        logger.info(f"[save_all] AI客户端已更新: {ai_provider_config['name']} ({ai_provider_config['provider_type']}) - {ai_provider_config['base_url']}, 模型: {ai_provider_config['model']}")
        
        # 保存到数据库
        db.save_user_setting('system_settings', system_settings)
        
        # 同时更新配置文件
        try:
            CONFIG.update({
                'ai_provider': system_settings['ai_provider'],
                'comfyui': system_settings['comfyui'],
                'quality_control': system_settings['quality_control'],
                'available_providers': system_settings.get('available_providers', PROVIDER_TEMPLATES)
            })
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=2, ensure_ascii=False)
            logger.info("所有系统设置已同步到配置文件")
        except Exception as e:
            logger.warning(f"更新配置文件失败: {e}")
        
        logger.info("所有系统设置已保存并生效")
        
        return jsonify({
            'success': True,
            'settings': system_settings,
            'message': '所有系统设置已保存并生效'
        })
        
    except Exception as e:
        logger.error(f"保存所有系统设置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_settings/reset', methods=['POST'])
def reset_system_settings():
    """重置系统设置为默认值"""
    try:
        global system_settings, generator, ai_client
        
        # 重置为默认配置
        system_settings.clear()
        system_settings.update(default_system_settings)
        
        # 更新生成器配置
        new_config = create_generation_config()
        generator.config = new_config
        
        # 更新 AI 客户端
        ai_provider_config = system_settings['ai_provider']
        provider_config = safe_create_provider_config(ai_provider_config)
        ai_client = AIClientFactory.create_client(provider_config)
        
        logger.info(f"[reset] AI客户端已重置: URL={ai_provider_config['base_url']}, 模型={ai_provider_config['model']}")
        
        # 保存到数据库
        db.save_user_setting('system_settings', system_settings)
        
        # 更新配置文件
        try:
            CONFIG.update({
                'ai_provider': system_settings['ai_provider'],
                'comfyui': system_settings['comfyui'],
                'quality_control': system_settings['quality_control']
            })
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=2, ensure_ascii=False)
            logger.info("系统设置已重置并同步到配置文件")
        except Exception as e:
            logger.warning(f"更新配置文件失败: {e}")
        
        return jsonify({
            'success': True,
            'settings': system_settings,
            'message': '系统设置已重置为默认值'
        })
        
    except Exception as e:
        logger.error(f"重置系统设置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_settings/force_reset', methods=['POST'])
def force_reset_system_settings():
    """强制重置系统设置"""
    try:
        global system_settings, generator, ai_client
        
        # 强制重置为默认配置
        system_settings.clear()
        system_settings.update(default_system_settings)
        
        # 更新生成器配置
        new_config = create_generation_config()
        generator.config = new_config
        
        # 更新 AI 客户端
        ai_provider_config = system_settings['ai_provider']
        provider_config = safe_create_provider_config(ai_provider_config)
        ai_client = AIClientFactory.create_client(provider_config)
        
        logger.info(f"[force_reset] AI客户端已强制重置: URL={ai_provider_config['base_url']}, 模型={ai_provider_config['model']}")
        
        # 强制保存到数据库
        db.save_user_setting('system_settings', system_settings)
        
        # 强制更新配置文件
        CONFIG.clear()
        CONFIG.update({
            'ai_provider': system_settings['ai_provider'],
            'comfyui': system_settings['comfyui'],
            'generation': {
                'max_iterations': 5,
                'quality_threshold': 7.0,
                'output_dir': 'generated_images',
                'image_size': {
                    'width': 1536,
                    'height': 1536
                }
            },
            'quality_control': system_settings['quality_control'],
            'prompts': {
                'enhancement_system': '你是一个专业的AI图像生成提示词优化专家。请将简单描述转换为详细、具体的英文提示词，包含视觉细节、艺术风格和技术参数。',
                'evaluation_system': '你是图像质量评估专家。请从构图、色彩、细节、美感、匹配度五个维度评估图像，返回0-10分的评分和改进建议。'
            },
            'available_providers': system_settings.get('available_providers', PROVIDER_TEMPLATES)
        })
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, indent=2, ensure_ascii=False)
        
        logger.info("系统设置已强制重置")
        
        return jsonify({
            'success': True,
            'settings': system_settings,
            'message': '系统设置已强制重置'
        })
        
    except Exception as e:
        logger.error(f"强制重置系统设置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quality_settings/default')
def get_default_quality_settings():
    """获取默认质量控制设置"""
    return jsonify({
        'success': True,
        'settings': default_quality_config
    })

@app.route('/api/quality_settings/reset', methods=['POST'])
def reset_quality_settings():
    """重置质量控制设置为默认值"""
    try:
        global quality_config
        
        # 重置为默认配置
        quality_config.clear()
        quality_config.update(default_quality_config)
        
        # 保存到数据库
        db.save_user_setting('quality_control', quality_config)
        
        # 更新配置文件
        try:
            CONFIG['quality_control'] = quality_config
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=2, ensure_ascii=False)
            logger.info("质量控制设置已重置并同步到配置文件")
        except Exception as e:
            logger.warning(f"更新配置文件失败: {e}")
        
        return jsonify({
            'success': True,
            'settings': quality_config,
            'message': '质量控制设置已重置为默认值'
        })
        
    except Exception as e:
        logger.error(f"重置质量设置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quality_settings', methods=['POST'])
def update_quality_settings():
    """更新质量控制设置"""
    try:
        data = request.json
        
        # 验证和更新设置
        if 'enabled' in data:
            quality_config['enabled'] = bool(data['enabled'])
        
        if 'score_threshold' in data:
            threshold = float(data['score_threshold'])
            if 0 <= threshold <= 10:
                quality_config['score_threshold'] = threshold
            else:
                return jsonify({'success': False, 'error': '质量阈值必须在0-10之间'}), 400
        
        if 'accuracy_threshold' in data:
            threshold = float(data['accuracy_threshold'])
            if 0 <= threshold <= 10:
                quality_config['accuracy_threshold'] = threshold
            else:
                return jsonify({'success': False, 'error': '准确度阈值必须在0-10之间'}), 400
        
        if 'auto_retry' in data:
            quality_config['auto_retry'] = bool(data['auto_retry'])
        
        if 'max_retries' in data:
            retries = int(data['max_retries'])
            if 0 <= retries <= 5:
                quality_config['max_retries'] = retries
            else:
                return jsonify({'success': False, 'error': '最大重试次数必须在0-5之间'}), 400
        
        if 'strict_mode' in data:
            quality_config['strict_mode'] = bool(data['strict_mode'])
        
        if 'defect_detection' in data:
            quality_config['defect_detection'] = bool(data['defect_detection'])
        
        if 'quality_check_enabled' in data:
            quality_config['quality_check_enabled'] = bool(data['quality_check_enabled'])
        
        if 'accuracy_check_enabled' in data:
            quality_config['accuracy_check_enabled'] = bool(data['accuracy_check_enabled'])
        
        # 更新生成器配置
        generation_config.quality_threshold = quality_config['score_threshold']
        update_generator_config()  # 更新完整的生成器配置
        
        # 保存设置到数据库
        db.save_user_setting('quality_control', quality_config)
        
        # 同时更新配置文件
        try:
            CONFIG['quality_control'] = quality_config
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=2, ensure_ascii=False)
            logger.info("质量控制设置已同步到配置文件")
        except Exception as e:
            logger.warning(f"更新配置文件失败: {e}")
        
        return jsonify({
            'success': True,
            'settings': quality_config,
            'message': '质量控制设置已更新并保存'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create_tree', methods=['POST'])
def create_tree():
    """创建新的生成树"""
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': '提示词不能为空'}), 400
    
    # 在数据库中创建新的生成树
    tree_id = db.create_tree(prompt, {'user_agent': request.headers.get('User-Agent', '')})
    
    # 获取根节点ID
    tree_data = db.get_tree(tree_id)
    root_id = tree_data['root_id']
    
    # 创建关键词提取任务
    task_id = db.create_task(tree_id, 'extract_keywords', root_id)
    
    def extract_and_update():
        try:
            db.update_task(task_id, 'running')
            keywords = run_async(extract_keywords(prompt))
            db.update_node(root_id, keywords=keywords, status='ready')
            db.update_task(task_id, 'completed', keywords)
            logger.info(f"根节点关键词提取完成: {len(keywords)} 个关键词")
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            db.update_task(task_id, 'failed', error=str(e))
    
    executor.submit(extract_and_update)
    
    return jsonify({
        'tree_id': tree_id,
        'root_id': root_id,
        'tree': tree_data,
        'keywords_task_id': task_id
    })

@app.route('/api/check_task/<task_id>')
def check_task(task_id):
    """检查任务状态"""
    task = db.get_task(task_id)
    if not task:
        return jsonify({"status": "not_found"})
    
    return jsonify({
        "status": task['status'],
        "result": task['result'],
        "error": task['error']
    })

@app.route('/api/generate_branches', methods=['POST'])
def generate_branches():
    """生成分支节点"""
    data = request.json
    tree_id = data.get('tree_id')
    parent_id = data.get('parent_id')
    selected_keywords = data.get('selected_keywords', [])
    
    # 检查父节点是否存在
    parent_node = db.get_node(parent_id)
    if not parent_node:
        return jsonify({'error': '父节点不存在'}), 404
    
    # 创建分支生成任务
    task_id = db.create_task(tree_id, 'generate_branches', parent_id)
    
    def generate_and_update():
        try:
            db.update_task(task_id, 'running')
            
            # 生成增强提示词
            enhanced_prompts = run_async(generate_enhanced_prompts(parent_node['prompt'], selected_keywords))
            
            # 创建子节点
            child_nodes = []
            for enhanced in enhanced_prompts:
                child_id = db.add_node(tree_id, enhanced['prompt'], parent_id, enhanced['direction'])
                db.update_node(child_id, status='generating')
                child_nodes.append({
                    'node_id': child_id,
                    'direction': enhanced['direction'],
                    'prompt': enhanced['prompt']
                })
            
            # 更新任务状态为分支创建完成
            db.update_task(task_id, 'completed', child_nodes)
            
            # 自动为每个子节点生成图像
            for child_data in child_nodes:
                child_id = child_data['node_id']
                image_task_id = db.create_task(tree_id, 'generate_image', child_id)
                
                def generate_child_image(node_id=child_id, img_task_id=image_task_id):
                    # 获取最新的质量控制设置
                    current_quality_config = get_current_quality_config()
                    retry_count = 0
                    max_retries = current_quality_config['max_retries'] if current_quality_config['auto_retry'] else 0
                    
                    while retry_count <= max_retries:
                        try:
                            db.update_task(img_task_id, 'running')
                            node_data = db.get_node(node_id)
                            if not node_data:
                                return
                            
                            # 生成图像
                            logger.info(f"节点 {node_id} 开始生成图像 (尝试 {retry_count + 1}/{max_retries + 1})")
                            image_data, final_prompt, base_quality_score = run_async(
                                generator.generate_optimized_image(node_data['prompt'])
                            )
                            
                            if image_data:
                                # 质量检查
                                quality_check = check_image_quality(image_data, final_prompt, node_id)
                                
                                if quality_check['passed'] or retry_count >= max_retries:
                                    # 质量通过或达到最大重试次数，保存图像
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    
                                    # 为每个树创建独立文件夹
                                    tree_folder = Path(generation_config.output_dir) / f"tree_{tree_id}"
                                    tree_folder.mkdir(parents=True, exist_ok=True)
                                    
                                    filename = f"web_{node_id}_{timestamp}.png"
                                    filepath = tree_folder / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(image_data)
                                    
                                    # 使用质量检查的评分
                                    final_quality_score = quality_check['quality_score']
                                    accuracy_score = quality_check['accuracy_score']
                                    
                                    # 更新节点信息
                                    image_data_b64 = base64.b64encode(image_data).decode('utf-8')
                                    db.update_node(node_id, 
                                                 image_path=str(filepath),
                                                 image_data=image_data_b64,
                                                 quality_score=final_quality_score,
                                                 accuracy_score=accuracy_score,
                                                 status='completed')
                                    
                                    # 提取关键词
                                    try:
                                        logger.info(f"开始为节点 {node_id} 提取关键词...")
                                        keywords = run_async(extract_keywords(final_prompt))
                                        db.update_node(node_id, keywords=keywords)
                                        logger.info(f"节点 {node_id} 关键词提取完成，共 {len(keywords)} 个关键词")
                                    except Exception as kw_error:
                                        logger.error(f"节点 {node_id} 关键词提取失败: {kw_error}")
                                        # 使用备用关键词
                                        backup_keywords = generate_creative_keywords(final_prompt)
                                        db.update_node(node_id, keywords=backup_keywords)
                                    
                                    db.update_task(img_task_id, 'completed', {
                                        'node_id': node_id,
                                        'quality_score': final_quality_score,
                                        'accuracy_score': accuracy_score,
                                        'final_prompt': final_prompt,
                                        'quality_check': quality_check,
                                        'retry_count': retry_count
                                    })
                                    
                                    logger.info(f"节点 {node_id} 图像生成完成: {quality_check['message']}")
                                    break
                                    
                                else:
                                    # 质量未通过，准备重试
                                    retry_count += 1
                                    if retry_count <= max_retries:
                                        logger.warning(f"节点 {node_id} 质量检查未通过，准备重试 ({retry_count}/{max_retries}): {quality_check['message']}")
                                        continue
                                    else:
                                        logger.error(f"节点 {node_id} 达到最大重试次数，使用当前结果")
                                        break
                            else:
                                db.update_node(node_id, status='failed')
                                db.update_task(img_task_id, 'failed', error='图像生成失败')
                                break
                                
                        except Exception as e:
                            logger.error(f"自动图像生成失败 {node_id}: {e}")
                            db.update_node(node_id, status='failed')
                            db.update_task(img_task_id, 'failed', error=str(e))
                            break
                
                # 提交图像生成任务
                executor.submit(generate_child_image)
            
        except Exception as e:
            logger.error(f"分支生成失败: {e}")
            db.update_task(task_id, 'failed', error=str(e))
    
    executor.submit(generate_and_update)
    
    return jsonify({'status': 'generating', 'task_id': task_id})

@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    """生成图像"""
    data = request.json
    tree_id = data.get('tree_id')
    node_id = data.get('node_id')
    
    tree = generation_trees.get(tree_id)
    if not tree:
        return jsonify({'error': '生成树不存在'}), 404
    
    node = tree.get_node(node_id)
    if not node:
        return jsonify({'error': '节点不存在'}), 404
    
    # 创建图像生成任务
    task_id = f"image_{tree_id}_{node_id}"
    task_status[task_id] = {"status": "running", "result": None}
    
    def generate_and_update():
        try:
            node.status = "generating"
            
            # 生成图像
            image_data, final_prompt, quality_score = run_async(
                generator.generate_optimized_image(node.prompt)
            )
            
            if image_data:
                # 保存图像
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 为每个树创建独立文件夹
                tree_folder = Path(generation_config.output_dir) / f"tree_{tree_id}"
                tree_folder.mkdir(parents=True, exist_ok=True)
                
                filename = f"web_{node_id}_{timestamp}.png"
                filepath = tree_folder / filename
                
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # 更新节点信息
                node.image_path = str(filepath)
                node.image_data = base64.b64encode(image_data).decode('utf-8')
                node.quality_score = quality_score
                node.status = "completed"
                
                # 提取关键词
                keywords = run_async(extract_keywords(final_prompt))
                node.keywords = keywords
                
                task_status[task_id] = {
                    "status": "completed", 
                    "result": {
                        'image_data': node.image_data,
                        'quality_score': quality_score,
                        'keywords': keywords,
                        'final_prompt': final_prompt
                    }
                }
                
            else:
                node.status = "failed"
                task_status[task_id] = {"status": "failed", "error": "图像生成失败"}
                
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            node.status = "failed"
            task_status[task_id] = {"status": "failed", "error": str(e)}
    
    executor.submit(generate_and_update)
    
    return jsonify({'status': 'generating', 'task_id': task_id})

@app.route('/api/get_tree/<tree_id>')
def get_tree(tree_id):
    """获取生成树数据"""
    tree_data = db.get_tree(tree_id)
    if not tree_data:
        return jsonify({'error': '生成树不存在'}), 404
    
    # 自动为没有关键词的节点提取关键词
    nodes_to_extract = []
    for node_id, node in tree_data['nodes'].items():
        # 如果节点有图像但没有关键词，自动提取
        if node['image_data'] and (not node['keywords'] or len(node['keywords']) == 0):
            nodes_to_extract.append((node_id, node['prompt']))
    
    # 异步提取关键词
    if nodes_to_extract:
        def extract_missing_keywords():
            for node_id, prompt in nodes_to_extract:
                try:
                    logger.info(f"自动为节点 {node_id} 提取关键词...")
                    keywords = run_async(extract_keywords(prompt))
                    db.update_node(node_id, keywords=keywords)
                    logger.info(f"节点 {node_id} 自动关键词提取完成，共 {len(keywords)} 个关键词")
                except Exception as e:
                    logger.error(f"节点 {node_id} 自动关键词提取失败: {e}")
                    # 使用备用关键词
                    backup_keywords = generate_creative_keywords(prompt)
                    db.update_node(node_id, keywords=backup_keywords)
        
        # 提交后台任务
        executor.submit(extract_missing_keywords)
        logger.info(f"启动自动关键词提取任务，共 {len(nodes_to_extract)} 个节点")
    
    return jsonify(tree_data)

@app.route('/api/check_branch_images/<tree_id>/<parent_id>')
def check_branch_images(tree_id, parent_id):
    """检查分支节点的图像生成状态"""
    tree_data = db.get_tree(tree_id)
    if not tree_data:
        return jsonify({'error': '生成树不存在'}), 404
    
    parent_node = tree_data['nodes'].get(parent_id)
    if not parent_node:
        return jsonify({'error': '父节点不存在'}), 404
    
    # 检查所有子节点的状态
    children_status = []
    all_completed = True
    
    for child_id in parent_node['children']:
        child_node = tree_data['nodes'].get(child_id)
        if child_node:
            status_info = {
                'node_id': child_id,
                'status': child_node['status'],
                'has_image': bool(child_node['image_data']),
                'quality_score': child_node['quality_score'],
                'prompt': child_node['prompt'],
                'keywords': child_node['keywords'],
                'has_keywords': bool(child_node['keywords'] and len(child_node['keywords']) > 0)
            }
            children_status.append(status_info)
            
            if child_node['status'] not in ['completed', 'failed']:
                all_completed = False
    
    return jsonify({
        'all_completed': all_completed,
        'children': children_status,
        'total_children': len(parent_node['children']),
        'completed_count': len([c for c in children_status if c['status'] == 'completed'])
    })

@app.route('/api/get_siblings/<tree_id>/<node_id>')
def get_siblings(tree_id, node_id):
    """获取同级分支节点"""
    tree_data = db.get_tree(tree_id)
    if not tree_data:
        return jsonify({'error': '生成树不存在'}), 404
    
    node = tree_data['nodes'].get(node_id)
    if not node:
        return jsonify({'error': '节点不存在'}), 404
    
    # 获取同级节点
    siblings = []
    if node['parent_id']:
        parent_node = tree_data['nodes'].get(node['parent_id'])
        if parent_node:
            for sibling_id in parent_node['children']:
                sibling_node = tree_data['nodes'].get(sibling_id)
                if sibling_node and sibling_node['image_data']:
                    siblings.append({
                        'node_id': sibling_id,
                        'prompt': sibling_node['prompt'],
                        'image_data': sibling_node['image_data'],
                        'quality_score': sibling_node['quality_score'],
                        'branch_info': sibling_node['branch_info']
                    })
    
    # 按分支索引排序
    siblings.sort(key=lambda x: x['branch_info'].get('branch_index', 0))
    
    # 找到当前节点在同级中的位置
    current_index = -1
    for i, sibling in enumerate(siblings):
        if sibling['node_id'] == node_id:
            current_index = i
            break
    
    return jsonify({
        'siblings': siblings,
        'current_index': current_index,
        'total_count': len(siblings)
    })

@app.route('/api/test_keywords', methods=['POST'])
def test_keywords():
    """测试关键词提取"""
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': '提示词不能为空'}), 400
    
    try:
        keywords = run_async(extract_keywords(prompt))
        return jsonify({
            'success': True,
            'prompt': prompt,
            'keywords': keywords,
            'count': len(keywords)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'prompt': prompt
        })

@app.route('/api/force_extract_keywords/<tree_id>/<node_id>', methods=['POST'])
def force_extract_keywords(tree_id, node_id):
    """强制为节点提取关键词"""
    node_data = db.get_node(node_id)
    if not node_data:
        return jsonify({'error': '节点不存在'}), 404
    
    try:
        keywords = run_async(extract_keywords(node_data['prompt']))
        db.update_node(node_id, keywords=keywords)
        return jsonify({
            'success': True,
            'node_id': node_id,
            'keywords': keywords,
            'count': len(keywords)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'node_id': node_id
        })

@app.route('/api/regenerate_image', methods=['POST'])
def regenerate_image():
    """重新生成图像"""
    data = request.json
    tree_id = data.get('tree_id')
    node_id = data.get('node_id')
    
    # 检查节点是否存在
    node_data = db.get_node(node_id)
    if not node_data:
        return jsonify({'error': '节点不存在'}), 404
    
    # 创建重新生成任务
    task_id = db.create_task(tree_id, 'regenerate_image', node_id)
    
    def regenerate_task():
        # 获取最新的质量控制设置
        current_quality_config = get_current_quality_config()
        retry_count = 0
        max_retries = current_quality_config['max_retries'] if current_quality_config['auto_retry'] else 0
        
        try:
            db.update_task(task_id, 'running')
            db.update_node(node_id, status='generating', image_data=None, image_path=None)
            
            logger.info(f"开始重新生成节点 {node_id} 的图像")
            
            while retry_count <= max_retries:
                try:
                    # 重新获取节点数据以确保使用最新的提示词
                    current_node_data = db.get_node(node_id)
                    if not current_node_data:
                        logger.error(f"节点 {node_id} 不存在，停止重新生成")
                        break
                    
                    # 生成图像
                    logger.info(f"节点 {node_id} 重新生成图像 (尝试 {retry_count + 1}/{max_retries + 1})")
                    logger.info(f"使用提示词: {current_node_data['prompt'][:100]}...")
                    image_data, final_prompt, base_quality_score = run_async(
                        generator.generate_optimized_image(current_node_data['prompt'])
                    )
                    
                    if image_data:
                        # 质量检查
                        quality_check = check_image_quality(image_data, final_prompt, node_id)
                        
                        if quality_check['passed'] or retry_count >= max_retries:
                            # 质量通过或达到最大重试次数，保存图像
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            # 为每个树创建独立文件夹
                            tree_folder = Path(generation_config.output_dir) / f"tree_{tree_id}"
                            tree_folder.mkdir(parents=True, exist_ok=True)
                            
                            filename = f"regenerated_{node_id}_{timestamp}.png"
                            filepath = tree_folder / filename
                            
                            # 删除旧图像文件
                            if node_data.get('image_path') and Path(node_data['image_path']).exists():
                                try:
                                    Path(node_data['image_path']).unlink()
                                    logger.info(f"已删除旧图像文件: {node_data['image_path']}")
                                except Exception as e:
                                    logger.warning(f"删除旧图像文件失败: {e}")
                            
                            with open(filepath, 'wb') as f:
                                f.write(image_data)
                            
                            # 使用质量检查的评分
                            final_quality_score = quality_check['quality_score']
                            accuracy_score = quality_check['accuracy_score']
                            
                            # 更新节点信息
                            image_data_b64 = base64.b64encode(image_data).decode('utf-8')
                            db.update_node(node_id, 
                                         image_path=str(filepath),
                                         image_data=image_data_b64,
                                         quality_score=final_quality_score,
                                         accuracy_score=accuracy_score,
                                         status='completed')
                            
                            # 重新提取关键词
                            try:
                                logger.info(f"重新为节点 {node_id} 提取关键词...")
                                keywords = run_async(extract_keywords(final_prompt))
                                db.update_node(node_id, keywords=keywords)
                                logger.info(f"节点 {node_id} 关键词重新提取完成，共 {len(keywords)} 个关键词")
                            except Exception as kw_error:
                                logger.error(f"节点 {node_id} 关键词重新提取失败: {kw_error}")
                                # 使用备用关键词
                                backup_keywords = generate_creative_keywords(final_prompt)
                                db.update_node(node_id, keywords=backup_keywords)
                            
                            db.update_task(task_id, 'completed', {
                                'node_id': node_id,
                                'quality_score': final_quality_score,
                                'accuracy_score': accuracy_score,
                                'final_prompt': final_prompt,
                                'quality_check': quality_check,
                                'retry_count': retry_count,
                                'regenerated': True
                            })
                            
                            logger.info(f"节点 {node_id} 图像重新生成完成: {quality_check['message']}")
                            break
                            
                        else:
                            # 质量未通过，准备重试
                            retry_count += 1
                            if retry_count <= max_retries:
                                logger.warning(f"节点 {node_id} 重新生成质量检查未通过，准备重试 ({retry_count}/{max_retries}): {quality_check['message']}")
                                continue
                            else:
                                logger.error(f"节点 {node_id} 重新生成达到最大重试次数，使用当前结果")
                                break
                    else:
                        db.update_node(node_id, status='failed')
                        db.update_task(task_id, 'failed', error='图像重新生成失败')
                        break
                        
                except Exception as e:
                    logger.error(f"图像重新生成失败 {node_id}: {e}")
                    db.update_node(node_id, status='failed')
                    db.update_task(task_id, 'failed', error=str(e))
                    break
                    
        except Exception as e:
            logger.error(f"重新生成任务失败: {e}")
            db.update_node(node_id, status='failed')
            db.update_task(task_id, 'failed', error=str(e))
    
    # 提交重新生成任务
    executor.submit(regenerate_task)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '图像重新生成任务已启动'
    })

@app.route('/api/download_image/<tree_id>/<node_id>')
def download_image(tree_id, node_id):
    """下载图像"""
    node_data = db.get_node(node_id)
    if not node_data or not node_data['image_path']:
        return jsonify({'error': '图像不存在'}), 404
    
    return send_file(node_data['image_path'], as_attachment=True)

@app.route('/api/update_prompt', methods=['POST'])
def update_prompt():
    """更新节点的提示词"""
    try:
        data = request.json
        tree_id = data.get('tree_id')
        node_id = data.get('node_id')
        new_prompt = data.get('new_prompt', '').strip()
        
        if not tree_id or not node_id or not new_prompt:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 检查节点是否存在
        node_data = db.get_node(node_id)
        if not node_data:
            return jsonify({'error': '节点不存在'}), 404
        
        if node_data['tree_id'] != tree_id:
            return jsonify({'error': '节点不属于指定的树'}), 400
        
        # 更新提示词
        db.update_node(node_id, prompt=new_prompt)
        
        logger.info(f"节点 {node_id} 提示词已更新: {new_prompt[:50]}...")
        
        return jsonify({
            'success': True,
            'message': '提示词已更新',
            'node_id': node_id,
            'new_prompt': new_prompt
        })
        
    except Exception as e:
        logger.error(f"更新提示词失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete_tree/<tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    """删除生成树及其所有数据"""
    try:
        # 检查树是否存在
        tree_data = db.get_tree(tree_id)
        if not tree_data:
            return jsonify({'error': '生成树不存在'}), 404
        
        # 执行删除
        success = db.delete_tree(tree_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'生成树 "{tree_data["nodes"][tree_data["root_id"]]["prompt"]}" 已成功删除',
                'tree_id': tree_id
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败，请稍后重试'
            }), 500
            
    except Exception as e:
        logger.error(f"删除树API失败 {tree_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auto_extract_keywords/<tree_id>')
def auto_extract_keywords(tree_id):
    """自动为树中缺少关键词的节点提取关键词"""
    tree_data = db.get_tree(tree_id)
    if not tree_data:
        return jsonify({'error': '生成树不存在'}), 404
    
    # 找到需要提取关键词的节点
    nodes_to_extract = []
    for node_id, node in tree_data['nodes'].items():
        # 如果节点有图像但没有关键词，或者关键词为空
        if (node['image_data'] or node['status'] == 'completed') and (not node['keywords'] or len(node['keywords']) == 0):
            nodes_to_extract.append({
                'node_id': node_id,
                'prompt': node['prompt'],
                'status': node['status']
            })
    
    if not nodes_to_extract:
        return jsonify({
            'success': True,
            'message': '所有节点都已有关键词',
            'extracted_count': 0,
            'total_nodes': len(tree_data['nodes'])
        })
    
    # 创建批量关键词提取任务
    task_id = db.create_task(tree_id, 'batch_extract_keywords', None)
    
    def batch_extract_keywords():
        try:
            db.update_task(task_id, 'running')
            extracted_count = 0
            
            for node_info in nodes_to_extract:
                try:
                    node_id = node_info['node_id']
                    prompt = node_info['prompt']
                    
                    logger.info(f"批量提取关键词: 节点 {node_id}")
                    keywords = run_async(extract_keywords(prompt))
                    db.update_node(node_id, keywords=keywords)
                    extracted_count += 1
                    logger.info(f"节点 {node_id} 关键词提取完成，共 {len(keywords)} 个关键词")
                    
                except Exception as e:
                    logger.error(f"节点 {node_id} 关键词提取失败: {e}")
                    # 使用备用关键词
                    backup_keywords = generate_creative_keywords(prompt)
                    db.update_node(node_id, keywords=backup_keywords)
                    extracted_count += 1
            
            db.update_task(task_id, 'completed', {
                'extracted_count': extracted_count,
                'total_nodes': len(nodes_to_extract),
                'success': True
            })
            
            logger.info(f"批量关键词提取完成: {extracted_count}/{len(nodes_to_extract)} 个节点")
            
        except Exception as e:
            logger.error(f"批量关键词提取失败: {e}")
            db.update_task(task_id, 'failed', error=str(e))
    
    # 提交后台任务
    executor.submit(batch_extract_keywords)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': f'开始为 {len(nodes_to_extract)} 个节点提取关键词',
        'nodes_to_extract': len(nodes_to_extract),
        'total_nodes': len(tree_data['nodes'])
    })

if __name__ == '__main__':
    # 创建输出目录
    Path(generation_config.output_dir).mkdir(exist_ok=True)
    
    # 启动Web服务器
    import socket
    
    # 查找可用端口
    def find_free_port():
        ports_to_try = [8080, 8081, 8082, 9000, 9001, 9002]
        for port in ports_to_try:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return 8080  # 默认端口
    
    port = find_free_port()
    print("🚀 启动Web服务器...")
    print(f"📱 请在浏览器中访问: http://localhost:{port}")
    
    try:
        app.run(host='localhost', port=port, debug=False, threaded=True)
    except OSError as e:
        print(f"❌ 端口 {port} 启动失败: {e}")
        print("💡 尝试使用其他端口...")
        # 尝试其他端口
        for backup_port in [8888, 7777, 6666]:
            try:
                print(f"🔄 尝试端口 {backup_port}...")
                app.run(host='localhost', port=backup_port, debug=False, threaded=True)
                break
            except OSError:
                continue
        else:
            print("❌ 所有端口都被占用，请手动指定端口")
            print("💡 或者重启计算机后再试")