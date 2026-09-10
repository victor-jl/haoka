-- ============================================
-- 清空 products 表中的所有商品数据
-- 使用方式：在 Supabase Dashboard → SQL Editor 中运行
-- ============================================

DELETE FROM products;

-- 验证是否已清空（应返回 0 行）
SELECT COUNT(*) AS remaining_rows FROM products;
