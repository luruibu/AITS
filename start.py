#!/usr/bin/env python3
"""
AI Image Tree System 启动脚本
简化的启动入口
"""

import os
import sys
import json
from pathlib import Path

def check_config():
    """检查配置文件"""
    config_file = Path("config.json")
    if not config_file.exists():
        print("❌ 配置文件不存在")
        print("💡 请先运行: python setup.py")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查基本配置
        if not config.get('ai_provider', {}).get('base_url'):
            print("⚠️ AI提供商配置不完整，请检查 config.json")
        
        if not config.get('comfyui', {}).get('url'):
            print("⚠️ ComfyUI配置不完整，请检查 config.json")
        
        return True
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

def check_dependencies():
    """检查依赖"""
    required_modules = ['flask', 'aiohttp', 'asyncio']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主启动流程"""
    print("🚀 启动 AI Image Tree System...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        sys.exit(1)
    
    # 启动应用
    try:
        print("✅ 检查通过，启动应用...")
        from app import app
        
        # 导入主应用并启动
        if __name__ == "__main__":
            exec(open("app.py").read())
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查配置和依赖")
        sys.exit(1)

if __name__ == "__main__":
    main()