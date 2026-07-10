"""
源码级中文化模块 - 构建前批量替换前端源码中的英文字符串。

原理：
- 基于翻译字典（zh-CN.json）
- 只替换 JS/TS 源码中的字符串字面量（单引号、双引号、模板字符串）
- 不碰变量名、函数名、属性名等代码逻辑
- 安全可控，可预测

支持的字符串类型：
- 双引号: "Hello World"  →  "你好世界"
- 单引号: 'Hello World'  →  '你好世界'
- 模板字符串: `Hello World`  →  `你好世界`
- JSX 属性: title="Hello"  →  title="你好"
- JSX 文本: <div>Hello</div>  →  <div>你好</div>
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ..config import BrandConfig


# 需要跳过的文件模式
SKIP_PATTERNS = [
    'node_modules',
    'dist',
    '__tests__',
    '.test.',
    '.spec.',
    'test_',
    '.d.ts',
    '.map',
    '.min.js',
]

# 需要跳过的目录模式
SKIP_DIRS = [
    'node_modules',
    'dist',
    '.git',
    '__tests__',
    '__mocks__',
    'tests',
]


def _should_skip(filepath: str) -> bool:
    """判断是否应该跳过该文件。"""
    for pattern in SKIP_PATTERNS:
        if pattern in filepath:
            return True
    return False


def _replace_in_string_literals(content: str, translations: dict[str, str]) -> str:
    """
    只替换源码中的字符串字面量，不碰代码逻辑。

    策略：
    1. 找出所有字符串字面量的位置
    2. 对每个字符串内容检查是否在翻译字典中
    3. 如果匹配，替换字符串内容
    """
    # 匹配字符串字面量的正则（单引号、双引号、模板字符串）
    # 注意：这是简化版，不处理转义嵌套等极端情况
    patterns = [
        # 双引号字符串
        (r'"((?:[^"\\]|\\.)*)"', '"', '"'),
        # 单引号字符串
        (r"'((?:[^'\\]|\\.)*)'", "'", "'"),
        # 模板字符串（不含表达式的）
        (r"`((?:[^`\\]|\\.)*?)`", '`', '`'),
    ]

    result = content
    # 为了避免多次替换互相干扰，先收集所有替换，最后一次性应用
    replacements: list[tuple[int, int, str]] = []  # (start, end, new_content)

    for pattern, left_quote, right_quote in patterns:
        for match in re.finditer(pattern, result):
            inner = match.group(1)
            # 跳过空字符串
            if not inner.strip():
                continue
            # 跳过明显是代码的字符串（含大括号、等号、分号等）
            if any(c in inner for c in ['{', '}', '=>', 'function', 'return', ';']):
                continue
            # 跳过路径和 URL
            if '/' in inner and (inner.startswith('/') or inner.endswith('/') or '.' in inner):
                continue
            # 跳过变量引用（模板字符串里的 ${}）
            if '${' in inner:
                continue
            
            # 精确匹配
            translated = translations.get(inner)
            if not translated:
                # 试试去空格匹配
                stripped = inner.strip()
                if stripped in translations:
                    translated = translations[stripped]
                    # 保留原有的前后空格
                    leading = inner[:len(inner) - len(inner.lstrip())]
                    trailing = inner[len(inner.rstrip()):]
                    translated = leading + translated + trailing
            
            if translated:
                start = match.start()
                end = match.end()
                new_str = left_quote + translated + right_quote
                replacements.append((start, end, new_str))

    # 按位置从后往前替换，避免位置偏移
    replacements.sort(key=lambda x: x[0], reverse=True)
    for start, end, new_str in replacements:
        result = result[:start] + new_str + result[end:]

    return result


def _replace_jsx_text(content: str, translations: dict[str, str]) -> str:
    """
    替换 JSX 中的文本节点（>文本< 的形式）。
    """
    def replace_match(match):
        text = match.group(1).strip()
        if not text:
            return match.group(0)
        translated = translations.get(text)
        if translated:
            # 保留原有的前后空格
            full_text = match.group(1)
            leading = full_text[:len(full_text) - len(full_text.lstrip())]
            trailing = full_text[len(full_text.rstrip()):]
            return '>' + leading + translated + trailing + '<'
        return match.group(0)

    # 匹配 JSX 文本: > 文本 <
    # 排除包含 HTML 实体或明显是代码的情况
    pattern = r'>\s*([A-Za-z][A-Za-z0-9\s\?\.\!,\(\)\-\':/&;]{2,})\s*<'
    result = re.sub(pattern, replace_match, content)
    return result


def translate_source_file(
    filepath: Path,
    translations: dict[str, str],
    dry_run: bool = False,
) -> bool:
    """
    翻译单个源码文件。返回是否修改。
    """
    if _should_skip(str(filepath)):
        return False

    try:
        content = filepath.read_text(encoding='utf-8')
    except (UnicodeDecodeError, IOError):
        return False

    original = content

    # 1. 替换字符串字面量
    content = _replace_in_string_literals(content, translations)

    # 2. 替换 JSX 文本节点
    content = _replace_jsx_text(content, translations)

    if content != original and not dry_run:
        filepath.write_text(content, encoding='utf-8')

    return content != original


def apply_source_localization(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    对前端源码进行中文化。

    只处理 web/ 目录下的 JS/TS/JSX/TSX 文件。
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.translations_file:
        return modified

    # 加载翻译字典
    with open(config.translations_file, encoding='utf-8') as f:
        data = json.load(f)

    # 展开 modules 格式
    translations: dict[str, str] = {}
    if "modules" in data:
        for module in data["modules"].values():
            if isinstance(module, dict):
                translations.update(module)
    else:
        translations = data

    if not translations:
        return modified

    # 要处理的源码目录
    source_dirs = [
        ls_root / "web" / "apps",
        ls_root / "web" / "libs",
    ]

    for src_dir in source_dirs:
        if not src_dir.exists():
            continue

        for root, dirs, files in os.walk(str(src_dir)):
            # 跳过不需要的目录
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                if not any(filename.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx']):
                    continue

                filepath = Path(root) / filename
                if translate_source_file(filepath, translations, dry_run):
                    modified.append(str(filepath.relative_to(ls_root)))

    return modified


__all__ = ["apply_source_localization"]
