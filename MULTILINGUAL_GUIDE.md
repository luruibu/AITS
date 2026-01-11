# 多语言支持指南 / Multi-language Support Guide

本文档说明如何使用和扩展 AI Image Tree 系统的多语言功能。

This document explains how to use and extend the multi-language functionality of the AI Image Tree system.

## 🌍 支持的语言 / Supported Languages

目前系统支持以下语言：

Currently, the system supports the following languages:

- 🇨🇳 **简体中文** (zh_CN) - Chinese Simplified
- 🇺🇸 **English** (en_US) - English  
- 🇯🇵 **日本語** (ja_JP) - Japanese

## 🔄 语言切换 / Language Switching

### 在Web界面中切换 / Switch in Web Interface

1. 在页面右上角找到语言选择器 / Find the language selector in the top-right corner
2. 点击下拉菜单选择语言 / Click the dropdown menu to select language
3. 页面会自动刷新并应用新语言 / Page will automatically refresh and apply the new language

### 自动语言检测 / Automatic Language Detection

系统会按以下优先级自动检测语言：

The system automatically detects language in the following priority:

1. **用户选择** / User Selection - 用户在界面中选择的语言 / Language selected by user in interface
2. **浏览器语言** / Browser Language - 浏览器的Accept-Language头 / Browser's Accept-Language header
3. **默认语言** / Default Language - 简体中文 (zh_CN) / Chinese Simplified (zh_CN)

## 🛠️ 开发者指南 / Developer Guide

### 添加新语言 / Adding New Languages

#### 1. 创建翻译文件 / Create Translation File

在 `i18n/` 目录下创建新的JSON文件：

Create a new JSON file in the `i18n/` directory:

```bash
# 例如添加法语支持 / For example, adding French support
touch i18n/fr_FR.json
```

#### 2. 复制翻译结构 / Copy Translation Structure

复制 `en_US.json` 的结构并翻译所有值：

Copy the structure from `en_US.json` and translate all values:

```json
{
  "app": {
    "title": "Générateur d'Arbre d'Images IA",
    "subtitle": "Système de génération d'arbres d'images créatives alimenté par l'IA",
    "description": "Expansion créative infinie grâce à l'exploration par branches"
  },
  "nav": {
    "home": "Accueil",
    "settings": "Paramètres Système",
    "history": "Historique",
    "help": "Aide"
  },
  // ... 更多翻译 / more translations
}
```

#### 3. 更新语言映射 / Update Language Mapping

在 `i18n_utils.py` 中添加语言名称映射：

Add language name mapping in `i18n_utils.py`:

```python
locale_names = {
    'zh_CN': '简体中文',
    'en_US': 'English',
    'ja_JP': '日本語',
    'fr_FR': 'Français',  # 新增 / New addition
    # ... 其他语言 / other languages
}
```

#### 4. 测试新语言 / Test New Language

重启应用并测试新语言：

Restart the application and test the new language:

```bash
python app.py
```

访问 `http://localhost:8080` 并在语言选择器中查看新语言。

Visit `http://localhost:8080` and check for the new language in the language selector.

### 翻译文件结构 / Translation File Structure

翻译文件使用嵌套JSON结构：

Translation files use nested JSON structure:

```json
{
  "category": {
    "subcategory": {
      "key": "翻译文本 / Translation text"
    }
  }
}
```

#### 主要分类 / Main Categories

- `app` - 应用程序基本信息 / Basic app information
- `nav` - 导航菜单 / Navigation menu
- `main` - 主界面元素 / Main interface elements
- `settings` - 设置面板 / Settings panel
- `providers` - AI提供商名称 / AI provider names
- `messages` - 系统消息 / System messages
- `errors` - 错误消息 / Error messages
- `help` - 帮助文档 / Help documentation
- `history` - 历史记录 / History records

### 在代码中使用翻译 / Using Translations in Code

#### 后端 Python / Backend Python

```python
from i18n_utils import t

# 基本翻译 / Basic translation
message = t('messages.success')

# 带参数的翻译 / Translation with parameters
message = t('messages.welcome', name='用户名')
```

#### 前端 JavaScript / Frontend JavaScript

```javascript
// 基本翻译 / Basic translation
const message = t('messages.success');

// 带参数的翻译 / Translation with parameters
const message = t('messages.welcome', {name: '用户名'});
```

#### HTML 模板 / HTML Templates

```html
<!-- 基本翻译 / Basic translation -->
<h1 data-i18n="app.title">默认文本</h1>

<!-- 占位符翻译 / Placeholder translation -->
<input data-i18n-placeholder="main.input_placeholder" placeholder="默认占位符">

<!-- 标题翻译 / Title translation -->
<button data-i18n-title="help.tooltip" title="默认提示">按钮</button>
```

## 🔧 配置选项 / Configuration Options

### 默认语言设置 / Default Language Setting

在 `i18n_utils.py` 中修改默认语言：

Modify the default language in `i18n_utils.py`:

```python
class I18nManager:
    def __init__(self, i18n_dir: str = "i18n", default_locale: str = "zh_CN"):
        # 修改 default_locale 参数 / Modify default_locale parameter
        self.default_locale = default_locale
```

### 语言检测优先级 / Language Detection Priority

系统按以下顺序检测语言：

The system detects language in the following order:

1. Session中的用户选择 / User selection in session
2. HTTP Accept-Language头 / HTTP Accept-Language header
3. 默认语言设置 / Default language setting

## 📝 翻译指南 / Translation Guidelines

### 翻译原则 / Translation Principles

1. **保持一致性** / Maintain Consistency - 相同概念使用相同翻译 / Use same translation for same concepts
2. **简洁明了** / Be Concise - 避免冗长的翻译 / Avoid lengthy translations
3. **符合习惯** / Follow Conventions - 使用目标语言的常用表达 / Use common expressions in target language
4. **保留格式** / Preserve Format - 保持占位符和格式标记 / Keep placeholders and format markers

### 特殊字符处理 / Special Character Handling

- 保留HTML标签 / Preserve HTML tags: `<strong>`, `<em>`, etc.
- 保留占位符 / Preserve placeholders: `{name}`, `{count}`, etc.
- 保留转义字符 / Preserve escape characters: `\n`, `\t`, etc.

### 文本长度考虑 / Text Length Considerations

不同语言的文本长度差异很大，需要考虑：

Different languages have varying text lengths, consider:

- 界面布局适应性 / Interface layout adaptability
- 按钮和标签的空间 / Space for buttons and labels
- 响应式设计兼容性 / Responsive design compatibility

## 🧪 测试多语言功能 / Testing Multi-language Features

### 手动测试 / Manual Testing

1. 切换到每种支持的语言 / Switch to each supported language
2. 检查所有界面元素是否正确翻译 / Check if all interface elements are correctly translated
3. 测试动态内容的翻译 / Test translation of dynamic content
4. 验证错误消息的翻译 / Verify translation of error messages

### 自动化测试 / Automated Testing

创建测试脚本验证翻译完整性：

Create test scripts to verify translation completeness:

```python
import json
from pathlib import Path

def test_translation_completeness():
    """测试翻译文件的完整性"""
    base_file = Path('i18n/en_US.json')
    base_data = json.loads(base_file.read_text(encoding='utf-8'))
    
    for lang_file in Path('i18n').glob('*.json'):
        if lang_file.name == 'en_US.json':
            continue
            
        lang_data = json.loads(lang_file.read_text(encoding='utf-8'))
        missing_keys = find_missing_keys(base_data, lang_data)
        
        if missing_keys:
            print(f"Missing keys in {lang_file.name}: {missing_keys}")
```

## 🚀 部署注意事项 / Deployment Considerations

### 服务器配置 / Server Configuration

确保服务器支持UTF-8编码：

Ensure server supports UTF-8 encoding:

```python
# Flask 应用配置 / Flask app configuration
app.config['JSON_AS_ASCII'] = False
```

### 缓存策略 / Caching Strategy

考虑翻译文件的缓存策略：

Consider caching strategy for translation files:

- 开发环境：禁用缓存 / Development: Disable caching
- 生产环境：启用缓存 / Production: Enable caching

## 📚 参考资源 / Reference Resources

### 国际化标准 / Internationalization Standards

- [ISO 639-1 语言代码](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) / Language Codes
- [ISO 3166-1 国家代码](https://en.wikipedia.org/wiki/ISO_3166-1) / Country Codes
- [Unicode 标准](https://unicode.org/) / Unicode Standard

### 翻译工具 / Translation Tools

- [Google Translate](https://translate.google.com/) - 机器翻译 / Machine translation
- [DeepL](https://www.deepl.com/) - 高质量机器翻译 / High-quality machine translation
- [Crowdin](https://crowdin.com/) - 协作翻译平台 / Collaborative translation platform

## 🤝 贡献翻译 / Contributing Translations

欢迎贡献新语言的翻译！

Welcome to contribute translations for new languages!

### 贡献流程 / Contribution Process

1. Fork 项目 / Fork the project
2. 创建新的翻译文件 / Create new translation file
3. 完成翻译并测试 / Complete translation and test
4. 提交 Pull Request / Submit Pull Request

### 翻译质量要求 / Translation Quality Requirements

- 准确性 / Accuracy - 翻译准确无误 / Accurate translation
- 完整性 / Completeness - 所有键值都已翻译 / All keys translated
- 一致性 / Consistency - 术语使用一致 / Consistent terminology
- 本地化 / Localization - 符合当地习惯 / Follow local conventions

---

如有问题或建议，请提交 Issue 或参与 Discussions。

For questions or suggestions, please submit an Issue or join Discussions.