-- ============================================
-- 临时清理脚本：去重 + 陈旧数据失效
-- 使用方式：在 Supabase SQL Editor 中运行
-- 日期：2026-07-26（根据实际日期修改）
-- ============================================

-- 1. 非今天创建的数据全部置为失效
UPDATE products
SET active = false
WHERE (active IS NULL OR active = true)
  AND created_at NOT LIKE '2026-07-26%';

-- 2. 今天创建的数据，按 source + product_id 分组去重
-- 同一组内仅保留 id 最大的那条，其余置为失效
UPDATE products p
SET active = false
WHERE (p.active IS NULL OR p.active = true)
  AND p.created_at LIKE '2026-07-26%'
  AND p.id NOT IN (
    SELECT MAX(id)
    FROM products
    WHERE created_at LIKE '2026-07-26%'
      AND (active IS NULL OR active = true)
    GROUP BY source, COALESCE(product_id, '')
  );
