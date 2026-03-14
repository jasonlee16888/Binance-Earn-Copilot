import os
import json
import sys
import re
from binance.client import Client

def normalize_strike_price(price):
    """智能取整算法：根据币价规模自动对齐币安标准的行权价刻度"""
    if price >= 10000:
        return round(price / 500) * 500   # BTC 级别，按 500 取整
    elif price >= 1000:
        return round(price / 50) * 50     # ETH 级别，按 50 取整
    elif price >= 100:
        return round(price / 5) * 5       # SOL/BNB 级别，按 5 取整
    elif price >= 10:
        return round(price)               # DOT/LINK 级别，按 1 取整
    else:
        return round(price, 2)            # 小币种保留两位小数

def get_safe_dual_invest_targets(asset):
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

    if not api_key or not api_secret:
        print(json.dumps({
            "error": "API keys are missing.",
            "solution": "请在 .env 文件或系统环境变量中设置 BINANCE_API_KEY 和 BINANCE_API_SECRET",
            "env_file_path": env_file if os.path.exists(env_file) else "不存在"
        }, indent=2, ensure_ascii=False))
        return

    client = Client(api_key=api_key, api_secret=api_secret)

    try:
        asset = asset.strip().upper()
        if not re.match(r"^[A-Z0-9]+$", asset):
            print(json.dumps({"error": f"Invalid asset symbol: {asset}"}))
            return

        symbol = f"{asset}USDT"

        # 获取当前价格和24小时变化
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker["price"])
        ticker_24hr = client.get_ticker(symbol=symbol)
        price_change_percent = float(ticker_24hr["priceChangePercent"])

        # 生成不同防守级别的标准化行权价矩阵
        def calc_safe_tier(margin_pct):
            raw_price = current_price * (1 + margin_pct)
            return normalize_strike_price(raw_price)

        matrix = {
            "aggressive_10_pct": calc_safe_tier(0.10),
            "balanced_15_pct": calc_safe_tier(0.15),
            "conservative_20_pct": calc_safe_tier(0.20)
        }

        output = {
            "module_name": "Dual Investment Multi-Tier Radar",
            "target_asset": asset,
            "market_context": {
                "current_price": current_price,
                "24h_price_change_percent": price_change_percent,
                "volatility_warning": "HIGH" if abs(price_change_percent) > 8 else "NORMAL"
            },
            "strategy": "Sell High (高位卖出) - 防卖飞模式",
            "strike_price_matrix": matrix,
            "agent_instruction": "请根据 market_context 中的 24h 涨跌幅与波动率警告，选择 strike_price_matrix 中最合适的一档。如果波动率 HIGH，必须选择 conservative_20_pct 档位。"
        }

        print(json.dumps(output, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    target_asset = "BTC"
    # 安全的参数解析
    for arg in sys.argv[1:]:
        if re.match(r"^[A-Za-z0-9]+$", arg):
            target_asset = arg
            break

    get_safe_dual_invest_targets(target_asset)