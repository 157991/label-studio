"""
品牌清理模块 - 安全地隐藏官方推广内容。

不修改 JSX 结构（避免语法错误），而是通过注入 CSS 来隐藏不需要的元素。
同时通过替换关键文本实现去品牌化。

隐藏的内容：
- Heidi 负鼠吉祥物和提示
- AWS Marketplace 推广卡片
- HumanSignal 底部品牌信息
- 外部社区链接 (Slack, GitHub Profile 等)
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import BrandConfig


# 需要隐藏的元素的 CSS 选择器
HIDE_SELECTORS = [
    # Heidi 相关
    '.heidi-tips',
    '.heidi-tip',
    '[class*="heidi"]',
    '[class*="Heidi"]',
    '#heidi',
    
    # AWS 推广卡片
    '.aws-promotion',
    '.aws-banner',
    '[class*="aws-spend"]',
    '[class*="marketplace"]',
    
    # 底部 HumanSignal 品牌
    '[class*="humansignal"]',
    '[class*="human-signal"]',
    '.footer-branding',
    
    # 推广/营销类
    '.promo-banner',
    '.promotion-card',
    '[class*="promo"]',
    '[class*="upgrade"]',
    '[class*="enterprise"]',
]

# 额外的 CSS 注入
EXTRA_CSS = """
/* 白标：隐藏官方推广和品牌元素 */
.heidi-tips,
.heidi-tip,
[class*="heidi" i],
[class*="Heidi" i],
.heidi-speaking,
.aws-promotion,
.aws-banner,
[class*="aws-spend" i],
[class*="marketplace" i],
[class*="humansignal" i],
[class*="human-signal" i],
[class*="upgrade-to-enterprise" i],
[class*="promo-banner" i] {
  display: none !important;
}

/* 白标：登录页左侧 Logo 隐藏 */
.login_page_new_ui .left .ls-logo {
  display: none !important;
}

/* 白标：登录页底部 "Brought to you by" + Human Signal Logo 隐藏 */
.login_page_new_ui .left .by {
  display: none !important;
}

/* 白标：登录页左侧背景：科技感深蓝→紫色渐变 */
.login_page_new_ui .left {
  background: linear-gradient(135deg, #EFF6FF 0%, #E0E7FF 40%, #F5F3FF 100%) !important;
}

/* 白标：登录页左侧装饰图隐藏 */
.login_page_new_ui .left:after {
  display: none !important;
}
"""


def inject_brand_css(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    注入品牌清理 CSS 到前端。

    通过在 index.html 中注入 CSS 来隐藏不需要的元素，
    比直接修改 JSX 更安全，不会破坏代码结构。
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.remove_branding:
        return modified

    # 注入到 dist index.html
    dist_index = ls_root / "web" / "dist" / "apps" / "labelstudio" / "index.html"
    if dist_index.exists():
        content = dist_index.read_text(encoding="utf-8")
        if "whitelabel-brand-cleanup" not in content:
            style_tag = f'\n<style id="whitelabel-brand-cleanup">\n{EXTRA_CSS}\n</style>\n'
            new_content = content.replace("</head>", style_tag + "</head>")
            if not dry_run:
                dist_index.write_text(new_content, encoding="utf-8")
            modified.append(str(dist_index.relative_to(ls_root)))

    # 注入到 Django 模板
    templates = [
        ls_root / "label_studio" / "templates" / "base.html",
        ls_root / "label_studio" / "templates" / "simple.html",
        ls_root / "label_studio" / "users" / "templates" / "users" / "new-ui" / "user_base.html",
    ]
    for tmpl in templates:
        if tmpl.exists():
            content = tmpl.read_text(encoding="utf-8")
            if "whitelabel-brand-cleanup" not in content:
                style_tag = f'\n<style id="whitelabel-brand-cleanup">\n{EXTRA_CSS}\n</style>\n'
                new_content = content.replace("</head>", style_tag + "</head>")
                if not dry_run:
                    tmpl.write_text(new_content, encoding="utf-8")
                modified.append(str(tmpl.relative_to(ls_root)))

    return modified


def clean_text_branding(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    清理文本中的品牌引用（安全的字符串替换）。

    只替换明确的品牌名和链接，不碰代码结构。
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.remove_branding:
        return modified

    # 只在明确的文案文件中替换
    target_files = [
        # 前端文案
        ls_root / "web" / "apps" / "labelstudio" / "src" / "components" / "HeidiTips" / "content.ts",
        # 侧边栏菜单文字在源码里，通过 source_i18n 模块处理
    ]

    for filepath in target_files:
        if not filepath.exists():
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            continue

        original = content
        # 移除 Heidi 相关的文案
        content = re.sub(r'Get the latest news from Heidi[^\n]*', '', content)
        content = re.sub(r'Brought to you by[^\n]*', '', content)

        if content != original and not dry_run:
            filepath.write_text(content, encoding="utf-8")
            modified.append(str(filepath.relative_to(ls_root)))

    return modified


def apply_brand_cleanup(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    应用品牌清理：通过 CSS 隐藏 + 文案清理。
    安全第一，不修改 JSX 结构。
    """
    modified: list[str] = []

    # 1. 注入 CSS 隐藏不需要的元素
    files = inject_brand_css(ls_root, config, dry_run)
    modified.extend(files)

    # 2. 清理文案中的品牌引用
    files = clean_text_branding(ls_root, config, dry_run)
    modified.extend(files)

    return modified


__all__ = ["apply_brand_cleanup"]
