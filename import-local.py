#!/usr/bin/env python3
"""
本地数据导入脚本 - 从 /tmp/api*.json 文件导入数据到 Supabase
适用于已有本地缓存的场景。

使用方法：
  1. 安装依赖：pip3 install requests
  2. 修改变量 SUPABASE_SERVICE_KEY
  3. 运行：python3 import-local.py
"""

import json
import os
import sys
import requests

# ===== Supabase 配置 =====
SUPABASE_URL = "https://rnqrgmaeibwbfeqkjpky.supabase.co"
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# 本地缓存文件路径
LOCAL_FILES = [
    ("卡之家", "/tmp/api1.json", {
        "source_url": "hk.ehaoka.com",
        "source_login_url": "https://hk.ehaoka.com/admin/",
    }),
    ("号易", "/tmp/api2.json", {
        "source_url": "et.haomifi.com",
        "source_login_url": "https://et.haomifi.com/admin/",
    }),
    ("172号卡", "/tmp/api3.json", {
        "source_url": "haokaapi.lot-ml.com",
        "source_login_url": "https://haoka.lot-ml.com/",
    }),
    ("政企校园卡", "/tmp/api4.json", {
        "source_url": "unionesim.com",
        "source_login_url": "https://unionesim.com/",
    }),
]


# ===== 解析函数 =====

def parse_kajiajia(raw_data, meta):
    """解析卡之家数据"""
    items = []
    data = raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
    product_list = data.get("list", []) if isinstance(data, dict) else (data or [])
    
    for item in (product_list or []):
        if not isinstance(item, dict):
            continue
        operator_map = ["", "移动", "联通", "电信", "广电"]
        op = item.get("operatorType", "")
        operator = operator_map[op] if isinstance(op, int) and op < len(operator_map) else str(op)
        
        tags = [t.get("label", "") for t in (item.get("tagsSelect", []) or [])]
        age_parts = (item.get("limitRule", {}) or {}).get("age", [])
        age_str = "~".join(str(a) for a in age_parts) if age_parts else "-"
        
        commission = item.get("commission", 0)
        price = item.get("price")
        
        items.append({
            "source": "卡之家",
            "source_url": meta["source_url"],
            "source_login_url": meta["source_login_url"],
            "product_id": str(item.get("id", "")),
            "name": item.get("name", "") or "",
            "detail_url": f"https://www.ehaoka.cn/shop#/pages/goods/index?goodsId={item.get('id', '')}&promoCode=Y9iVicCA",
            "operator": operator,
            "commission": f"¥{commission}",
            "price": f"¥{price}" if price else "-",
            "settle_mode": "一次性" if item.get("settleMode") == 1 else "次月返",
            "created_at": item.get("createdAt", "") or "",
            "tags": tags,
            "age": age_str,
            "share_link": "",
            "remark": "",
        })
    return items


def parse_haoyi(raw_data, meta):
    """解析号易数据"""
    items = []
    rows = raw_data.get("rows", []) if isinstance(raw_data, dict) else (raw_data or [])
    
    for item in (rows or []):
        if not isinstance(item, dict):
            continue
        items.append({
            "source": "号易",
            "source_url": meta["source_url"],
            "source_login_url": meta["source_login_url"],
            "product_id": str(item.get("id", "")),
            "name": item.get("goods_name", "") or "",
            "detail_url": f"https://my.86hk.vip/#/pages/goods/details?goods_id={item.get('id', '')}&share_id={item.get('agent_id', '')}",
            "operator": "",
            "commission": f"¥{item.get('agent_brokerage', 0)}",
            "price": "-",
            "settle_mode": "次月返" if item.get("settlement_method") == 2 else "一次性",
            "created_at": item.get("create_time", "") or "",
            "tags": item.get("point_msg", []) or [],
            "age": "-",
            "share_link": item.get("out_url", "") or "",
            "remark": item.get("point", "") or "",
        })
    return items


def parse_haoka172(raw_data, meta):
    """解析172号卡数据"""
    settle_map = {1: "月返", 2: "次月返", 3: "一次性", 4: "年返", 5: "季度返", 6: "半年返", 7: "一次性买断"}
    items = []
    data_list = raw_data.get("data", []) if isinstance(raw_data, dict) else (raw_data or [])
    
    for item in (data_list or []):
        if not isinstance(item, dict):
            continue
        age1 = item.get("age1", "")
        age2 = item.get("age2", "")
        age_str = f"{age1}~{age2}岁" if age1 or age2 else "-"
        
        tags = [item.get("areaRead", "") or ""]
        if item.get("disableArea"):
            tags.append(f"禁发{item.get('disableArea')}")
        tags = [t for t in tags if t]
        
        price = item.get("price")
        
        items.append({
            "source": "172号卡",
            "source_url": meta["source_url"],
            "source_login_url": meta["source_login_url"],
            "product_id": str(item.get("productID", "")),
            "name": item.get("productName", "") or "",
            "detail_url": f"https://sztc.rimian666.cn/h5orderEn/index?pudID={item.get('sn', '')}&userid={item.get('userSn', '')}",
            "operator": item.get("operator", "") or "",
            "commission": item.get("sPriceRead", "-") or "-",
            "price": f"¥{price}" if price else "-",
            "settle_mode": settle_map.get(item.get("backMoneyType"), str(item.get("backMoneyType", "-"))),
            "created_at": item.get("createTime", "") or "",
            "tags": tags,
            "age": age_str,
            "share_link": "",
            "remark": item.get("remark", "") or "",
        })
    return items


def parse_zhengqi(raw_data, meta):
    """解析政企校园卡数据"""
    items = []
    data_list = raw_data.get("data", []) if isinstance(raw_data, dict) else (raw_data or [])
    
    for item in (data_list or []):
        if not isinstance(item, dict):
            continue
        tags = [t for t in (item.get("tags", "") or "").split(",") if t]
        commission = item.get("commission_display") or f"¥{item.get('actual_commission', 0)}"
        
        items.append({
            "source": "政企校园卡",
            "source_url": meta["source_url"],
            "source_login_url": meta["source_login_url"],
            "product_id": str(item.get("id", "")),
            "name": item.get("name", "") or "",
            "detail_url": item.get("public_product_url", "https://unionesim.com/"),
            "operator": item.get("yys", "") or "",
            "commission": str(commission),
            "price": item.get("yuezu_format", "-") or "-",
            "settle_mode": item.get("js_type_text", "-") or "-",
            "created_at": item.get("create_time", "") or "",
            "tags": tags,
            "age": item.get("age", "-") or "-",
            "share_link": item.get("public_product_url", "") or "",
            "remark": item.get("mark", "") or "",
        })
    return items


PARSERS = {
    "卡之家": parse_kajiajia,
    "号易": parse_haoyi,
    "172号卡": parse_haoka172,
    "政企校园卡": parse_zhengqi,
}


# ===== 主流程 =====

def push_to_supabase(items, source_name):
    """将数据写入 Supabase"""
    if not items:
        print(f"  → {source_name}: 无数据，跳过")
        return 0

    if not SUPABASE_SERVICE_KEY:
        print(f"  → {source_name}: ⚠️ 未配置 SUPABASE_SERVICE_KEY，跳过写入")
        return 0

    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Prefer": "resolution=merge-duplicates",
    }

    # 先删除该来源的旧数据
    print(f"  → 清理旧数据...", end=" ")
    try:
        del_resp = requests.delete(f"{url}?source=eq.{source_name}", headers=headers)
        if del_resp.status_code not in (200, 204):
            print(f"⚠️ 删除返回 {del_resp.status_code}")
        else:
            print("✅")
    except Exception as e:
        print(f"❌ {e}")
        return 0

    # 批量插入
    total = len(items)
    batch_size = 1000
    inserted = 0
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        try:
            resp = requests.post(url, headers=headers, json=batch)
            if resp.status_code in (200, 201):
                inserted += len(batch)
                print(f"  → 已写入 {inserted}/{total}", end="\r")
            else:
                print(f"\n  → 批次失败: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"\n  → 异常: {e}")
    
    print(f"\n  → ✅ {source_name}: 写入 {inserted}/{total} 条")
    return inserted


def main():
    print("=" * 50)
    print("  haoka 本地数据导入 → Supabase")
    print("=" * 50)

    if not SUPABASE_SERVICE_KEY:
        print("\n⚠️  请先在脚本中配置 SUPABASE_SERVICE_KEY！")
        print("   路径: Supabase Dashboard → Settings → API → service_role key\n")
        sys.exit(1)

    total_all = 0
    for source_name, filepath, meta in LOCAL_FILES:
        print(f"\n📦 {source_name}")
        
        if not os.path.exists(filepath):
            print(f"  → ❌ 文件不存在: {filepath}")
            continue
        
        try:
            with open(filepath, "r") as f:
                raw_data = json.load(f)
            print(f"  → 读取文件: {filepath} ({os.path.getsize(filepath)//1024}KB)")
        except Exception as e:
            print(f"  → ❌ 读取失败: {e}")
            continue
        
        parser = PARSERS.get(source_name)
        if not parser:
            print(f"  → ❌ 没有对应的解析器")
            continue
        
        items = parser(raw_data, meta)
        print(f"  → 解析出 {len(items)} 条商品")
        
        inserted = push_to_supabase(items, source_name)
        total_all += inserted

    print(f"\n{'=' * 50}")
    print(f"  ✅ 完成！共导入 {total_all} 条商品数据")
    print(f"  🌐 GitHub Pages: https://victor-jl.github.io/haoka/（部署后生效）")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
