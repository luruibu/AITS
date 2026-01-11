#!/usr/bin/env python3
"""
ComfyUI 自动安装脚本
为 AI Image Tree 项目自动安装和配置 ComfyUI
"""

import os
import sys
import subprocess
import urllib.request
import json
from pathlib import Path
import shutil
import platform

class ComfyUIInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.comfyui_dir = Path("ComfyUI")
        self.models_info = {
            "unet": {
                "filename": "z_image_turbo_bf16.safetensors",
                "url": "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/flux1-schnell.safetensors",
                "size": "23.8GB"
            },
            "clip": {
                "filename": "qwen_3_4b.safetensors", 
                "url": "https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct/resolve/main/model.safetensors",
                "size": "8.2GB"
            },
            "vae": {
                "filename": "ae.safetensors",
                "url": "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors", 
                "size": "335MB"
            }
        }
    
    def print_header(self):
        print("=" * 60)
        print("🎨 ComfyUI 自动安装脚本")
        print("   为 AI Image Tree 项目配置 ComfyUI")
        print("=" * 60)
        print()
    
    def check_requirements(self):
        """检查系统要求"""
        print("🔍 检查系统要求...")
        
        # 检查 Python 版本
        python_version = sys.version_info
        if python_version < (3, 8):
            print("❌ Python 版本过低")
            print(f"   当前版本: {python_version.major}.{python_version.minor}")
            print("   需要版本: 3.8+")
            return False
        elif python_version >= (3, 12):
            print("⚠️ Python 版本较新")
            print(f"   当前版本: {python_version.major}.{python_version.minor}")
            print("   推荐版本: 3.8-3.11")
            print("   某些依赖可能不兼容，但会尝试继续安装")
        else:
            print(f"✅ Python 版本: {python_version.major}.{python_version.minor}")
        
        print(f"✅ Python 版本: {python_version.major}.{python_version.minor}")
        
        # 检查 Git
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            print("✅ Git 已安装")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git 未安装，请先安装 Git")
            return False
        
        # 检查可用空间
        free_space = shutil.disk_usage(".").free / (1024**3)  # GB
        if free_space < 50:
            print(f"⚠️ 磁盘空间不足: {free_space:.1f}GB 可用")
            print("   建议至少 50GB 可用空间")
            response = input("是否继续安装? (y/N): ")
            if response.lower() != 'y':
                return False
        
        print(f"✅ 磁盘空间: {free_space:.1f}GB 可用")
        return True
    
    def clone_comfyui(self):
        """克隆 ComfyUI 仓库"""
        print("\n📥 克隆 ComfyUI 仓库...")
        
        if self.comfyui_dir.exists():
            print("⚠️ ComfyUI 目录已存在")
            response = input("是否删除并重新克隆? (y/N): ")
            if response.lower() == 'y':
                shutil.rmtree(self.comfyui_dir)
            else:
                print("跳过克隆步骤")
                return True
        
        try:
            subprocess.run([
                "git", "clone", 
                "https://github.com/comfyanonymous/ComfyUI.git",
                str(self.comfyui_dir)
            ], check=True)
            print("✅ ComfyUI 克隆完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 克隆失败: {e}")
            return False
    
    def install_dependencies(self):
        """安装 Python 依赖"""
        print("\n📦 安装 Python 依赖...")
        
        requirements_file = self.comfyui_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt 文件不存在")
            return False
        
        try:
            # 升级 pip
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # 安装依赖
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file)
            ], check=True)
            
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def create_model_directories(self):
        """创建模型目录结构"""
        print("\n📁 创建模型目录...")
        
        model_dirs = [
            "models/checkpoints",
            "models/clip", 
            "models/unet",
            "models/vae",
            "models/controlnet",
            "models/loras"
        ]
        
        for dir_path in model_dirs:
            full_path = self.comfyui_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {dir_path}")
        
        return True
    
    def download_file(self, url, filepath, description):
        """下载文件并显示进度"""
        print(f"📥 下载 {description}...")
        print(f"   URL: {url}")
        print(f"   保存到: {filepath}")
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"\r   进度: {percent}% ", end="", flush=True)
        
        try:
            urllib.request.urlretrieve(url, filepath, progress_hook)
            print(f"\n✅ {description} 下载完成")
            return True
        except Exception as e:
            print(f"\n❌ {description} 下载失败: {e}")
            return False
    
    def download_models(self):
        """下载必需的模型文件"""
        print("\n🤖 下载模型文件...")
        print("⚠️ 注意: 模型文件较大，下载可能需要较长时间")
        
        total_size = 0
        for model_type, info in self.models_info.items():
            total_size += float(info["size"].replace("GB", "").replace("MB", "")) * (1000 if "GB" in info["size"] else 1)
        
        print(f"📊 总下载大小: 约 {total_size/1000:.1f}GB")
        
        response = input("是否现在下载模型文件? (y/N): ")
        if response.lower() != 'y':
            print("⏭️ 跳过模型下载")
            print("💡 请手动下载模型文件，参考 COMFYUI_SETUP.md")
            return True
        
        success_count = 0
        for model_type, info in self.models_info.items():
            model_dir = self.comfyui_dir / "models" / model_type
            filepath = model_dir / info["filename"]
            
            if filepath.exists():
                print(f"⏭️ {info['filename']} 已存在，跳过下载")
                success_count += 1
                continue
            
            if self.download_file(info["url"], filepath, info["filename"]):
                success_count += 1
        
        print(f"\n📊 模型下载完成: {success_count}/{len(self.models_info)}")
        return success_count > 0
    
    def create_startup_script(self):
        """创建启动脚本"""
        print("\n📝 创建启动脚本...")
        
        if self.system == "windows":
            script_content = f"""@echo off
echo 🚀 启动 ComfyUI 服务器...
cd /d "{self.comfyui_dir.absolute()}"
python main.py --listen 0.0.0.0 --port 8000
pause
"""
            script_path = "start_comfyui.bat"
        else:
            script_content = f"""#!/bin/bash
echo "🚀 启动 ComfyUI 服务器..."
cd "{self.comfyui_dir.absolute()}"
python main.py --listen 0.0.0.0 --port 8000
"""
            script_path = "start_comfyui.sh"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if self.system != "windows":
            os.chmod(script_path, 0o755)
        
        print(f"✅ 启动脚本已创建: {script_path}")
        return True
    
    def test_installation(self):
        """测试安装"""
        print("\n🧪 测试安装...")
        
        # 检查主要文件
        main_py = self.comfyui_dir / "main.py"
        if not main_py.exists():
            print("❌ main.py 文件不存在")
            return False
        
        print("✅ ComfyUI 主文件存在")
        
        # 检查模型目录
        models_dir = self.comfyui_dir / "models"
        if not models_dir.exists():
            print("❌ 模型目录不存在")
            return False
        
        print("✅ 模型目录存在")
        
        # 检查已下载的模型
        model_count = 0
        for model_type, info in self.models_info.items():
            model_path = models_dir / model_type / info["filename"]
            if model_path.exists():
                model_count += 1
                print(f"✅ 模型文件存在: {info['filename']}")
            else:
                print(f"⚠️ 模型文件缺失: {info['filename']}")
        
        print(f"📊 模型文件: {model_count}/{len(self.models_info)} 已下载")
        return True
    
    def print_next_steps(self):
        """打印后续步骤"""
        print("\n" + "=" * 60)
        print("🎉 ComfyUI 安装完成！")
        print("=" * 60)
        print()
        print("📋 后续步骤:")
        print()
        print("1. 启动 ComfyUI:")
        if self.system == "windows":
            print("   双击 start_comfyui.bat")
        else:
            print("   ./start_comfyui.sh")
        print("   或手动运行:")
        print(f"   cd {self.comfyui_dir}")
        print("   python main.py --listen 0.0.0.0 --port 8000")
        print()
        print("2. 验证安装:")
        print("   在浏览器中访问: http://localhost:8000")
        print("   导入工作流文件: comfyui_workflow.json")
        print()
        print("3. 配置 AI Image Tree:")
        print("   确保 config.json 中 ComfyUI URL 为: http://localhost:8000")
        print()
        print("4. 如果缺少模型文件:")
        print("   参考 COMFYUI_SETUP.md 手动下载")
        print()
        print("🆘 如遇问题，请查看 COMFYUI_SETUP.md 故障排除部分")
        print()
    
    def run(self):
        """运行安装流程"""
        self.print_header()
        
        if not self.check_requirements():
            print("❌ 系统要求检查失败，安装终止")
            return False
        
        if not self.clone_comfyui():
            print("❌ ComfyUI 克隆失败，安装终止")
            return False
        
        if not self.install_dependencies():
            print("❌ 依赖安装失败，安装终止")
            return False
        
        if not self.create_model_directories():
            print("❌ 模型目录创建失败，安装终止")
            return False
        
        self.download_models()  # 允许跳过
        
        if not self.create_startup_script():
            print("❌ 启动脚本创建失败")
            return False
        
        if not self.test_installation():
            print("❌ 安装测试失败")
            return False
        
        self.print_next_steps()
        return True

def main():
    installer = ComfyUIInstaller()
    success = installer.run()
    
    if success:
        print("✅ 安装成功完成！")
        sys.exit(0)
    else:
        print("❌ 安装失败")
        sys.exit(1)

if __name__ == "__main__":
    main()