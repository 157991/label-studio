"""
国际化注入模块 - 运行时中英双语切换（增强版）。

方案：
1. 将翻译字典注入到前端 index.html 和 Django 模板中
2. 注入一个增强版 i18n JS 脚本，实现：
   - 页面加载时翻译所有文本节点
   - MutationObserver 监听 DOM 变化，动态渲染的内容也自动翻译
   - 右上角添加 中/EN 切换按钮
   - 切换时即时替换，不刷新页面
   - 语言偏好存在 localStorage

不侵入 React 源码，通过 DOM 操作实现翻译。安全可靠。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import BrandConfig


I18N_SCRIPT = r"""
(function() {
  // ========== 翻译字典 ==========
  var __translations = __TRANSLATIONS__;
  var __brandName = '__BRAND_NAME__';
  var __defaultLang = '__DEFAULT_LANG__';

  // ========== 状态管理 ==========
  var currentLang = localStorage.getItem('ls-whitelabel-lang') || __defaultLang;

  function getTranslation(text) {
    if (currentLang === 'en') return text;
    var trimmed = text.trim();
    if (!trimmed) return text;

    // 精确匹配
    if (__translations[trimmed]) {
      // 保留前后空白
      var leading = text.match(/^\s*/)[0];
      var trailing = text.match(/\s*$/)[0];
      return leading + __translations[trimmed] + trailing;
    }

    // 尝试小写匹配
    var lower = trimmed.toLowerCase();
    for (var key in __translations) {
      if (key.toLowerCase() === lower) {
        var leading = text.match(/^\s*/)[0];
        var trailing = text.match(/\s*$/)[0];
        return leading + __translations[key] + trailing;
      }
    }

    return text;
  }

  // ========== 文本节点翻译 ==========
  var translatedNodes = new WeakSet();

  function translateTextNode(node) {
    if (!node || node.nodeType !== 3) return; // 只处理文本节点
    if (!node.nodeValue || !node.nodeValue.trim()) return;
    if (translatedNodes.has(node)) return;

    var originalText = node.nodeValue;
    var translated = getTranslation(originalText);

    if (translated !== originalText) {
      node.nodeValue = translated;
      // 存储原始文本用于切换回英文
      node.__originalText = originalText;
    }
    translatedNodes.add(node);
  }

  function translateElement(element) {
    if (!element || element.nodeType !== 1) return;

    // 跳过 script, style, noscript 等
    var tag = element.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'CODE' || tag === 'PRE') return;

    // 跳过我们自己的元素
    if (element.id && element.id.indexOf('ls-whitelabel') === 0) return;
    if (element.classList && element.classList.contains('ls-whitelabel-skip')) return;

    // 翻译所有文本子节点
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
      acceptNode: function(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        // 检查父元素是不是 script/style 等
        var parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        var ptag = parent.tagName;
        if (ptag === 'SCRIPT' || ptag === 'STYLE' || ptag === 'NOSCRIPT' || ptag === 'CODE' || ptag === 'PRE') return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    var node;
    while ((node = walker.nextNode())) {
      translateTextNode(node);
    }

    // 翻译 input placeholder
    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
      var placeholder = element.getAttribute('placeholder');
      if (placeholder && placeholder.trim()) {
        var translated = getTranslation(placeholder);
        if (translated !== placeholder) {
          if (!element.__originalPlaceholder) {
            element.__originalPlaceholder = placeholder;
          }
          element.setAttribute('placeholder', translated);
        }
      }
    }

    // 翻译 title 属性 (tooltip)
    var title = element.getAttribute('title');
    if (title && title.trim() && title.indexOf('http') !== 0) {
      var titleTranslated = getTranslation(title);
      if (titleTranslated !== title) {
        if (!element.__originalTitle) {
          element.__originalTitle = title;
        }
        element.setAttribute('title', titleTranslated);
      }
    }

    // 翻译 aria-label
    var ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) {
      var ariaTranslated = getTranslation(ariaLabel);
      if (ariaTranslated !== ariaLabel) {
        if (!element.__originalAriaLabel) {
          element.__originalAriaLabel = ariaLabel;
        }
        element.setAttribute('aria-label', ariaTranslated);
      }
    }
  }

  function translatePage() {
    translateElement(document.body);

    // 翻译 document.title
    if (document.title) {
      var newTitle = getTranslation(document.title);
      // 也替换品牌名
      newTitle = newTitle.replace(/Label\s*Studio/gi, __brandName);
      if (newTitle !== document.title) {
        document.__originalTitle = document.title;
        document.title = newTitle;
      }
    }
  }

  // ========== 恢复英文 ==========
  function restoreTextNode(node) {
    if (node.__originalText) {
      node.nodeValue = node.__originalText;
      translatedNodes.delete(node);
    }
  }

  function restoreElement(element) {
    if (!element || element.nodeType !== 1) return;

    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      restoreTextNode(node);
    }

    if (element.__originalPlaceholder) {
      element.setAttribute('placeholder', element.__originalPlaceholder);
    }
    if (element.__originalTitle) {
      element.setAttribute('title', element.__originalTitle);
    }
    if (element.__originalAriaLabel) {
      element.setAttribute('aria-label', element.__originalAriaLabel);
    }
  }

  function restorePage() {
    restoreElement(document.body);
    if (document.__originalTitle) {
      document.title = document.__originalTitle;
    }
  }

  // ========== DOM 变化监听 ==========
  var observer = new MutationObserver(function(mutations) {
    if (currentLang !== 'zh-CN') return;

    mutations.forEach(function(mutation) {
      // 新增节点
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) {
            // 延迟一下，等内容渲染完成
            setTimeout(function() {
              translateElement(node);
            }, 50);
          } else if (node.nodeType === 3) {
            translateTextNode(node);
          }
        });
      }
      // 文本变化
      else if (mutation.type === 'characterData') {
        translateTextNode(mutation.target);
      }
    });
  });

  // ========== 切换语言 ==========
  function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('ls-whitelabel-lang', lang);

    if (lang === 'zh-CN') {
      translatePage();
    } else {
      restorePage();
    }

    // 更新按钮状态
    var btnZh = document.getElementById('ls-whitelabel-btn-zh');
    var btnEn = document.getElementById('ls-whitelabel-btn-en');
    if (btnZh && btnEn) {
      btnZh.style.fontWeight = lang === 'zh-CN' ? 'bold' : 'normal';
      btnZh.style.opacity = lang === 'zh-CN' ? '1' : '0.6';
      btnEn.style.fontWeight = lang === 'en' ? 'bold' : 'normal';
      btnEn.style.opacity = lang === 'en' ? '1' : '0.6';
    }
  }

  // ========== 添加切换按钮 ==========
  function addToggleButton() {
    if (document.getElementById('ls-whitelabel-lang-toggle')) return;

    var container = document.createElement('div');
    container.id = 'ls-whitelabel-lang-toggle';
    container.style.cssText = 'position:fixed;top:12px;right:80px;z-index:99999;background:rgba(255,255,255,0.95);border:1px solid #e5e7eb;border-radius:6px;padding:2px 6px;font-size:13px;display:flex;align-items:center;gap:4px;box-shadow:0 2px 8px rgba(0,0,0,0.1);backdrop-filter:blur(4px);';

    var btnZh = document.createElement('button');
    btnZh.id = 'ls-whitelabel-btn-zh';
    btnZh.textContent = '中';
    btnZh.style.cssText = 'background:none;border:none;cursor:pointer;padding:2px 6px;border-radius:4px;font-size:12px;color:#374151;';
    btnZh.onmouseover = function() { this.style.background = '#f3f4f6'; };
    btnZh.onmouseout = function() { this.style.background = 'none'; };
    btnZh.onclick = function() { setLanguage('zh-CN'); };

    var separator = document.createElement('span');
    separator.textContent = '|';
    separator.style.cssText = 'color:#d1d5db;';

    var btnEn = document.createElement('button');
    btnEn.id = 'ls-whitelabel-btn-en';
    btnEn.textContent = 'EN';
    btnEn.style.cssText = 'background:none;border:none;cursor:pointer;padding:2px 6px;border-radius:4px;font-size:12px;color:#374151;';
    btnEn.onmouseover = function() { this.style.background = '#f3f4f6'; };
    btnEn.onmouseout = function() { this.style.background = 'none'; };
    btnEn.onclick = function() { setLanguage('en'); };

    container.appendChild(btnZh);
    container.appendChild(separator);
    container.appendChild(btnEn);
    document.body.appendChild(container);

    // 设置初始状态
    btnZh.style.fontWeight = currentLang === 'zh-CN' ? 'bold' : 'normal';
    btnZh.style.opacity = currentLang === 'zh-CN' ? '1' : '0.6';
    btnEn.style.fontWeight = currentLang === 'en' ? 'bold' : 'normal';
    btnEn.style.opacity = currentLang === 'en' ? '1' : '0.6';
  }

  // ========== 初始化 ==========
  function init() {
    if (currentLang === 'zh-CN') {
      translatePage();
    }
    addToggleButton();

    // 启动 DOM 监听
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      characterDataOldValue: false
    });

    // 页面完全加载后再翻译一次（确保所有动态内容都翻译到）
    window.addEventListener('load', function() {
      setTimeout(function() {
        if (currentLang === 'zh-CN') {
          translatePage();
        }
      }, 500);
    });
  }

  // DOM ready 时初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // 暴露给全局
  window.__setLanguage = setLanguage;
})();
"""


def _build_translations_json(config: BrandConfig) -> str:
    """构建翻译字典 JSON 字符串。"""
    if not config.translations_file:
        return "{}"

    with open(config.translations_file, encoding="utf-8") as f:
        data = json.load(f)

    # 展开所有 modules
    translations: dict[str, str] = {}
    if isinstance(data, dict):
        if "modules" in data and isinstance(data["modules"], dict):
            for module in data["modules"].values():
                if isinstance(module, dict):
                    translations.update(module)
        else:
            translations = data

    # 补充一些常见的翻译（翻译字典里可能没有的）
    extra = {
        "Label Studio": config.brand_name,
        "Label Studio Enterprise": config.brand_name + " 企业版",
        "LabelStudio": config.brand_slug.replace("-", "").title(),
    }
    for k, v in extra.items():
        if k not in translations:
            translations[k] = v

    return json.dumps(translations, ensure_ascii=False)


def inject_i18n(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    注入运行时国际化脚本到前端页面和 Django 模板。

    增强版特性：
    - MutationObserver 监听 DOM 变化，动态内容自动翻译
    - 翻译文本节点、placeholder、title、aria-label
    - 右上角中英文切换按钮
    - 支持切换回英文（恢复原文）
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.i18n_enabled:
        return modified

    translations_json = _build_translations_json(config)
    script_content = (
        I18N_SCRIPT
        .replace("__TRANSLATIONS__", translations_json)
        .replace("__BRAND_NAME__", config.brand_name)
        .replace("__DEFAULT_LANG__", config.default_language)
    )

    # 构造注入的 script 标签
    inject_html = f'\n<script id="ls-whitelabel-i18n">\n{script_content}\n</script>\n'

    # ========== 前端构建产物 index.html ==========
    dist_index = ls_root / "web" / "dist" / "apps" / "labelstudio" / "index.html"
    if dist_index.exists():
        content = dist_index.read_text(encoding="utf-8")
        if 'ls-whitelabel-i18n' not in content:
            # 在 </body> 前注入
            new_content = content.replace("</body>", inject_html + "</body>")
            if not dry_run:
                dist_index.write_text(new_content, encoding="utf-8")
            modified.append(str(dist_index.relative_to(ls_root)))

    # ========== Django 模板 ==========
    backend_templates = [
        ls_root / "label_studio" / "templates" / "base.html",
        ls_root / "label_studio" / "templates" / "simple.html",
        ls_root / "label_studio" / "users" / "templates" / "users" / "new-ui" / "user_base.html",
        ls_root / "label_studio" / "users" / "templates" / "users" / "user_base.html",
    ]

    for tmpl in backend_templates:
        if tmpl.exists():
            content = tmpl.read_text(encoding="utf-8")
            if 'ls-whitelabel-i18n' not in content:
                new_content = content.replace("</body>", inject_html + "</body>")
                if new_content == content:
                    # 没有 </body>，试试在 </html> 前
                    new_content = content.replace("</html>", inject_html + "</html>")
                if not dry_run:
                    tmpl.write_text(new_content, encoding="utf-8")
                modified.append(str(tmpl.relative_to(ls_root)))

    return modified


__all__ = ["inject_i18n"]
