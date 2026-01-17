#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Image Tree System 启动脚本
简化的启动入口
"""

import os
import sys
import json
from pathlib import Path

# 强制设置UTF-8编码（Windows兼容性）
if sys.platform.startswith('win'):
    import locale
    import codecs
    
    try:
        # 设置控制台代码页为UTF-8
        os.system('chcp 65001 >nul 2>&1')
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # 重新配置标准输入输出流
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        else:
            # 对于较老的Python版本，使用包装器
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach(), errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach(), errors='replace')
        
        # 设置默认编码
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')
            
        # 设置locale
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                pass  # 忽略locale设置失败
                
    except Exception as e:
        print(f"Warning: Failed to set UTF-8 encoding: {e}")
        pass

def check_config():
    """检查配置文件"""
    config_file = Path("config.json")
    if not config_file.exists():
        print("❌ 配置文件不存在")
        print("💡 请先运行: python setup.py")
        return False
    
    try:
        # 强制使用UTF-8编码读取配置文件
        with open(config_file, 'r', encoding='utf-8', errors='replace') as f:
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
        
        # 更安全的方式启动应用 - 直接导入而不是使用importlib
        try:
            # 直接导入app模块
            import app
            # 如果app模块有main函数，调用它；否则直接运行Flask应用
            if hasattr(app, 'main'):
                app.main()
            elif hasattr(app, 'app'):
                # 启动Flask应用
                app.app.run(host='localhost', port=8080, debug=False, threaded=True)
            else:
                print("❌ 无法找到应用入口点")
                sys.exit(1)
                
        except ImportError as e:
            print(f"❌ 导入应用模块失败: {e}")
            print("💡 请检查app.py文件是否存在且语法正确")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请检查配置和依赖")
        
        # 输出更详细的错误信息用于调试
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main()