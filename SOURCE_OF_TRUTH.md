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
| 权限控制 | `index.html` Supabase 配置 | SHA-256 密码验证，hash 存在 DB |
| 管理员密码 | `app_config` 表 → `admin_password_hash` | SHA-256 哈希存储在数据库 |
| 订单链接 | `index.html#setOrderUrls()` | 4 个平台各自的订单页 URL |
| Supabase Project | `rnqrgmaeibwbfeqkjpky` | URL: https://rnqrgmaeibwbfeqkjpky.supabase.co |
| 在线地址 | `import-local.py#L32-35` | 见 memory 日志 |
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

**当前**：CloudStudio 静态部署（纯前端 + Supabase）
**可选**：GitHub Pages（需将仓库公开）

## 维护规则

- 新增数据源时修改 `import-local.py` 和 `update-data.py` 的解析函数。
- 修改管理员密码：在 Supabase `app_config` 表中更新 `admin_password_hash`（SHA-256）。
- 修改订单链接时更新 `index.html` 中的 `setOrderUrls()` 函数。
- 更新数据：在本地跑 `python3 import-local.py`（需配置 SUPABASE_SERVICE_KEY 环境变量）。
- 敏感信息（手机号、密码等）**不允许**硬编码在代码中，一律存入 `app_config` 表。
