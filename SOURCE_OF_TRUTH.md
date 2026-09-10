# 知识库导航 — haoka

多平台号卡商品数据聚合工具。

## 快速查找

| 要找什么 | 去哪里 | 备注 |
|---|---|---|
| 项目定位 | 本文件 | 多平台商品数据汇总仪表盘 |
| 前端代码 | `index.html` | 单页 HTML，直连 Supabase |
| 数据库 | Supabase `products` 表 | 存储 4 个平台商品数据 |
| 配置数据 | Supabase `app_config` 表 | 管理员密码 hash、手机号等 |
| 数据更新 | `import-local.py` | 从本地 /tmp/api*.json 导入 |
| 数据更新（在线） | `update-data.py` | 配置 API 地址后直接从接口拉取 |
| 建表 SQL | `supabase-schema.sql` | 含 products 和 app_config 表 |
| 权限控制 | `index.html#doAdminLogin()` | Supabase Auth 服务端会话鉴权（邮箱+密码），不再使用客户端校验 |
| 管理员账号 | Supabase Auth → Users | 在 Dashboard 的 Authentication → Users 中创建 |
| 访客读取 | Postgres 视图 `products_public` | 只含非敏感列；管理员登录后读 `products` 全表 |
| RLS 策略 | `.workbuddy/fix-auth-rls.sql` | anon 仅可读视图；写权限与全表读取仅 authenticated |
| 订单链接 | `index.html#setOrderUrls()` | 4 个平台各自的订单页 URL |
| 数据库保活 | `index.html#keepAlive()` | 管理员模式「💓」按钮，执行一次轻量查询防止 Supabase 闲置暂停；优先走 RPC `get_now()`（函数定义见 `supabase-schema.sql` 末尾，需在 SQL Editor 手动创建一次），未创建时自动回退为 `products` 轻量查询 |
| Supabase Project | `rnqrgmaeibwbfeqkjpky` | URL: https://rnqrgmaeibwbfeqkjpky.supabase.co |
| 在线地址 | GitHub Pages | https://victor-jl.github.io/haoka/ |
| GitHub 仓库 | `https://github.com/victor-jl/haoka` | |

## 项目说明

```text
haoka/
├── index.html            # 前端（直连 Supabase，已无后端依赖）
├── import-local.py       # 本地数据导入 Supabase
├── update-data.py        # 在线 API 数据更新脚本
├── supabase-schema.sql   # 建表 SQL
├── server.py             # (旧) 保留但不再部署使用
└── .gitignore
```

## 部署方式

**当前**：GitHub Pages — https://victor-jl.github.io/haoka/
- 仓库已公开，Pages 源为 `main` 分支 + 根目录 `/`，push 后自动构建（约 1 分钟）
- git remote 为 SSH：`git@github.com:victor-jl/haoka.git`（本机 `~/.ssh/id_ed25519` 已授权）
- 注意：钥匙串里的 `github-pat` 是**只读** token，只能读 API，不能 push

**历史**：CloudStudio 静态部署 https://d602fbfdcc27455190d527bbeed61754.app.codebuddy.work

## 维护规则

- 新增数据源时修改 `import-local.py` 和 `update-data.py` 的解析函数。
- 修改管理员密码：在 Supabase Dashboard → Authentication → Users 中重置，不要再用 `app_config`。
- 修改订单链接时更新 `index.html` 中的 `setOrderUrls()` 函数。
- 更新数据：在本地跑 `python3 import-local.py`（需配置 SUPABASE_SERVICE_KEY 环境变量）。
- 敏感信息（手机号、密码等）**不允许**硬编码在代码中，一律存入 `app_config` 表。
