"""
品牌配置加载与验证。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BrandConfig:
    """品牌配置数据类。"""

    # 基础品牌信息
    brand_name: str = "Label Studio"
    brand_slug: str = "label-studio"
    brand_domain: str = "labelstud.io"
    support_email: str = "support@labelstud.io"

    # Logo 和图标
    logo_svg: Optional[str] = None           # logo.svg 路径
    logo_dark_svg: Optional[str] = None      # 暗色模式 logo
    favicon_ico: Optional[str] = None        # favicon.ico
    favicon_png: Optional[str] = None        # favicon.png

    # 主题色
    primary_color: str = "#2D8CF0"

    # 国际化
    i18n_enabled: bool = True
    default_language: str = "zh-CN"          # zh-CN 或 en
    translations_file: str | None = None  # 翻译字典 JSON 路径
    source_i18n: bool = False              # 前端源码级中文化（默认关闭，风险高）
    backend_i18n: bool = True              # 后端Python源码中文化（列名、筛选等，安全）

    # 外部链接替换
    external_links: dict[str, str] = field(default_factory=dict)
    # {原域名: 新域名}，例如 {"labelstud.io": "yourbrand.com"}

    # 移除的功能/链接
    remove_branding_links: bool = True         # 移除底部 branding 链接
    remove_external_docs: bool = False       # 移除文档外链
    remove_branding: bool = True              # 移除官方推广内容（Heidi、AWS卡片等）

    # 原始配置源路径（内部使用）
    _source_path: Optional[Path] = None


def load_brand_config(config_path: str | Path) -> BrandConfig:
    """从 JSON 文件加载品牌配置。"""
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"品牌配置文件不存在: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cfg = BrandConfig()
    cfg._source_path = path

    # 品牌基础信息
    brand = data.get("brand", {})
    cfg.brand_name = brand.get("name", cfg.brand_name)
    cfg.brand_slug = brand.get("slug", cfg.brand_slug)
    cfg.brand_domain = brand.get("domain", cfg.brand_domain)
    cfg.support_email = brand.get("support_email", cfg.support_email)

    # 主题色
    colors = data.get("colors", {})
    cfg.primary_color = colors.get("primary", cfg.primary_color)

    # Logo 和图标
    assets = data.get("assets", {})
    base_dir = path.parent
    for key in ["logo_svg", "logo_dark_svg", "favicon_ico", "favicon_png"]:
        val = assets.get(key)
        if val:
            p = Path(val)
            if not p.is_absolute():
                p = base_dir / p
            if p.exists():
                setattr(cfg, key, str(p))

    # 国际化
    i18n = data.get("i18n", {})
    cfg.i18n_enabled = i18n.get("enabled", cfg.i18n_enabled)
    cfg.default_language = i18n.get("default_language", cfg.default_language)
    cfg.source_i18n = i18n.get("source_i18n", cfg.source_i18n)
    cfg.backend_i18n = i18n.get("backend_i18n", cfg.backend_i18n)
    trans_file = i18n.get("translations_file")
    if trans_file:
        p = Path(trans_file)
        if not p.is_absolute():
            p = base_dir / p
        if p.exists():
            cfg.translations_file = str(p)

    # 外链
    links = data.get("links", {})
    cfg.external_links = links.get("replace", {})
    cfg.remove_branding_links = links.get("remove_branding", cfg.remove_branding_links)
    cfg.remove_external_docs = links.get("remove_external_docs", cfg.remove_external_docs)

    return cfg


def validate_config(config: BrandConfig) -> list[str]:
    """验证配置，返回警告列表。"""
    warnings = []

    if not config.logo_svg:
        warnings.append("未配置 logo_svg，将使用默认 logo")

    if config.logo_svg and not Path(config.logo_svg).exists():
        warnings.append("logo_svg 文件不存在")
    if config.favicon_ico and not Path(config.favicon_ico).exists():
        warnings.append("favicon_ico 文件不存在")

    if config.i18n_enabled and not config.translations_file:
        warnings.append("启用了 i18n 但未配置翻译文件")

    return warnings


__all__ = ["BrandConfig", "load_brand_config", "validate_config"]
