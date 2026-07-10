"""
后端 Python 源码中文化模块。

处理后端传往前台的用户可见文本：
- Data Manager 列名 (ID, Completed, Cancelled 等)
- 筛选选项
- Actions 菜单
- 错误消息
- API 响应中的用户可见文本
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ..config import BrandConfig


SKIP_DIRS = [
    'node_modules',
    'dist',
    '__pycache__',
    'migrations',
    'tests',
    '.git',
]


def _should_skip(filepath: str) -> bool:
    for d in SKIP_DIRS:
        if f'/{d}/' in filepath or filepath.endswith(f'/{d}'):
            return True
    if '__pycache__' in filepath:
        return True
    return False


def _replace_in_python_strings(content: str, translations: dict[str, str]) -> str:
    """
    替换 Python 源码中的字符串字面量。
    只替换在翻译字典中精确匹配的字符串。
    """
    # 匹配 Python 字符串字面量（单引号、双引号、三引号）
    # 只处理单行字符串
    patterns = [
        # 双引号
        (r'"((?:[^"\\]|\\.)*)"', '"', '"'),
        # 单引号
        (r"'((?:[^'\\]|\\.)*)'", "'", "'"),
    ]

    result = content
    replacements: list[tuple[int, int, str]] = []

    for pattern, left_q, right_q in patterns:
        for match in re.finditer(pattern, result):
            inner = match.group(1)
            if not inner.strip():
                continue
            # 跳过明显是代码/变量/路径的
            if any(c in inner for c in ['=', '{', '}', '=>', ':', '(', ')', '/', '_', '.']):
                # 但允许带空格的短语（如 "Task ID"）
                if not re.search(r'[A-Za-z ]{3,}', inner):
                    continue
            # 跳过纯小写标识符（变量名的可能）
            if inner.islower() and ' ' not in inner and len(inner) < 20:
                continue
            
            translated = translations.get(inner)
            if not translated:
                stripped = inner.strip()
                if stripped in translations:
                    translated = translations[stripped]
                    leading = inner[:len(inner) - len(inner.lstrip())]
                    trailing = inner[len(inner.rstrip()):]
                    translated = leading + translated + trailing
            
            if translated:
                start = match.start()
                end = match.end()
                new_str = left_q + translated + right_q
                replacements.append((start, end, new_str))

    # 从后往前替换
    replacements.sort(key=lambda x: x[0], reverse=True)
    for start, end, new_str in replacements:
        result = result[:start] + new_str + result[end:]

    return result


def apply_backend_localization(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    对后端 Python 源码进行中文化。

    重点处理用户可见的文本：
    - data_manager 列名和筛选
    - API 错误消息
    - 表单验证消息
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.translations_file or not config.source_i18n:
        return modified

    # 加载翻译字典
    with open(config.translations_file, encoding='utf-8') as f:
        data = json.load(f)

    translations: dict[str, str] = {}
    if "modules" in data:
        for module in data["modules"].values():
            if isinstance(module, dict):
                translations.update(module)
    else:
        translations = data

    if not translations:
        return modified

    # 重点处理的目录
    target_dirs = [
        ls_root / "label_studio" / "data_manager",
        ls_root / "label_studio" / "users",
        ls_root / "label_studio" / "organizations",
        ls_root / "label_studio" / "projects",
        ls_root / "label_studio" / "core",
    ]

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue

        for root, dirs, files in os.walk(str(target_dir)):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                if not filename.endswith('.py'):
                    continue

                filepath = Path(root) / filename
                rel = str(filepath.relative_to(ls_root))
                if _should_skip(rel):
                    continue

                try:
                    content = filepath.read_text(encoding='utf-8')
                except (UnicodeDecodeError, IOError):
                    continue

                original = content
                content = _replace_in_python_strings(content, translations)

                if content != original:
                    if not dry_run:
                        filepath.write_text(content, encoding='utf-8')
                    modified.append(rel)

    return modified


__all__ = ["apply_backend_localization"]
