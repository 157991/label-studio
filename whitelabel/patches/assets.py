"""
静态资源替换补丁 - logo, favicon, 图片等。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..config import BrandConfig


def _copy_if_exists(src: str | None, dst: Path, dry_run: bool = False) -> bool:
    """如果源文件存在，复制到目标。返回是否成功。"""
    if not src:
        return False
    src_path = Path(src)
    if not src_path.exists():
        return False
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst)
    return True


def apply_asset_patches(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """
    应用品牌资源替换。

    覆盖位置：
    - 前端源码 assets/images/ (开发时用)
    - 前端 dist 产物 (已构建时用)
    - 后端 Django static/images/
    - 后端 Django static/icons/
    """
    modified: list[str] = []
    ls_root = Path(ls_root)

    # ========== Logo SVG ==========
    if config.logo_svg:
        targets = [
            # 前端源码
            ls_root / "web" / "apps" / "labelstudio" / "src" / "assets" / "images" / "logo.svg",
            # 前端 dist 构建产物
            ls_root / "web" / "dist" / "apps" / "labelstudio" / "images" / "logo.svg",
            # 后端 static
            ls_root / "label_studio" / "core" / "static" / "images" / "logo.svg",
            ls_root / "label_studio" / "core" / "static" / "icons" / "logo.svg",
            ls_root / "label_studio" / "core" / "static" / "icons" / "logo-black.svg",
        ]

        for dst in targets:
            if _copy_if_exists(config.logo_svg, dst, dry_run):
                modified.append(str(dst.relative_to(ls_root)))

    # ========== 暗色 Logo ==========
    if config.logo_dark_svg:
        targets = [
            ls_root / "web" / "apps" / "labelstudio" / "src" / "assets" / "images" / "logo-dark.svg",
            ls_root / "web" / "dist" / "apps" / "labelstudio" / "images" / "logo-dark.svg",
        ]
        for dst in targets:
            if _copy_if_exists(config.logo_dark_svg, dst, dry_run):
                modified.append(str(dst.relative_to(ls_root)))

    # ========== Favicon ICO ==========
    if config.favicon_ico:
        targets = [
            ls_root / "web" / "apps" / "labelstudio" / "src" / "assets" / "images" / "favicon.ico",
            ls_root / "web" / "dist" / "apps" / "labelstudio" / "images" / "favicon.ico",
            ls_root / "label_studio" / "core" / "static" / "images" / "favicon.ico",
        ]
        for dst in targets:
            if _copy_if_exists(config.favicon_ico, dst, dry_run):
                modified.append(str(dst.relative_to(ls_root)))

    # ========== Favicon PNG ==========
    if config.favicon_png:
        targets = [
            ls_root / "web" / "apps" / "labelstudio" / "src" / "assets" / "images" / "favicon.png",
            ls_root / "web" / "dist" / "apps" / "labelstudio" / "images" / "favicon.png",
            ls_root / "label_studio" / "core" / "static" / "images" / "favicon.png",
        ]
        for dst in targets:
            if _copy_if_exists(config.favicon_png, dst, dry_run):
                modified.append(str(dst.relative_to(ls_root)))

    return modified


__all__ = ["apply_asset_patches"]
