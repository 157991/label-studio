"""
前端源码补丁 - Logo 组件、品牌名、Menubar 等关键点。
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import BrandConfig


def _replace_in_file(
    filepath: Path,
    replacements: list[tuple[str | re.Pattern, str]],
    dry_run: bool = False,
) -> bool:
    """文件内替换。"""
    if not filepath.exists():
        return False
    content = filepath.read_text(encoding="utf-8")
    original = content
    for pattern, replacement in replacements:
        if isinstance(pattern, re.Pattern):
            content = pattern.sub(replacement, content)
        else:
            content = content.replace(pattern, replacement)
    if content != original and not dry_run:
        filepath.write_text(content, encoding="utf-8")
    return content != original


def apply_frontend_patches(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    修改前端关键组件中的品牌信息。

    只改关键几个点，不全量替换，保持最小侵入。
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    # ========== Menubar 组件 - 品牌名显示 ==========
    menubar = ls_root / "web" / "apps" / "labelstudio" / "src" / "components" / "Menubar" / "Menubar.jsx"
    if menubar.exists():
        changed = _replace_in_file(menubar, [
            # 替换 aria-label 中的 "Label Studio Logo"
            ("Label Studio Logo", f"{config.brand_name} Logo"),
        ], dry_run)
        if changed:
            modified.append(str(menubar.relative_to(ls_root)))

    # ========== 首页 - 版本号显示 ==========
    home_page = ls_root / "web" / "apps" / "labelstudio" / "src" / "pages" / "Home" / "HomePage.tsx"
    if home_page.exists():
        changed = _replace_in_file(home_page, [
            ("Label Studio Version: Community", f"{config.brand_name} 版本"),
            (re.compile(r'Label\s+Studio\s+Version\s*:\s*Community', re.IGNORECASE), f"{config.brand_name} 版本"),
        ], dry_run)
        if changed:
            modified.append(str(home_page.relative_to(ls_root)))

    # ========== Editor 提示消息 ==========
    messages = ls_root / "web" / "libs" / "editor" / "src" / "utils" / "messages.jsx"
    if messages.exists():
        changed = _replace_in_file(messages, [
            ("Label Studio", config.brand_name),
        ], dry_run)
        if changed:
            modified.append(str(messages.relative_to(ls_root)))

    # ========== Heidi Tips 内容 ==========
    heidi_tips = ls_root / "web" / "apps" / "labelstudio" / "src" / "components" / "HeidiTips" / "content.ts"
    if heidi_tips.exists():
        changed = _replace_in_file(heidi_tips, [
            ("Label Studio", config.brand_name),
            ("labelstud.io", config.brand_domain),
        ], dry_run)
        if changed:
            modified.append(str(heidi_tips.relative_to(ls_root)))

    # ========== 移除 Menubar 中的外链 (Docs, GitHub, Slack) ==========
    if config.remove_branding_links and menubar.exists():
        content = menubar.read_text(encoding="utf-8")
        original = content
        # 移除指向 labelstud.io / github.com/HumanSignal / slack.com 的链接
        for domain in ["labelstud.io", "github.com/HumanSignal", "slack.com", "humansignal.com"]:
            content = re.sub(
                rf'<(?:Link|a)\s[^>]*href=["\'][^"\']*{re.escape(domain)}[^"\']*["\'][^>]*>.*?</(?:Link|a)>',
                '',
                content,
                flags=re.DOTALL,
            )
        # 移除空的 <li> 包装
        content = re.sub(r'<li[^>]*>\s*</li>', '', content)
        if content != original and not dry_run:
            menubar.write_text(content, encoding="utf-8")
            rel = str(menubar.relative_to(ls_root))
            if rel not in modified:
                modified.append(rel)

    return modified


__all__ = ["apply_frontend_patches"]
