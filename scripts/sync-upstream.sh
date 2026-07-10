#!/bin/bash
#
# 同步上游 Label Studio 代码到当前分支
#
# 用法:
#   ./scripts/sync-upstream.sh              # 同步 upstream/develop 到当前分支
#   ./scripts/sync-upstream.sh main         # 同步 upstream/main
#
# 流程:
#   1. fetch upstream
#   2. 合并到当前分支
#   3. 有冲突的话提示手动解决
#   4. 合并完成后提示重新应用白标

set -e

BRANCH="${1:-develop}"

echo "🔄 同步上游 Label Studio ($BRANCH)..."
echo

# 检查是否在 git 仓库
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 不在 git 仓库中"
    exit 1
fi

# 检查 upstream remote
if ! git remote get-url upstream > /dev/null 2>&1; then
    echo "❌ 未配置 upstream remote"
    echo "   执行: git remote add upstream https://github.com/HumanSignal/label-studio.git"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
echo "🌿 当前分支: $CURRENT_BRANCH"
echo "📍 上游分支: upstream/$BRANCH"
echo

# 检查是否有未提交的修改
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  有未提交的修改，请先提交或 stash"
    echo "   git stash  # 暂存修改"
    echo "   同步完后: git stash pop  # 恢复"
    exit 1
fi

# Fetch
echo "📥 Fetching upstream/$BRANCH..."
git fetch upstream "$BRANCH"
echo "   ✓ Fetch 成功"
echo

# 合并
echo "🔀 合并 upstream/$BRANCH -> $CURRENT_BRANCH..."
if git merge --no-ff "upstream/$BRANCH" -m "Merge upstream/$BRANCH into $CURRENT_BRANCH"; then
    echo "   ✓ 合并成功，无冲突！"
    echo
    echo "✅ 上游同步完成！"
    echo
    echo "下一步: 重新应用白标并验证"
    echo "   python whitelabel/cli.py apply --brand brands/default/"
    echo "   # 然后构建前端 + 启动服务验证"
else
    echo
    echo "⚠️  有冲突！请手动解决。"
    echo
    echo "冲突文件列表:"
    git diff --name-only --diff-filter=U
    echo
    echo "解决冲突后:"
    echo "   git add <文件>"
    echo "   git commit"
    echo
    echo "白标相关冲突处理建议:"
    echo "   - logo/favicon 等资源文件 → 用我们的版本 (git checkout --ours <file>)"
    echo "   - 白标引擎代码 (whitelabel/) → 用我们的版本"
    echo "   - Label Studio 业务代码 → 用上游版本，重新应用白标"
    exit 1
fi
