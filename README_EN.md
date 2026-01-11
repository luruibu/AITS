# AI Image Tree System

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

🌳 An AI-powered creative image generation tree system that supports multiple AI providers and enables infinite creative expansion through branching exploration.

## ✨ Features

- 🤖 **Multiple AI Provider Support**: Ollama (Local) / OpenRouter (Cloud) / OpenAI (Official) / Custom API
- 🌐 **Dynamic Model Fetching**: Real-time retrieval of latest available model lists from APIs
- 🎨 **Smart Interface**: Automatically adjusts configuration interface based on provider type
- 🌳 **Tree Generation**: Keyword-based branching exploration and creative expansion
- 🔄 **Quality Control**: Configurable image quality assessment and automatic retry
- 💾 **Persistent Storage**: SQLite database for generation history and settings
- 📱 **Responsive Web Interface**: Modern user interface design
- 🌍 **Multi-language Support**: Chinese/English interface with easy language switching

## 🚀 Quick Start

### System Requirements

- Python 3.8+
- ComfyUI (for image generation)
- Ollama (optional, for local AI models)

> 📖 For detailed installation instructions, see [INSTALL.md](INSTALL.md)
> 🎨 For ComfyUI setup guide, see [COMFYUI_SETUP.md](COMFYUI_SETUP.md)

### Installation Steps

#### Method 1: Automatic Installation (Recommended)

1. **Clone the Project**
```bash
git clone https://github.com/your-username/ai-image-tree.git
cd ai-image-tree
```

2. **Auto-install ComfyUI**
```bash
python install_comfyui.py
```

3. **Run Installation Script**
```bash
python setup.py
```

4. **Configure Settings**
Edit the `config.json` file to configure your AI service addresses and API keys

5. **Start Services**
```bash
# Start ComfyUI (new terminal window)
./start_comfyui.sh  # Linux/Mac
# or
start_comfyui.bat   # Windows

# Start AI Image Tree
python start.py
```

#### Method 2: Manual Installation

1. **Clone the Project**
```bash
git clone https://github.com/your-username/ai-image-tree.git
cd ai-image-tree
```

2. **Install ComfyUI**
```bash
# Refer to COMFYUI_SETUP.md for manual installation
# or use the auto script
python install_comfyui.py
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Settings**
```bash
cp config.json.example config.json
# Edit config.json to configure your AI services
```

5. **Start Application**
```bash
# Start ComfyUI (port 8000)
cd ComfyUI
python main.py --listen 0.0.0.0 --port 8000

# Start AI Image Tree (new terminal, port 8080)
cd ..
python app.py
```

6. **Access Interface**
Open browser and visit: http://localhost:8080

### Quick Launch

#### Windows Users
Double-click the `start.bat` file, or run in command line:
```cmd
start.bat
```

#### Linux/Mac Users
Run in terminal:
```bash
chmod +x start.sh
./start.sh
```

#### Universal Method
```bash
python start.py
```

## 🔧 Configuration

### AI Provider Configuration

The system supports multiple AI providers, switchable in the web interface system settings:

#### Ollama (Local)
- No API key required
- Supports various locally deployed open-source models
- Default address: `http://localhost:11434`

#### OpenRouter (Cloud)
- Requires API key (get from [OpenRouter](https://openrouter.ai))
- Supports 350+ cloud models
- Includes Claude, GPT-4, Gemini, etc.

#### OpenAI (Official)
- Requires API key (get from [OpenAI](https://openai.com))
- Supports GPT-4o, GPT-4o-mini, and other official models

#### Custom API
- Supports any OpenAI-compatible API service
- Configurable custom addresses and authentication

### ComfyUI Configuration

Ensure ComfyUI is running and accessible:
- Default address: `http://localhost:8000`
- Supports custom sampling steps, CFG guidance scale, and other parameters

#### Test ComfyUI Connection

Use the test script to verify ComfyUI configuration:

```bash
# Test default address (localhost:8000)
python test_comfyui_connection.py

# Test custom address
python test_comfyui_connection.py http://192.168.100.249:8000
```

The test script checks:
- ComfyUI API connection status
- Workflow file compatibility
- Required model file existence

## 📖 Usage Guide

### Basic Usage

1. **Enter Prompt**: Input your creative description in the main interface
2. **Generate Root Node**: System extracts keywords and generates initial image
3. **Select Keywords**: Choose interesting directions from extracted keywords
4. **Generate Branches**: System generates 4 branch images based on selected keywords
5. **Continue Exploration**: Continue expanding new creative directions from any branch node

### Advanced Features

- **System Settings**: Configure AI providers, model parameters, quality control, etc.
- **Model Switching**: Real-time switching between different AI models
- **Quality Control**: Enable image quality assessment and automatic retry
- **History Management**: View and manage previous generation trees
- **Language Switching**: Switch between Chinese and English interfaces

## 🌍 Multi-language Support

The system supports multiple languages with easy switching:

### Supported Languages
- 🇨🇳 **Chinese (Simplified)** - 简体中文
- 🇺🇸 **English** - English

### Language Switching
- Use the language selector in the top-right corner of the interface
- Language preference is automatically saved
- All interface elements are translated including:
  - Navigation menus
  - Settings panels
  - Error messages
  - Help documentation

### Adding New Languages

To add support for a new language:

1. Create a new translation file in the `i18n/` directory (e.g., `fr_FR.json`)
2. Copy the structure from `en_US.json` and translate all values
3. The system will automatically detect and load the new language
4. Add the language name mapping in `i18n_utils.py`

## 🛠️ Development

### Project Structure

```
ai-image-tree/
├── app.py                 # Main application
├── ai_client.py          # AI client system
├── auto_image_generator.py # Image generator
├── database.py           # Database operations
├── i18n_utils.py         # Internationalization utilities
├── start.py              # Startup script
├── setup.py              # Installation script
├── install_comfyui.py    # ComfyUI auto-installation script
├── test_comfyui_connection.py # ComfyUI connection test script
├── test_image_generation.py # Image generation test script
├── comfyui_workflow.json # ComfyUI workflow definition
├── config.json.example   # Configuration file template
├── requirements.txt      # Python dependencies
├── i18n/                 # Translation files
│   ├── zh_CN.json       # Chinese translations
│   └── en_US.json       # English translations
├── static/js/            # Frontend JavaScript
│   └── i18n.js          # Frontend i18n support
├── templates/            # Web templates
│   └── simple_index.html
├── generated_images/     # Generated images (auto-created)
├── web_generated_images/ # Web generated images (auto-created)
├── COMFYUI_SETUP.md     # ComfyUI installation guide
├── COMFYUI_INTEGRATION.md # ComfyUI integration technical docs
├── INSTALL.md           # Detailed installation guide
├── LICENSE              # Open source license
├── CONTRIBUTING.md      # Contribution guide
├── README.md            # Project documentation (Chinese)
└── README_EN.md         # Project documentation (English)
```

## 📁 Project Files

| File/Directory | Description |
|----------------|-------------|
| `app.py` | Main application |
| `ai_client.py` | AI client system |
| `auto_image_generator.py` | Image generator |
| `database.py` | Database operations |
| `i18n_utils.py` | Internationalization utilities |
| `setup.py` | Auto-installation script |
| `start.py` | Startup script |
| `start.bat` | Windows startup script |
| `start.sh` | Linux/Mac startup script |
| `install_comfyui.py` | ComfyUI auto-installation script |
| `test_comfyui_connection.py` | ComfyUI connection test script |
| `test_image_generation.py` | Image generation test script |
| `comfyui_workflow.json` | ComfyUI workflow definition file |
| `config.json.example` | Configuration file template |
| `requirements.txt` | Python dependencies list |
| `i18n/` | Translation files directory |
| `static/js/` | Frontend JavaScript files |
| `templates/` | Web templates directory |
| `COMFYUI_SETUP.md` | ComfyUI detailed installation guide |
| `COMFYUI_INTEGRATION.md` | ComfyUI integration technical documentation |
| `INSTALL.md` | Detailed installation guide |
| `CONTRIBUTING.md` | Contribution guide |
| `CHANGELOG.md` | Update log |
| `LICENSE` | Open source license |

### Core Components

- **AI Client System** (`ai_client.py`): Unified multi-provider AI interface
- **Image Generator** (`auto_image_generator.py`): Image generation and quality control
- **Database Layer** (`database.py`): Data persistence and management
- **Internationalization** (`i18n_utils.py`): Multi-language support system
- **Web Interface** (`app.py` + `templates/`): Flask web application

### Extension Development

The system uses modular design for easy extension:

- **Add New AI Providers**: Inherit from `BaseAIClient` class
- **Custom Quality Assessment**: Modify `ImageQuality` evaluation logic
- **Interface Customization**: Modify HTML templates and CSS styles
- **Add New Languages**: Create translation files in `i18n/` directory

## 🚀 Deployment

### Development Environment
```bash
python app.py  # Runs on localhost:8080 by default
```

### Production Environment
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app

# Using uWSGI
pip install uwsgi
uwsgi --http :8080 --wsgi-file app.py --callable app
```

### Docker Deployment (Coming Soon)
```bash
docker build -t ai-image-tree .
docker run -p 8080:8080 ai-image-tree
```

## 🔒 Security Considerations

- 🔑 Keep API keys secure, don't commit to version control
- 🌐 Use HTTPS in production environments
- 🛡️ Configure appropriate firewall rules
- 📝 Regularly backup database and configuration files

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - Powerful image generation backend
- [Ollama](https://ollama.ai/) - Local AI model runtime environment
- [OpenRouter](https://openrouter.ai/) - Cloud AI model API service
- [Flask](https://flask.palletsprojects.com/) - Web framework

## 📞 Support

If you encounter issues or have suggestions:

- Submit an [Issue](https://github.com/your-username/ai-image-tree/issues)
- Join [Discussions](https://github.com/your-username/ai-image-tree/discussions)

---

⭐ If this project helps you, please give it a star!