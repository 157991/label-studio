"""
Django 模板修改补丁 - 登录页、错误页、base 模板等。
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
    """在文件中执行多个替换。返回是否修改。"""
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


def apply_template_patches(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    修改 Django 模板中的品牌信息。

    覆盖：
    - 页面 <title>
    - 登录页品牌名
    - 错误页品牌信息
    - footer branding 链接
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    # ========== 新 UI 用户模板 (登录页) ==========
    user_base = ls_root / "label_studio" / "users" / "templates" / "users" / "new-ui" / "user_base.html"
    if user_base.exists():
        changed = _replace_in_file(user_base, [
            # 页面 title
            ("Label Studio", config.brand_name),
            # HumanSignal 底部品牌名
            ("HumanSignal", config.brand_name),
        ], dry_run)
        if changed:
            modified.append(str(user_base.relative_to(ls_root)))

    # ========== 旧 UI 用户模板 ==========
    old_user_base = ls_root / "label_studio" / "users" / "templates" / "users" / "user_base.html"
    if old_user_base.exists():
        changed = _replace_in_file(old_user_base, [
            ("Label Studio", config.brand_name),
        ], dry_run)
        if changed:
            modified.append(str(old_user_base.relative_to(ls_root)))

    # ========== 错误页 (403/404/500) ==========
    error_pages = [
        ls_root / "label_studio" / "templates" / "403.html",
        ls_root / "label_studio" / "templates" / "404.html",
        ls_root / "label_studio" / "templates" / "500.html",
    ]
    for page in error_pages:
        if page.exists():
            changed = _replace_in_file(page, [
                ("Label Studio", config.brand_name),
                ("labelstud.io", config.brand_domain),
            ], dry_run)
            if changed:
                modified.append(str(page.relative_to(ls_root)))

    # ========== base 模板 (页面 title) ==========
    base_templates = [
        ls_root / "label_studio" / "templates" / "base.html",
        ls_root / "label_studio" / "templates" / "simple.html",
    ]
    for tmpl in base_templates:
        if tmpl.exists():
            changed = _replace_in_file(tmpl, [
                ("Label Studio", config.brand_name),
            ], dry_run)
            if changed:
                modified.append(str(tmpl.relative_to(ls_root)))

    # ========== 移除 footer branding 链接 ==========
    if config.remove_branding_links:
        footer_files = [user_base, old_user_base]
        for ff in footer_files:
            if ff.exists():
                # 移除 HumanSignal / Label Studio 官方链接
                content = ff.read_text(encoding="utf-8")
                new_content = re.sub(
                    r'<a[^>]*href="https?://(?:www\.)?(?:labelstud\.io|humansignal\.com|heartex\.com)[^"]*"[^>]*>.*?</a>',
                    '',
                    content,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                if new_content != content and not dry_run:
                    ff.write_text(new_content, encoding="utf-8")
                    rel = str(ff.relative_to(ls_root))
                    if rel not in modified:
                        modified.append(rel)

    return modified


__all__ = ["apply_template_patches"]
