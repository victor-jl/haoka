#!/usr/bin/env python3
"""
数据更新脚本 - 从各平台 API 拉取数据并推送到 Supabase

使用方法：
  1. 先安装依赖：pip3 install requests supabase
  2. 修改下面的 SUPABASE_URL 和 SUPABASE_SERVICE_KEY（在 Supabase Dashboard → Settings → API → service_role key）
  3. 修改 API_CONFIG 里的接口地址和参数
  4. 运行：python3 update-data.py
"""

import json
import os
import sys
import requests

# ===== 配置 =====

# Supabase 配置（从 Settings → API 获取）
SUPABASE_URL = "https://rnqrgmaeibwbfeqkjpky.supabase.co"
SUPABASE_SERVICE_KEY = ""  # ← 请填写 service_role key（在 Settings → API 页面）

# API 接口配置（请根据实际情况修改）
API_CONFIG = [
    {
        "name": "卡之家",
        "source_url": "hk.ehaoka.com",
        "source_login_url": "https://hk.ehaoka.com/admin/",
        "url": "",  # ← 填写实际的 API 接口地址
        "method": "GET",
        "headers": {},
        "parse": "kajiajia",  # 解析方式
    },
    {
        "name": "号易",
        "source_url": "et.haomifi.com",
        "source_login_url": "https://et.haomifi.com/admin/",
        "url": "",
        "method": "GET",
        "headers": {},
        "parse": "haoyi",
    },
    {
        "name": "172号卡",
        "source_url": "haokaapi.lot-ml.com",
        "source_login_url": "https://haoka.lot-ml.com/",
        "url": "",
        "method": "GET",
        "headers": {},
        "parse": "haoka172",
    },
    {
        "name": "政企校园卡",
        "source_url": "unionesim.com",
        "source_login_url": "https://unionesim.com/",
        "url": "",
        "method": "GET",
        "headers": {},
        "parse": "zhengqi",
    },
]


# ===== 数据解析函数 =====

def parse_kajiajia(data):
    """解析卡之家 API 返回"""
    items = []
    for item in (data.get("data", {}) if isinstance(data, dict) and "data" in data else data or []):
        if isinstance(item, dict):
            items.append({
                "source": "卡之家",
                "source_url": "hk.ehaoka.com",
                "source_login_url": "https://hk.ehaoka.com/admin/",
                "product_id": str(item.get("id", "")),
                "name": item.get("name", ""),
                "detail_url": "https://www.ehaoka.cn/shop#/pages/goods/index?goodsId=" + str(item.get("id", "")) + "&promoCode=Y9iVicCA",
                "operator": ["", "移动", "联通", "电信", "广电"][item.get("operatorType", 0)] if isinstance(item.get("operatorType"), int) else str(item.get("operatorType", "")),
                "commission": "¥" + str(item.get("commission", 0)),
                "price": "¥" + str(item.get("price", 0)) if item.get("price") else "-",
                "settle_mode": "一次性" if item.get("settleMode") == 1 else "次月返",
                "created_at": item.get("createdAt", ""),
                "tags": json.dumps([t.get("label", "") for t in (item.get("tagsSelect", []) or [])], ensure_ascii=False),
                "age": "~".join(str(a) for a in (item.get("limitRule", {}) or {}).get("age", [])) or "-",
                "share_link": "",
                "remark": "",
            })
    return items


def parse_haoyi(data):
    """解析号易 API 返回"""
    items = []
    for item in (data.get("rows", []) if isinstance(data, dict) else data or []):
        if isinstance(item, dict):
            items.append({
                "source": "号易",
                "source_url": "et.haomifi.com",
                "source_login_url": "https://et.haomifi.com/admin/",
                "product_id": str(item.get("id", "")),
                "name": item.get("goods_name", ""),
                "detail_url": "https://my.86hk.vip/#/pages/goods/details?goods_id=" + str(item.get("id", "")) + "&share_id=" + str(item.get("agent_id", "")),
                "operator": "",
                "commission": "¥" + str(item.get("agent_brokerage", 0)),
                "price": "-",
                "settle_mode": "次月返" if item.get("settlement_method") == 2 else "一次性",
                "created_at": item.get("create_time", ""),
                "tags": json.dumps(item.get("point_msg", []) or [], ensure_ascii=False),
                "age": "-",
                "share_link": item.get("out_url", ""),
                "remark": item.get("point", ""),
            })
    return items


def parse_haoka172(data):
    """解析172号卡 API 返回"""
    settle_map = {1: "月返", 2: "次月返", 3: "一次性", 4: "年返", 5: "季度返", 6: "半年返", 7: "一次性买断"}
    items = []
    for item in (data.get("data", []) if isinstance(data, dict) else data or []):
        if isinstance(item, dict):
            age1 = item.get("age1", "")
            age2 = item.get("age2", "")
            age_str = f"{age1}~{age2}岁" if age1 or age2 else "-"
            tags = [item.get("areaRead", ""), ("禁发" + item.get("disableArea", "")) if item.get("disableArea") else ""]
            tags = [t for t in tags if t]
            items.append({
                "source": "172号卡",
                "source_url": "haokaapi.lot-ml.com",
                "source_login_url": "https://haoka.lot-ml.com/",
                "product_id": str(item.get("productID", "")),
                "name": item.get("productName", ""),
                "detail_url": "https://sztc.rimian666.cn/h5orderEn/index?pudID=" + str(item.get("sn", "")) + "&userid=" + str(item.get("userSn", "")),
                "operator": item.get("operator", ""),
                "commission": item.get("sPriceRead", "-"),
                "price": "¥" + str(item.get("price", "")) if item.get("price") else "-",
                "settle_mode": settle_map.get(item.get("backMoneyType"), str(item.get("backMoneyType", "-"))),
                "created_at": item.get("createTime", ""),
                "tags": json.dumps(tags, ensure_ascii=False),
                "age": age_str,
                "share_link": "",
                "remark": item.get("remark", ""),
            })
    return items


def parse_zhengqi(data):
    """解析政企校园卡 API 返回"""
    items = []
    for item in (data.get("data", []) if isinstance(data, dict) else data or []):
        if isinstance(item, dict):
            items.append({
                "source": "政企校园卡",
                "source_url": "unionesim.com",
                "source_login_url": "https://unionesim.com/",
                "product_id": str(item.get("id", "")),
                "name": item.get("name", ""),
                "detail_url": item.get("public_product_url", "https://unionesim.com/"),
                "operator": item.get("yys", ""),
                "commission": item.get("commission_display", "¥" + str(item.get("actual_commission", 0))),
                "price": item.get("yuezu_format", "-"),
                "settle_mode": item.get("js_type_text", "-"),
                "created_at": item.get("create_time", ""),
                "tags": json.dumps([t for t in (item.get("tags", "") or "").split(",") if t], ensure_ascii=False),
                "age": item.get("age", "-"),
                "share_link": item.get("public_product_url", ""),
                "remark": item.get("mark", ""),
            })
    return items


PARSERS = {
    "kajiajia": parse_kajiajia,
    "haoyi": parse_haoyi,
    "haoka172": parse_haoka172,
    "zhengqi": parse_zhengqi,
}


# ===== 主流程 =====

def fetch_api(config):
    """调用 API 获取数据"""
    print(f"  → 正在拉取 {config['name']}...", end=" ")
    try:
        if config["method"] == "GET":
            resp = requests.get(config["url"], headers=config["headers"], timeout=30)
        else:
            resp = requests.post(config["url"], headers=config["headers"], json=config.get("body", {}), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"✅ 成功 ({len(json.dumps(data))} bytes)")
        return data
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def push_to_supabase(items, source_name):
    """将数据 upsert 到 Supabase"""
    if not items:
        print(f"  → {source_name}: 无数据，跳过")
        return 0, 0

    if not SUPABASE_SERVICE_KEY:
        print(f"  → {source_name}: ⚠️ 未配置 service_role key，跳过写入")
        return 0, 0

    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Prefer": "resolution=merge-duplicates",
    }

    # 先删除该来源的旧数据
    print(f"  → 清理 {source_name} 旧数据...", end=" ")
    try:
        del_resp = requests.delete(
            f"{url}?source=eq.{source_name}",
            headers=headers
        )
        if del_resp.status_code not in (200, 204):
            print(f"⚠️ 删除返回 {del_resp.status_code}")
        else:
            print("✅")
    except Exception as e:
        print(f"❌ {e}")

    # 批量插入新数据（最多每批 1000 条）
    batch_size = 1000
    total = len(items)
    inserted = 0
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        try:
            resp = requests.post(url, headers=headers, json=batch)
            if resp.status_code in (200, 201):
                inserted += len(batch)
            else:
                print(f"  → 批次 {i//batch_size + 1} 失败: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"  → 批次 {i//batch_size + 1} 异常: {e}")

    return total, inserted


def main():
    print("=" * 50)
    print("  haoka 数据更新工具 → Supabase")
    print("=" * 50)

    if not SUPABASE_SERVICE_KEY:
        print("\n⚠️  请先在脚本中配置 SUPABASE_SERVICE_KEY！")
        print("   在 Supabase Dashboard → Settings → API → service_role key 获取\n")

    total_all = 0
    for api in API_CONFIG:
        print(f"\n📦 {api['name']}")
        if not api["url"]:
            print(f"  → ⏭️  未配置接口地址，跳过")
            continue

        data = fetch_api(api)
        if data is None:
            continue

        parser = PARSERS.get(api["parse"])
        if not parser:
            print(f"  → ❌ 未知的解析方式: {api['parse']}")
            continue

        items = parser(data)
        print(f"  → 解析出 {len(items)} 条商品")

        total, inserted = push_to_supabase(items, api["name"])
        print(f"  → ✅ 已写入 {inserted}/{total} 条")
        total_all += inserted

    print(f"\n{'=' * 50}")
    print(f"  ✅ 完成！共更新 {total_all} 条商品数据")
    print(f"  🌐 前端地址: https://victor-jl.github.io/haoka/")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
