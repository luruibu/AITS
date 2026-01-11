#!/usr/bin/env python3
"""
AI Image Tree System Setup Script
自动化安装和配置脚本
"""

import os
import sys
import json
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    print(f"✅ Python 版本检查通过: {sys.version}")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装Python依赖...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 依赖安装成功")
            return True
        else:
            print(f"❌ 依赖安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 依赖安装出错: {e}")
        return False

def setup_config():
    """设置配置文件"""
    print("\n⚙️ 设置配置文件...")
    
    config_file = Path("config.json")
    example_file = Path("config.json.example")
    
    if config_file.exists():
        print("⚠️ config.json 已存在，跳过配置")
        return True
    
    if not example_file.exists():
        print("❌ config.json.example 不存在")
        return False
    
    try:
        shutil.copy(example_file, config_file)
        print("✅ 配置文件创建成功")
        print("💡 请编辑 config.json 配置你的AI服务")
        return True
    except Exception as e:
        print(f"❌ 配置文件创建失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建项目目录...")
    
    directories = [
        "generated_images",
        "web_generated_images",
        "logs"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"✅ 目录创建成功: {dir_name}")
        except Exception as e:
            print(f"❌ 目录创建失败 {dir_name}: {e}")
            return False
    
    return True

def check_services():
    """检查外部服务"""
    print("\n🔍 检查外部服务...")
    
    # 这里可以添加对Ollama和ComfyUI的连接检查
    print("💡 请确保以下服务正在运行:")
    print("   - Ollama (默认: http://localhost:11434)")
    print("   - ComfyUI (默认: http://localhost:8000)")
    
    return True

def main():
    """主安装流程"""
    print("🚀 AI Image Tree System 安装向导")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 安装失败，请检查网络连接和权限")
        sys.exit(1)
    
    # 设置配置
    if not setup_config():
        print("\n❌ 配置设置失败")
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        print("\n❌ 目录创建失败")
        sys.exit(1)
    
    # 检查服务
    check_services()
    
    print("\n" + "=" * 50)
    print("🎉 安装完成！")
    print("\n📋 下一步:")
    print("1. 编辑 config.json 配置你的AI服务")
    print("2. 启动 Ollama 和 ComfyUI 服务")
    print("3. 运行: python app.py")
    print("4. 访问: http://localhost:8080")
    print("\n📚 更多信息请查看 README.md")

if __name__ == "__main__":
    main()