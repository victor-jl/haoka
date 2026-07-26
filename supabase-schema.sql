-- ============================================
-- Supabase 建表脚本 - haoka 商品数据
-- 在 Supabase Dashboard → SQL Editor 中运行
-- ============================================

-- 创建 products 表
CREATE TABLE IF NOT EXISTS products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source TEXT NOT NULL,                  -- 来源：卡之家/号易/172号卡/政企校园卡
  source_url TEXT,                       -- 平台域名
  source_login_url TEXT,                 -- 平台登录地址
  product_id TEXT,                       -- 商品在平台的原始ID
  name TEXT NOT NULL,                    -- 商品名称
  detail_url TEXT,                       -- 详情/领取链接
  operator TEXT,                         -- 运营商
  commission TEXT,                       -- 佣金
  price TEXT,                            -- 价格
  settle_mode TEXT,                      -- 结算方式
  tags JSONB DEFAULT '[]'::jsonb,       -- 标签数组
  age TEXT,                              -- 年龄要求
  created_at TEXT,                       -- 创建时间
  share_link TEXT,                       -- 分享链接
  claim_link TEXT,                       -- 领取链接（与 detail_url 相同，但直接存储）
  qr_code TEXT,                          -- 二维码 base64 data URL（导入时预生成）
  remark TEXT,                           -- 备注
  updated_at TIMESTAMPTZ DEFAULT NOW()   -- 更新时间
);

-- 创建索引：按来源查询加速
CREATE INDEX IF NOT EXISTS idx_products_source ON products (source);

-- 创建索引：按商品名搜索加速
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin (name gin_trgm_ops);
-- 需要先安装扩展：CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ========== 权限设置 ==========

-- 启用行级安全
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 允许匿名用户读取（公开访问）
CREATE POLICY "允许公开读取"
  ON products FOR SELECT
  USING (true);

-- 允许匿名用户更新（前端页面更新 QR 码和链接）
CREATE POLICY "允许公开更新"
  ON products FOR UPDATE
  USING (true)
  WITH CHECK (true);

-- 只有持有 service_role key 的后台脚本才能写入
-- （更新脚本里用 service_role key，不需要额外建 policy）

-- ============================================
-- app_config 配置表（存储敏感信息，以 hash 形式）
-- ============================================
CREATE TABLE IF NOT EXISTS app_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE app_config ENABLE ROW LEVEL SECURITY;

-- 允许公开读取配置（值已做 hash 处理，如密码是 SHA-256）
CREATE POLICY "允许公开读取配置"
  ON app_config FOR SELECT
  USING (true);

-- ============================================
-- 若已有表，追加新列（非破坏性迁移）
-- ============================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS claim_link TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_code TEXT;
