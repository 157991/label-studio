# Label Studio 白标体系

一套可复用的 Label Studio 品牌定制 + 中英双语方案。

## ✨ 特性

- 🎨 **品牌定制**: Logo、Favicon、品牌名、主题色一键替换
- 🌐 **中英双语**: 运行时注入，零侵入源码，右上角一键切换
- 🔄 **上游同步**: 无缝跟进 HumanSignal 官方更新
- 📦 **多品牌复用**: 一套框架，N 个品牌配置，按需构建
- 🎯 **最小侵入**: 只改 10 个左右关键文件，上游合并冲突极少

## 📁 目录结构

```
label-studio/
├── whitelabel/                  # 白标核心引擎
│   ├── cli.py                   # 命令行工具
│   ├── engine.py                # 核心引擎
│   ├── config.py                # 配置加载
│   ├── patches/                 # 各类补丁模块
│   │   ├── assets.py            # 静态资源替换 (logo/favicon)
│   │   ├── templates.py         # Django 模板修改
│   │   ├── frontend.py          # 前端关键组件修改
│   │   └── backend.py           # 后端品牌信息修改
│   └── i18n/
│       └── injector.py          # 中英双语注入
├── brands/                      # 品牌配置目录
│   ├── default/                 # 默认示例品牌
│   │   ├── brand.json           # 品牌配置
│   │   ├── logo.svg             # Logo
│   │   ├── logo-dark.svg        # 暗色 Logo
│   │   ├── favicon.ico          # Favicon
│   │   └── zh-CN.json           # 中文翻译字典
│   └── your-brand/              # 你的品牌（复制 default 修改）
│       └── ...
└── scripts/
    └── sync-upstream.sh         # 上游同步脚本
```

## 🚀 快速开始

### 1. 应用白标

```bash
# 预览（不实际修改）
python whitelabel/cli.py apply --brand brands/default/ --dry-run

# 实际应用
python whitelabel/cli.py apply --brand brands/default/
```

### 2. 添加新品牌

```bash
# 1. 复制默认品牌
cp -r brands/default brands/my-company

# 2. 修改 brand.json 中的品牌名、域名等

# 3. 替换 logo.svg, logo-dark.svg, favicon.ico 为你的品牌资源

# 4. （可选）修改 zh-CN.json 翻译字典

# 5. 应用
python whitelabel/cli.py apply --brand brands/my-company/
```

### 3. 查看状态

```bash
python whitelabel/cli.py status
```

### 4. 同步上游

```bash
# 添加 upstream remote（第一次需要）
git remote add upstream https://github.com/HumanSignal/label-studio.git

# 同步
./scripts/sync-upstream.sh
# 或
python whitelabel/cli.py sync-upstream

# 同步后重新应用白标
python whitelabel/cli.py apply --brand brands/default/
```

## 🔄 上游同步工作流

```
日常开发在 whitelabel 分支上

1. git fetch upstream develop
2. git merge upstream/develop
3. 解决冲突（极少，因为我们改的文件少）
4. 重新应用白标
5. 构建验证
6. 推送
```

### 冲突处理原则

| 文件类型 | 处理方式 |
|---------|---------|
| 白标引擎代码 (whitelabel/) | 用我们的版本 (ours) |
| Logo / Favicon 资源 | 用我们的版本 (ours) |
| 品牌配置 (brands/) | 用我们的版本 (ours) |
| Label Studio 业务代码 | 用上游版本 (theirs)，重新应用白标 |

```bash
# 冲突时，白标相关文件用我们的
git checkout --ours whitelabel/ brands/
git checkout --ours web/apps/labelstudio/src/assets/images/logo.svg

# Label Studio 代码用上游的
git checkout --theirs web/libs/editor/src/...

# 然后重新应用白标
python whitelabel/cli.py apply --brand brands/default/
```

## 🌐 中英双语机制

### 原理

不侵入 React 源码，通过注入 JS 脚本实现：

1. 页面加载时，将翻译字典注入到 `window.__WHITELABEL_TRANSLATIONS__`
2. 脚本遍历 DOM 文本节点，匹配翻译字典进行替换
3. 使用 MutationObserver 监听 DOM 变化，动态翻译新内容
4. 右上角悬浮切换按钮，语言偏好存 localStorage

### 优点

- ✅ 零侵入，不改一行 React 源码
- ✅ 即时切换，不用刷新页面
- ✅ 支持动态内容（Ajax 加载的内容也能翻译）
- ✅ 翻译字典独立，维护简单

### 扩展翻译

编辑 `brands/<品牌>/zh-CN.json`，添加新词条：

```json
{
  "Original English Text": "中文翻译",
  "Another string": "另一个字符串"
}
```

重新应用白标即可生效。

## 🎯 品牌替换覆盖范围

| 类别 | 位置 | 状态 |
|------|------|------|
| **Logo** | 前端 React 组件 (Menubar) | ✅ |
| | 登录页 Django 模板 | ✅ |
| | 错误页 (404/500/403) | ✅ |
| | 后端静态资源 | ✅ |
| **Favicon** | 前端 dist | ✅ |
| | 后端 static | ✅ |
| **品牌名** | 页面 `<title>` | ✅ |
| | 首页版本显示 | ✅ |
| | 注册/登录页 | ✅ |
| | 错误页 | ✅ |
| | 邮件模板 | ✅ |
| **外链** | Menubar Docs/GitHub/Slack | ✅ |
| | 底部 branding 链接 | ✅ |
| **国际化** | 全页面中英文切换 | ✅ |

## 🏗️ 架构设计

### 三层分离

```
上游代码 (develop 分支)
    ↓ 定期 merge
白标分支 (whitelabel 分支) ← 白标引擎 + 品牌配置
    ↓ 构建时应用
最终部署产物
```

### 为什么最小侵入？

- 全量正则替换 → 3944 个文件改动 → 每次上游合并都是灾难
- 最小侵入 → <20 个文件改动 → 冲突极少，秒解决
- 运行时注入 → 0 个源码文件改动 → 零冲突

## 📝 新增品牌清单

给新客户做白标时，检查以下清单：

- [ ] 创建 `brands/<品牌名>/` 目录
- [ ] 填写 `brand.json`（品牌名、域名、邮箱等）
- [ ] 准备 `logo.svg`（200x48 左右，透明背景）
- [ ] 准备 `logo-dark.svg`（暗色模式用）
- [ ] 准备 `favicon.ico`（32x32）
- [ ] 准备 `favicon.png`（可选）
- [ ] （可选）定制 `zh-CN.json` 翻译
- [ ] 应用白标：`python whitelabel/cli.py apply --brand brands/<品牌名>/`
- [ ] 构建前端 + 启动后端验证
- [ ] 检查登录页、首页、项目页的 Logo 和品牌名
- [ ] 检查中英文切换是否正常
- [ ] 检查错误页（访问不存在的页面看 404）

## 🔧 常见问题

### Q: 上游更新后白标会失效吗？
A: 不会。白标引擎是独立的，每次构建前重新 apply 就行。上游更新的是业务代码，白标是在构建时叠加的。

### Q: 翻译不全怎么办？
A: 编辑 `zh-CN.json` 加新词条，重新 apply 就行。翻译字典是增量的，不影响已有词条。

### Q: 我想完全去除中英文切换按钮怎么办？
A: 在 `brand.json` 里设置 `"i18n": { "enabled": false }`。

### Q: 怎么恢复到原版 Label Studio？
A: `git checkout -- .` 恢复所有被修改的文件即可。白标引擎本身的文件不受影响。
