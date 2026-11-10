#!/usr/bin/env python3
"""
批量查询 Wolf V2 和 Dolphin 配置接口

用法：
  python query_configs.py

运行后会提示输入：
  1. 机构 ID 列表（逗号分隔，如 A__map,DidaOpaq,AgodaUK）
  2. Dolphin API 的 Bearer Token（可选，不填则跳过 Dolphin 查询）

输出：
  - 终端打印所有配置查询结果
  - 同时写入 query_results.json 文件
"""

import json
import sys
import time
import urllib.request
import urllib.error

# ──────────────────────────────────────────
# 配置项定义
# ──────────────────────────────────────────

WOLF_V2_URL = "https://wolf-caller-api.didaadmin.com/api/v1/ClientConfigurations/GetConfigurationValueByClientIdAndKey"

DOLPHIN_URL_TEMPLATE = "http://wolf-v3-api.didainternal.com:8081/public/api/dolphin/config/{traceId}/{bizTier}/{key}"

# Wolf V2 配置项（按机构维度查询）
WOLF_V2_KEYS = [
    # ① 国籍处理
    ("DidaAPI.Config.CheckNationalityClient", "国籍检查开关（Nationality Free）"),
    ("Dida.Biz.Rate.NationalityHackUnified", "国籍 Hack 统一配置"),
    ("Dida.Biz.Rate.SubClientID", "子渠道/忽略国籍限制"),
    #  坑位合并
    ("Channel.MergeRatePlan.Config", "RP 合并/轮转配置"),
    # ④ 输出策略
    ("DidaAPI.Config.TopCountForBreakfastCancellation", "最优取消政策/坑位数量"),
    ("Channel.DuplicateRefundableAsNonRefundable", "复制可取消RP为不可取消"),
    # ③ RP 过滤
    ("DidaAPI.Config.NonRefundFilterV2", "不可取消 RP 过滤"),
    ("Dida.Biz.Rate.OccupancyFilterConfig", "入住人数过滤"),
    ("Channel.Rate.LowBalanceSwitchToCacheClientScopes", "低余额降级切缓存"),
    # 其他
    ("DidaAPI.Config.RPToHotelSearchV2", "询价代替（禁用RP合并的机构）"),
    ("Dida.Biz.SwitchConfig", "SwitchClient 配置"),
]

# Dolphin 配置项（全局配置）
DOLPHIN_KEYS = [
    ("Channel.MergeRatePlanDidaHotel.Config", 30, "酒店维度 RP 合并配置"),
    ("RedisConnectionString.Channel.MergeRatePlanData", 20, "RP 合并 Redis 连接串"),
]


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────

def http_post(url, data, headers=None, timeout=15):
    """发送 POST 请求"""
    if headers is None:
        headers = {}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={**{"Content-Type": "application/json", "Accept": "*/*"}, **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"success": False, "message": f"网络错误: {e}", "messageCode": 0, "data": None}
    except Exception as e:
        return {"success": False, "message": f"异常: {e}", "messageCode": 0, "data": None}


def http_get(url, headers=None, timeout=15):
    """发送 GET 请求"""
    if headers is None:
        headers = {}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"success": False, "message": f"网络错误: {e}", "messageCode": 0, "data": None}
    except Exception as e:
        return {"success": False, "message": f"异常: {e}", "messageCode": 0, "data": None}


def safe_parse_json(value):
    """尝试将字符串值解析为 JSON，失败则原样返回"""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(key, desc, result, indent="  "):
    """打印单个配置查询结果"""
    status = "✅" if result.get("success") else "❌"
    print(f"\n{indent}{status} {key}")
    print(f"{indent}   说明: {desc}")

    if not result.get("success"):
        print(f"{indent}   错误: {result.get('message', '未知错误')}")
        return

    data = result.get("data")
    if data is None:
        print(f"{indent}   值: (null) — 未配置，使用默认值")
    elif isinstance(data, str):
        # 尝试格式化 JSON
        parsed = safe_parse_json(data)
        if isinstance(parsed, (dict, list)):
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
            # 每行加缩进
            lines = formatted.split("\n")
            print(f"{indent}   值:")
            for line in lines:
                print(f"{indent}     {line}")
        else:
            print(f"{indent}   值: {data}")
    else:
        print(f"{indent}   值: {data}")


# ──────────────────────────────────────────
# Wolf V2 批量查询
# ──────────────────────────────────────────

def query_wolf_v2(client_ids, all_keys):
    """批量查询 Wolf V2 配置"""
    print_section("Wolf V2 配置查询")
    print(f"机构 ID: {', '.join(client_ids)}")
    print(f"配置项数量: {len(all_keys)}")

    results = {}

    for key, desc in all_keys:
        print(f"\n查询中: {key} ...")
        payload = {
            "clientIds": client_ids,
            "configurationKeys": [key],
        }
        result = http_post(WOLF_V2_URL, payload)
        results[key] = {"desc": desc, "result": result}
        print_result(key, desc, result)

    return results


# ──────────────────────────────────────────
# Dolphin 批量查询
# ──────────────────────────────────────────

def query_dolphin(bearer_token, all_keys):
    """批量查询 Dolphin 配置"""
    print_section("Dolphin 全局配置查询")
    print(f"配置项数量: {len(all_keys)}")

    results = {}
    trace_id = time.strftime("%Y%m%d%H%M%S")

    for key, biz_tier, desc in all_keys:
        url = DOLPHIN_URL_TEMPLATE.format(
            traceId=trace_id,
            bizTier=biz_tier,
            key=key,
        )
        print(f"\n查询中: {key} (bizTier={biz_tier}) ...")
        headers = {"Authorization": f"Bearer {bearer_token}"}
        result = http_get(url, headers=headers)
        results[key] = {"desc": desc, "bizTier": biz_tier, "result": result}
        print_result(key, desc, result, indent="  ")

    return results


# ──────────────────────────────────────────
# 保存结果
# ──────────────────────────────────────────

def save_results(wolf_results, dolphin_results, client_ids):
    """将结果保存到 JSON 文件"""
    output = {
        "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "client_ids": client_ids,
        "wolf_v2": {},
        "dolphin": {},
    }

    for key, info in wolf_results.items():
        output["wolf_v2"][key] = {
            "desc": info["desc"],
            "success": info["result"].get("success", False),
            "message": info["result"].get("message", ""),
            "raw_data": info["result"].get("data"),
        }

    for key, info in dolphin_results.items():
        output["dolphin"][key] = {
            "desc": info["desc"],
            "bizTier": info["bizTier"],
            "success": info["result"].get("success", False),
            "message": info["result"].get("message", ""),
            "raw_data": info["result"].get("data"),
        }

    output_file = "query_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")


# ──────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────

def main():
    print("渠道侧配置批量查询工具")
    print("-" * 40)

    # 输入机构 ID
    raw_ids = input("请输入机构 ID（逗号分隔，如 A__map,DidaOpaq,AgodaUK）: ").strip()
    if not raw_ids:
        print("错误: 机构 ID 不能为空")
        sys.exit(1)

    client_ids = [cid.strip() for cid in raw_ids.split(",") if cid.strip()]
    print(f"解析到 {len(client_ids)} 个机构: {client_ids}")

    # 输入 Dolphin Token（可选）
    bearer_token = input("请输入 Dolphin API Bearer Token（回车跳过）: ").strip()

    # 查询 Wolf V2
    wolf_results = query_wolf_v2(client_ids, WOLF_V2_KEYS)

    # 查询 Dolphin
    dolphin_results = {}
    if bearer_token:
        dolphin_results = query_dolphin(bearer_token, DOLPHIN_KEYS)
    else:
        print("\n️  未提供 Dolphin Token，跳过 Dolphin 配置查询")

    # 保存结果
    save_results(wolf_results, dolphin_results, client_ids)

    print("\n查询完成！")


if __name__ == "__main__":
    main()
