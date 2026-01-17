#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化工具类
提供多语言支持功能
"""

import sys
import os

# Windows编码兼容性设置
if sys.platform.startswith('win'):
    import codecs
    try:
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # 重新配置标准输入输出流
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        else:
            # 对于较老的Python版本，使用包装器
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach(), errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach(), errors='replace')
    except Exception:
        pass

import json
from pathlib import Path
from typing import Dict, Any, Optional
from flask import session, request

class I18nManager:
    """国际化管理器"""
    
    def __init__(self, i18n_dir: str = "i18n", default_locale: str = "zh_CN"):
        self.i18n_dir = Path(i18n_dir)
        self.default_locale = default_locale
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.supported_locales = []
        self.load_translations()
    
    def load_translations(self):
        """加载所有翻译文件"""
        if not self.i18n_dir.exists():
            print(f"Warning: i18n directory {self.i18n_dir} does not exist")
            return
        
        for file_path in self.i18n_dir.glob("*.json"):
            locale = file_path.stem
            try:
                # 强制使用UTF-8编码读取翻译文件
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.translations[locale] = json.load(f)
                self.supported_locales.append(locale)
                print(f"Loaded translations for locale: {locale}")
            except Exception as e:
                print(f"Error loading translations for {locale}: {e}")
        
        if not self.supported_locales:
            print("Warning: No translation files loaded")
    
    def get_current_locale(self) -> str:
        """获取当前语言环境"""
        # 1. 从 session 中获取用户选择的语言
        try:
            if 'locale' in session:
                locale = session['locale']
                if locale in self.supported_locales:
                    return locale
        except RuntimeError:
            # 在Flask请求上下文之外，跳过session检查
            pass
        
        # 2. 从 HTTP Accept-Language 头获取
        try:
            if request and hasattr(request, 'accept_languages'):
                for lang in request.accept_languages:
                    # 处理 'zh-CN' -> 'zh_CN' 格式转换
                    locale = lang[0].replace('-', '_')
                    if locale in self.supported_locales:
                        return locale
                    # 尝试匹配语言前缀，如 'zh' 匹配 'zh_CN'
                    lang_prefix = locale.split('_')[0]
                    for supported in self.supported_locales:
                        if supported.startswith(lang_prefix):
                            return supported
        except RuntimeError:
            # 在Flask请求上下文之外，跳过request检查
            pass
        
        # 3. 返回默认语言
        return self.default_locale
    
    def set_locale(self, locale: str):
        """设置当前语言环境"""
        if locale in self.supported_locales:
            try:
                session['locale'] = locale
                return True
            except RuntimeError:
                # 在Flask请求上下文之外，无法设置session
                print(f"Warning: Cannot set locale in session outside request context")
                return False
        return False
    
    def get_translation(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """获取翻译文本"""
        if locale is None:
            locale = self.get_current_locale()
        
        # 如果指定的语言不存在，使用默认语言
        if locale not in self.translations:
            locale = self.default_locale
        
        # 如果默认语言也不存在，返回原始key
        if locale not in self.translations:
            return key
        
        # 支持嵌套key，如 'app.title'
        translation_dict = self.translations[locale]
        keys = key.split('.')
        
        try:
            for k in keys:
                translation_dict = translation_dict[k]
            
            # 支持字符串格式化
            if isinstance(translation_dict, str) and kwargs:
                return translation_dict.format(**kwargs)
            
            return str(translation_dict)
        except (KeyError, TypeError):
            # 如果key不存在，尝试从默认语言获取
            if locale != self.default_locale:
                return self.get_translation(key, self.default_locale, **kwargs)
            return key
    
    def get_supported_locales(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        locale_names = {
            'zh_CN': '简体中文',
            'en_US': 'English',
            'zh_TW': '繁體中文',
            'ja_JP': '日本語',
            'ko_KR': '한국어',
            'fr_FR': 'Français',
            'de_DE': 'Deutsch',
            'es_ES': 'Español',
            'ru_RU': 'Русский'
        }
        
        return {
            locale: locale_names.get(locale, locale)
            for locale in self.supported_locales
        }

# 全局实例
i18n = I18nManager()

def t(key: str, **kwargs) -> str:
    """翻译函数的简写形式"""
    return i18n.get_translation(key, **kwargs)

def get_locale() -> str:
    """获取当前语言环境的简写形式"""
    return i18n.get_current_locale()

def set_locale(locale: str) -> bool:
    """设置语言环境的简写形式"""
    return i18n.set_locale(locale)

# Flask 模板函数
def register_i18n_functions(app):
    """注册国际化函数到Flask模板"""
    app.jinja_env.globals['t'] = t
    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['get_supported_locales'] = i18n.get_supported_locales