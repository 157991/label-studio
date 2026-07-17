#!/usr/bin/env python3
"""
Label Studio 白标 CLI 工具

用法:
  python whitelabel/cli.py apply --brand brands/default/
  python whitelabel/cli.py apply --brand brands/smartai/ --dry-run
  python whitelabel/cli.py sync-upstream                      # 同步上游
  python whitelabel/cli.py status                             # 查看当前状态
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 让 import 能找到 whitelabel 模块
sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_apply(args):
    """应用白标配置。"""
    from whitelabel.engine import apply_whitelabel

    ls_root = Path(args.ls_root).resolve()
    brand_path = Path(args.brand).resolve()

    if not brand_path.exists():
        print(f"❌ 品牌配置不存在: {brand_path}")
        sys.exit(1)

    # 支持传目录（默认读 brand.json）或直接传 JSON 文件
    if brand_path.is_dir():
        brand_path = brand_path / "brand.json"

    if args.dry_run:
        print("🔍 DRY RUN 模式 - 不会实际修改文件\n")

    print(f"🎨 应用白标: {brand_path}")
    print(f"📦 Label Studio: {ls_root}\n")

    stats = apply_whitelabel(ls_root, brand_path, dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print(f"✅ 完成！品牌: {stats['brand']}")
    print(f"📝 修改文件数: {stats['total_modified']}")
    print("\n各模块修改数:")
    for module, count in stats["patches"].items():
        print(f"  {module:15s}: {count} 个文件")

    if stats["modified_files"]:
        print(f"\n修改的文件 (前20个):")
        for f in stats["modified_files"][:20]:
            print(f"  - {f}")
        if len(stats["modified_files"]) > 20:
            print(f"  ... 还有 {len(stats['modified_files']) - 20} 个")

    return 0


def cmd_status(args):
    """查看当前白标状态。"""
    import subprocess

    ls_root = Path(args.ls_root).resolve()

    print(f"📦 Label Studio 根目录: {ls_root}")
    print()

    # git 状态
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(ls_root),
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    print(f"📊 Git 状态: {len(lines)} 个文件被修改")

    # 看看哪些是白标相关的
    wl_files = [l for l in lines if l.startswith("whitelabel/") or l.startswith("brands/")]
    ls_modified = [l for l in lines if not l.startswith("whitelabel/") and not l.startswith("brands/")]
    print(f"   ├─ 白标框架文件: {len(wl_files)}")
    print(f"   └─ Label Studio 源码: {len(ls_modified)}")

    # 可用品牌
    brands_dir = ls_root / "brands"
    if brands_dir.is_dir():
        brands = [d for d in brands_dir.iterdir() if d.is_dir()]
        print(f"\n🏷️  可用品牌 ({len(brands)} 个):")
        for b in brands:
            brand_json = b / "brand.json"
            if brand_json.exists():
                with open(brand_json, encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("brand", {}).get("name", b.name)
                i18n = "✓" if data.get("i18n", {}).get("enabled") else "✗"
                logo = "✓" if data.get("assets", {}).get("logo_svg") else "✗"
                print(f"   - {b.name:20s} | {name:20s} | logo:{logo}  i18n:{i18n}")

    return 0


def cmd_sync_upstream(args):
    """同步上游代码到当前分支。"""
    import subprocess

    ls_root = Path(args.ls_root).resolve()

    print("🔄 同步上游 Label Studio 代码...")
    print()

    # 1. 检查 upstream remote
    result = subprocess.run(
        ["git", "remote", "get-url", "upstream"],
        cwd=str(ls_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("❌ 未配置 upstream remote")
        print("   请先执行: git remote add upstream https://github.com/HumanSignal/label-studio.git")
        return 1

    upstream_url = result.stdout.strip()
    print(f"📍 上游: {upstream_url}")

    # 2. fetch upstream
    print("\n📥 Fetching upstream...")
    result = subprocess.run(
        ["git", "fetch", "upstream", args.branch],
        cwd=str(ls_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Fetch 失败: {result.stderr}")
        return 1
    print("   ✓ Fetch 成功")

    # 3. 当前分支
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(ls_root),
        capture_output=True,
        text=True,
    )
    current_branch = result.stdout.strip()
    print(f"🌿 当前分支: {current_branch}")

    # 4. 合并
    print(f"\n🔀 合并 upstream/{args.branch} 到 {current_branch}...")
    result = subprocess.run(
        ["git", "merge", "--no-ff", f"upstream/{args.branch}", "-m", f"Merge upstream/{args.branch} into {current_branch}"],
        cwd=str(ls_root),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("   ✓ 合并成功，无冲突！")
        print()
        print("✅ 上游同步完成！")
        print("   建议: 运行构建验证是否正常")
        print("         python whitelabel/cli.py apply --brand brands/default/")
        return 0
    else:
        print("   ⚠️  有冲突，需要手动解决")
        print()
        print("冲突文件:")
        # 列出冲突文件
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=str(ls_root),
            capture_output=True,
            text=True,
        )
        for line in result2.stdout.strip().split("\n"):
            if line:
                print(f"  - {line}")
        print()
        print("解决后执行: git add <文件> && git commit")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Label Studio 白标工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python whitelabel/cli.py apply --brand brands/default/
  python whitelabel/cli.py apply --brand brands/default/ --dry-run
  python whitelabel/cli.py sync-upstream
  python whitelabel/cli.py status
        """,
    )
    parser.add_argument(
        "--ls-root", default=".",
        help="Label Studio 根目录 (默认: 当前目录)",
    )

    sub = parser.add_subparsers(dest="command", help="命令")

    # apply
    apply_p = sub.add_parser("apply", help="应用白标配置")
    apply_p.add_argument("--brand", required=True, help="品牌目录或 brand.json 路径")
    apply_p.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")

    # sync-upstream
    sync_p = sub.add_parser("sync-upstream", help="同步上游代码")
    sync_p.add_argument("--branch", default="develop", help="上游分支名 (默认: develop)")

    # status
    sub.add_parser("status", help="查看白标状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "apply":
        return cmd_apply(args)
    elif args.command == "sync-upstream":
        return cmd_sync_upstream(args)
    elif args.command == "status":
        return cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
