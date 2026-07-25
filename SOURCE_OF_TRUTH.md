# 知识库导航 — haoka

多平台号卡商品数据聚合工具。

## 快速查找

| 要找什么 | 去哪里 | 备注 |
|---|---|---|
| 项目定位与功能介绍 | `README.md`（如下） | 多平台商品数据汇总仪表盘 |
| 后端服务代码 | `server.py` | Python HTTP 服务器，端口 8899 |
| 前端页面代码 | `index.html` | 单页 HTML，含 JS 与 CSS |
| 数据来源配置 | `server.py#L10-L11` | 4 个 json 文件 → SQLite 缓存 |
| 登录方式 | `server.py#L115-L146` | POST /api/send-code, /api/verify-code, /api/logout; 仅 `17602111723` 可通过验证码登录 |
| API 路由 | `server.py#L66-L100` | GET /api/api1~4, /api/refresh, /api/check-session; POST /api/send-code, /api/verify-code, /api/logout, /api/update |
| 权限控制 | `index.html#L405-L424` | 分享页免登录，主页面手机验证码登录，仅 `17602111723` 有 admin 权限 |
| 订单链接 | `index.html#L292-L309` | 4 个平台各自的订单页 URL |
| GitHub 仓库 | `https://github.com/victor-jl/haoka` | |

## 项目说明

```text
haoka/
├── server.py          # 后端：SQLite 数据缓存 + HTTP API
├── index.html         # 前端：表格展示 + 搜索/筛选/订单入口
└── .gitignore         # Git 忽略规则
```

## 目录职责

| 路径 | 放什么 | 不放什么 |
|---|---|---|
| `haoka/` | 项目核心代码（server.py, index.html） | 临时文件、截图、其他项目 |

## 维护规则

- 新增 API 数据来源时更新 `server.py` 中的 `API_FILES` 列表。
- 修改前端列权限时更新 `index.html` 中的 `login-hide` class 逻辑。
- 变更 admin 手机号时更新 `server.py#L18` 的 `ADMIN_PHONE`。
- 修改订单链接时更新 `index.html` 中的 `setOrderUrls()` 函数。
- 通过 `POST /api/update` 传入 curl 命令更新某个 API 的缓存数据。
