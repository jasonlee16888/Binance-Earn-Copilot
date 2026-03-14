import requests
import json
import re

def get_trending_assets():
    # 网络正常，直接使用币安主站官方接口
    url = "https://api.binance.com/api/v3/ticker/24hr"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        tickers = resp.json()

        valid_tickers = []
        for t in tickers:
            symbol = t['symbol']
            
            # 1. 基础门槛：必须是 USDT 交易对
            if not symbol.endswith('USDT'):
                continue
                
            # 2. 危险隔离：与模块A严格对齐，剔除所有稳定币和法币
            if re.match(r"^(USDC|FDUSD|TUSD|EUR|AEUR|DAI|USD1|USDP)", symbol):
                continue
                
            # 3. 危险隔离：剔除带有杠杆磨损属性的 UP/DOWN 衍生代币
            if symbol.endswith('UPUSDT') or symbol.endswith('DOWNUSDT') or symbol.endswith('BULLUSDT') or symbol.endswith('BEARUSDT'):
                continue
                
            valid_tickers.append(t)

        # 4. 寻找主线：按 24 小时成交量 (quoteVolume) 降序排列，取前五名
        valid_tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        top_5 = valid_tickers[:5]

        results = []
        for t in top_5:
            price_change = float(t['priceChangePercent'])
            asset_name = t['symbol'].replace('USDT', '')
            
            # 5. 动态研判：为 Agent 提供情绪标签
            if price_change > 15:
                signal = "强势拉升 (Uptrend) - 市场情绪高涨，定投建议缩小单次买入份额"
            elif price_change < -10:
                signal = "深度回调 (Deep Pullback) - 绝佳的定投吸筹窗口，可适当加码"
            else:
                signal = "高流动性震荡 (Consolidation) - 资金博弈激烈，适合平摊建仓"

            results.append({
                "asset": asset_name,
                "current_price": float(t['lastPrice']),
                "price_change_24h": f"{price_change}%",
                "narrative_signal": signal
            })

        # 6. 打包输出 JSON 给大模型
        print(json.dumps({
            "module_name": "Auto-Invest Narrative Radar",
            "selection_logic": "全网资金共识筛选，已静默拦截稳定币与高危衍生品",
            "recommended_portfolio": results
        }, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": f"Data process error: {str(e)}"}))

if __name__ == "__main__":
    get_trending_assets()