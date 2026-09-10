# haoka · 多平台号卡商品数据汇总

聚合 **卡之家 / 号易 / 172号卡 / 政企校园卡** 四个平台的号卡商品数据，统一展示、搜索与筛选，一个页面看完所有渠道的商品和佣金。

## 🔗 在线访问

**https://victor-jl.github.io/haoka/**

纯静态单页，打开即用。加 `?share` 参数（如 `https://victor-jl.github.io/haoka/?share`）进入分享模式，隐藏佣金、价格等敏感列。

## ✨ 功能

- **四平台聚合**：一次加载全部渠道商品，按来源、运营商筛选
- **分类标签**：号卡 / 宽带 / 移动 WiFi 自动归类
- **关键词搜索**：商品名、标签实时匹配
- **表格 / 卡片双视图**：桌面看表格，手机看卡片
- **管理员模式**：用 Supabase 账号登录（服务端会话鉴权）后显示佣金、结算方式、备注，以及订单入口、二维码、数据导入等功能；未登录访客只能读到不含敏感列的公开视图
- **数据库保活**：管理员模式下的 💓 按钮，一键执行轻量查询，防止 Supabase 免费项目因闲置暂停（另有每 3 天自动执行的定时任务）

## 🛠 技术架构

纯前端 + BaaS，没有自建后端：

- 前端：单页 HTML（`index.html`），原生 JS，无构建步骤
- 数据：Supabase（PostgreSQL + PostgREST），前端通过 `supabase-js` 直连
- 托管：GitHub Pages（推送到 `main` 分支自动部署）

## 📁 目录结构

```
haoka/
├── index.html            # 前端页面（直连 Supabase）
├── supabase-schema.sql   # 建表 SQL + get_now() 保活函数
├── import-local.py       # 从本地 JSON 导入数据到 Supabase
├── update-data.py        # 配置 API 后从接口在线拉取更新
├── clear-data.sql        # 清空商品数据（慎用）
├── cleanup-duplicates.sql# 清理重复数据
└── server.py             # 早期后端，已不再使用
```

## 🚀 本地运行

```bash
python3 -m http.server 8173
# 打开 http://127.0.0.1:8173/index.html
```

> 需要用**系统浏览器**打开。部分内嵌预览窗口无法访问外网，会导致数据加载失败。

## 🔄 更新数据

```bash
export SUPABASE_SERVICE_KEY=你的_service_role_key
python3 import-local.py      # 从本地 /tmp/api*.json 导入
python3 update-data.py       # 或直接从平台接口拉取
```

新增数据源时，修改 `import-local.py` / `update-data.py` 里对应的解析函数即可。

## 📦 部署

推送到 `main` 分支后，GitHub Pages 约 1 分钟自动完成部署：

```bash
git push origin main
```

## 🔒 说明

- 管理员密码以 SHA-256 哈希形式存于 Supabase `app_config` 表，手机号等敏感信息同样存库，不硬编码在代码中
- 前端使用的 Supabase `anon key` 为公开只读用途，配合行级安全策略（RLS）使用
