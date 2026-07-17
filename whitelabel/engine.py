"""
Label Studio 白标引擎 - 核心入口
应用品牌配置到 Label Studio 源码，支持多品牌复用。

执行顺序：
1. 静态资源替换 (logo, favicon)
2. 品牌清理 (CSS注入隐藏Heidi/AWS推广)
3. 前端关键组件修改 (品牌名、Logo引用等)
4. 后端品牌信息修改
5. Django 模板修改 (登录页、错误页等)
6. 后端源码中文化 (列名、筛选、actions 等Python字符串)
7. 注入运行时国际化 (增强版：MutationObserver + 双语切换)

设计原则：
- 安全第一：运行时注入优于源码修改
- 最小侵入：能不碰源码就不碰
- 可预测：每次 apply 结果一致
"""

from __future__ import annotations

from pathlib import Path

from .config import BrandConfig, load_brand_config
from .patches.assets import apply_asset_patches
from .patches.brand_cleanup import apply_brand_cleanup
from .patches.templates import apply_template_patches
from .patches.frontend import apply_frontend_patches
from .patches.backend import apply_backend_patches
from .patches.backend_i18n import apply_backend_localization
from .patches.source_i18n import apply_source_localization
from .patches.templates_i18n import apply_template_localization
from .i18n.injector import inject_i18n


class WhitelabelEngine:
    """白标引擎：加载品牌配置，应用所有补丁。"""

    def __init__(
        self,
        ls_root: str | Path,
        brand_path: str | Path,
        dry_run: bool = False,
    ):
        self.ls_root = Path(ls_root).resolve()
        self.brand_path = Path(brand_path).resolve()
        self.config: BrandConfig = load_brand_config(self.brand_path)
        self.dry_run = dry_run
        self.modified_files: list[str] = []

    def apply_all(self) -> dict:
        """应用所有白标补丁。返回修改统计。"""
        stats = {
            "brand": self.config.brand_name,
            "modified_files": [],
            "patches": {},
        }

        # 1. 静态资源替换 (logo, favicon 等)
        print("[1/9] 替换品牌资源 (logo, favicon...)")
        files = apply_asset_patches(self.ls_root, self.config, self.dry_run)
        stats["patches"]["assets"] = len(files)
        stats["modified_files"].extend(files)

        # 2. 品牌清理 (CSS注入隐藏 Heidi、AWS推广、外链等)
        if self.config.remove_branding:
            print("[2/9] 清理官方推广内容 (Heidi/AWS/外链...)")
            files = apply_brand_cleanup(self.ls_root, self.config, self.dry_run)
            stats["patches"]["cleanup"] = len(files)
            stats["modified_files"].extend(files)
        else:
            print("[2/9] 跳过品牌清理 (未启用)")
            stats["patches"]["cleanup"] = 0

        # 3. 前端关键组件修改 (Logo引用、品牌名等)
        print("[3/9] 修改前端关键组件...")
        files = apply_frontend_patches(self.ls_root, self.config, self.dry_run)
        stats["patches"]["frontend"] = len(files)
        stats["modified_files"].extend(files)

        # 3.5 前端源码级中文化 (基于翻译字典替换字符串)
        if self.config.source_i18n and self.config.translations_file:
            print("[3.5/9] 前端源码中文化 (Webhooks、页面文案...)")
            files = apply_source_localization(self.ls_root, self.config, self.dry_run)
            stats["patches"]["source_i18n"] = len(files)
            stats["modified_files"].extend(files)
        else:
            print("[3.5/9] 跳过前端源码中文化 (未启用)")
            stats["patches"]["source_i18n"] = 0

        # 4. 后端品牌信息修改
        print("[4/9] 修改后端品牌信息...")
        files = apply_backend_patches(self.ls_root, self.config, self.dry_run)
        stats["patches"]["backend"] = len(files)
        stats["modified_files"].extend(files)

        # 5. 后端源码中文化 (列名、筛选、actions 等)
        if self.config.backend_i18n and self.config.translations_file:
            print("[5/9] 后端源码中文化 (列名、筛选、actions...)")
            files = apply_backend_localization(self.ls_root, self.config, self.dry_run)
            stats["patches"]["backend_i18n"] = len(files)
            stats["modified_files"].extend(files)
        else:
            print("[5/9] 跳过后端中文化 (未启用)")
            stats["patches"]["backend_i18n"] = 0

        # 5.5 标注模板中文化 (分类名、模板标题)
        if self.config.source_i18n and self.config.translations_file:
            print("[5.5/9] 标注模板中文化 (分类、模板名...)")
            files = apply_template_localization(self.ls_root, self.config, self.dry_run)
            stats["patches"]["templates_i18n"] = len(files)
            stats["modified_files"].extend(files)
        else:
            print("[5.5/9] 跳过模板中文化 (未启用)")
            stats["patches"]["templates_i18n"] = 0

        # 6. Django 模板修改 (登录页、错误页等)
        print("[6/9] 修改后端模板...")
        files = apply_template_patches(self.ls_root, self.config, self.dry_run)
        stats["patches"]["templates"] = len(files)
        stats["modified_files"].extend(files)

        # 7. 注入运行时国际化 (增强版 MutationObserver)
        if self.config.i18n_enabled:
            print("[7/9] 注入运行时双语切换 (增强版)...")
            files = inject_i18n(self.ls_root, self.config, self.dry_run)
            stats["patches"]["i18n"] = len(files)
            stats["modified_files"].extend(files)
        else:
            print("[7/9] 跳过国际化 (未启用)")
            stats["patches"]["i18n"] = 0

        # 去重
        stats["modified_files"] = sorted(set(stats["modified_files"]))
        stats["total_modified"] = len(stats["modified_files"])

        return stats


def apply_whitelabel(
    ls_root: str | Path,
    brand_path: str | Path,
    dry_run: bool = False,
) -> dict:
    """便捷函数：应用白标。"""
    engine = WhitelabelEngine(ls_root, brand_path, dry_run)
    return engine.apply_all()


__all__ = ["WhitelabelEngine", "apply_whitelabel", "BrandConfig", "load_brand_config"]
