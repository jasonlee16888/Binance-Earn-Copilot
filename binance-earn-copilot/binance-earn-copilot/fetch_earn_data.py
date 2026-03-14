import os
import json
import concurrent.futures
from binance.client import Client

def fetch_coin_data(client, coin):
    """单独拉取某个币种数据的函数（供多线程调用）"""
    try:
        response = client.get_simple_earn_flexible_product_list(asset=coin)

        if "rows" in response and len(response["rows"]) > 0:
            product = response["rows"][0]

            base_apr = float(product.get("latestAnnualPercentageRate", "0"))
            tier_info = product.get("tierAnnualPercentageRate", "无阶梯补贴")

            return {
                "asset": coin,
                "product_id": product.get("productId"),
                "base_apy_percent": round(base_apr * 100, 2),
                "tier_bonus_info": tier_info,
                "status": product.get("status")
            }

    except Exception as e:
        return {"asset": coin, "error": str(e)}

    return None

def get_stablecoin_earn_data():
    # 优先从 .env 文件读取 API Key 和 Secret，如果不存在则从环境变量读取
    api_key = None
    api_secret = None
    
    # 尝试从 .env 文件读取
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == 'BINANCE_API_KEY':
                                api_key = value
                            elif key == 'BINANCE_API_SECRET':
                                api_secret = value
        except Exception as e:
            print(json.dumps({"warning": f"读取.env文件失败: {str(e)}"}, indent=2, ensure_ascii=False))
    
    # 如果 .env 中没有找到，尝试从环境变量读取
    if not api_key:
        api_key = os.environ.get("BINANCE_API_KEY")
    if not api_secret:
        api_secret = os.environ.get("BINANCE_API_SECRET")

    # 如果没有设置密钥，给出清晰提示
    if not api_key or not api_secret:
        print(json.dumps({
            "error": "API keys are missing.",
            "solution": "请在 .env 文件或系统环境变量中设置 BINANCE_API_KEY 和 BINANCE_API_SECRET",
            "env_file_path": env_file if os.path.exists(env_file) else "不存在"
        }, indent=2, ensure_ascii=False))
        return

    client = Client(api_key=api_key, api_secret=api_secret)

    target_stablecoins = ["USDT", "USDC", "FDUSD", "USD1", "TUSD", "DAI", "AEUR", "EUR"]
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_coin = {executor.submit(fetch_coin_data, client, coin): coin for coin in target_stablecoins}

        for future in concurrent.futures.as_completed(future_to_coin):
            data = future.result()
            if data and "error" not in data:
                results.append(data)

    results.sort(key=lambda x: x.get("base_apy_percent", 0), reverse=True)

    print(json.dumps({
        "module_name": "Stablecoin Simple Earn Radar (Pro Version)",
        "scan_results": results
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_stablecoin_earn_data()