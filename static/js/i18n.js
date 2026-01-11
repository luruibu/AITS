/**
 * 前端国际化支持
 */

class I18nManager {
    constructor() {
        this.currentLocale = 'zh_CN';
        this.translations = {};
        this.supportedLocales = {};
        this.fallbackLocale = 'zh_CN';
        
        // 初始化
        this.init();
    }
    
    async init() {
        try {
            // 获取当前语言设置
            const response = await fetch('/api/get_locale');
            const data = await response.json();
            
            if (data.success) {
                this.currentLocale = data.locale;
                this.supportedLocales = data.supported_locales;
                
                // 加载翻译文件
                await this.loadTranslations(this.currentLocale);
                
                // 更新页面
                this.updatePage();
                
                // 创建语言切换器
                this.createLanguageSwitcher();
            }
        } catch (error) {
            console.error('初始化国际化失败:', error);
        }
    }
    
    async loadTranslations(locale) {
        try {
            const response = await fetch(`/api/translations/${locale}`);
            const data = await response.json();
            
            if (data.success) {
                this.translations[locale] = data.translations;
                return true;
            }
        } catch (error) {
            console.error(`加载翻译文件失败 (${locale}):`, error);
        }
        return false;
    }
    
    async setLocale(locale) {
        try {
            // 设置服务器端语言
            const response = await fetch(`/api/set_locale/${locale}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentLocale = locale;
                
                // 如果翻译文件未加载，先加载
                if (!this.translations[locale]) {
                    await this.loadTranslations(locale);
                }
                
                // 更新页面
                this.updatePage();
                
                // 保存到本地存储
                localStorage.setItem('preferred_locale', locale);
                
                return true;
            }
        } catch (error) {
            console.error('设置语言失败:', error);
        }
        return false;
    }
    
    t(key, params = {}) {
        const locale = this.currentLocale;
        let translation = this.getNestedValue(this.translations[locale], key);
        
        // 如果当前语言没有翻译，尝试使用fallback语言
        if (!translation && locale !== this.fallbackLocale) {
            translation = this.getNestedValue(this.translations[this.fallbackLocale], key);
        }
        
        // 如果仍然没有翻译，返回key本身
        if (!translation) {
            return key;
        }
        
        // 处理参数替换
        return this.formatString(translation, params);
    }
    
    getNestedValue(obj, key) {
        return key.split('.').reduce((o, k) => (o && o[k]) ? o[k] : null, obj);
    }
    
    formatString(str, params) {
        return str.replace(/\{(\w+)\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }
    
    updatePage() {
        // 更新所有带有 data-i18n 属性的元素
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' && (element.type === 'text' || element.type === 'search')) {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // 更新所有带有 data-i18n-placeholder 属性的元素
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // 更新所有带有 data-i18n-title 属性的元素
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
        
        // 更新页面标题
        const titleElement = document.querySelector('title');
        if (titleElement && titleElement.hasAttribute('data-i18n')) {
            titleElement.textContent = this.t(titleElement.getAttribute('data-i18n'));
        }
    }
    
    createLanguageSwitcher() {
        // 查找语言切换器容器
        const container = document.getElementById('language-switcher');
        if (!container) return;
        
        // 创建下拉选择器
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm';
        select.style.width = 'auto';
        
        // 添加选项
        Object.entries(this.supportedLocales).forEach(([locale, name]) => {
            const option = document.createElement('option');
            option.value = locale;
            option.textContent = name;
            option.selected = locale === this.currentLocale;
            select.appendChild(option);
        });
        
        // 添加事件监听器
        select.addEventListener('change', async (e) => {
            const newLocale = e.target.value;
            const success = await this.setLocale(newLocale);
            
            if (success) {
                // 显示成功消息
                this.showMessage(this.t('messages.settings_saved'), 'success');
            } else {
                // 显示错误消息
                this.showMessage(this.t('messages.error'), 'error');
                // 恢复原来的选择
                e.target.value = this.currentLocale;
            }
        });
        
        // 清空容器并添加选择器
        container.innerHTML = '';
        container.appendChild(select);
    }
    
    showMessage(message, type = 'info') {
        // 创建消息提示
        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 3000);
    }
}

// 全局实例
let i18nManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    i18nManager = new I18nManager();
});

// 全局翻译函数
function t(key, params = {}) {
    return i18nManager ? i18nManager.t(key, params) : key;
}

// 全局语言设置函数
async function setLocale(locale) {
    return i18nManager ? await i18nManager.setLocale(locale) : false;
}