"""
后端品牌信息补丁 - Django settings, 邮件模板等。
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


def apply_backend_patches(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    修改后端品牌相关信息。

    覆盖：
    - Django settings 中的站点名
    - 邮件模板品牌信息
    - API 响应中的品牌名
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    # ========== Django settings ==========
    settings_files = [
        ls_root / "label_studio" / "core" / "settings" / "label_studio.py",
        ls_root / "label_studio" / "core" / "settings" / "common.py",
    ]
    for sf in settings_files:
        if sf.exists():
            changed = _replace_in_file(sf, [
                ("Label Studio", config.brand_name),
            ], dry_run)
            if changed:
                modified.append(str(sf.relative_to(ls_root)))

    # ========== 邮件模板 ==========
    # 找所有 email 相关的模板
    email_dirs = [
        ls_root / "label_studio" / "users" / "templates",
        ls_root / "label_studio" / "organizations" / "templates",
        ls_root / "label_studio" / "core" / "templates",
    ]
    for ed in email_dirs:
        if not ed.exists():
            continue
        for filepath in ed.rglob("*.html"):
            rel = str(filepath.relative_to(ls_root))
            # 只处理邮件相关模板
            if any(k in rel.lower() for k in ['email', 'mail', 'invite', 'reset', 'confirm']):
                content = filepath.read_text(encoding="utf-8")
                if "Label Studio" in content or "labelstud.io" in content:
                    changed = _replace_in_file(filepath, [
                        ("Label Studio", config.brand_name),
                        ("labelstud.io", config.brand_domain),
                    ], dry_run)
                    if changed:
                        modified.append(rel)

    # ========== 账号相关 views (注册/登录页面标题) ==========
    views_files = [
        ls_root / "label_studio" / "users" / "views.py",
        ls_root / "label_studio" / "users" / "views" / "signup.py",
    ]
    for vf in views_files:
        if vf.exists():
            content = vf.read_text(encoding="utf-8")
            if "Label Studio" in content:
                changed = _replace_in_file(vf, [
                    ("Label Studio", config.brand_name),
                ], dry_run)
                if changed:
                    modified.append(str(vf.relative_to(ls_root)))

    return modified


__all__ = ["apply_backend_patches"]
