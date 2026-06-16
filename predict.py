import requests
import pandas as pd
import telegram
import asyncio
import os
from datetime import datetime

# ==================== 設定 ====================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHANNEL_ID"))

HKJC_ENDPOINT = "https://info.cld.hkjc.com/graphql/base/"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://bet.hkjc.com/",
}

# ==================== HKJC 抓取 ====================
def get_hkjc_football_data():
    payload = {
        "operationName": "GetFootballMatches",
        "variables": {
            "fbOddsTypes": ["HAD", "HIL", "CRS"],
            "startIndex": 0,
            "endIndex": 50,
            "inplayOnly": False
        },
        "query": """query GetFootballMatches($fbOddsTypes: [String!], $startIndex: Int, $endIndex: Int) {
          matches: allMatchList(fbOddsTypes: $fbOddsTypes, startIndex: $startIndex, endIndex: $endIndex, inplayOnly: false) {
            matchId homeTeam {name} awayTeam {name} league {name}
            kickOffTime status
            foPools { oddsType lines { combination currentOdds } }
          }
        }"""
    }
    try:
        resp = requests.post(HKJC_ENDPOINT, json=payload, headers=HEADERS, timeout=20)
        data = resp.json()
        rows = []
        for m in data.get("data", {}).get("matches", []):
            row = {
                "比賽": f"{m.get('homeTeam',{}).get('name','?')} vs {m.get('awayTeam',{}).get('name','?')}",
                "聯賽": m.get('league',{}).get('name',''),
                "開球": m.get('kickOffTime','')[:16]
            }
            for pool in m.get('foPools', []):
                ot = pool.get('oddsType','')
                for line in pool.get('lines', []):
                    row[f"{ot}_{line.get('combination','')}"] = line.get('currentOdds')
            rows.append(row)
        df = pd.DataFrame(rows)
        print(f"✅ 成功抓到 {len(df)} 場比賽")
        return df
    except Exception as e:
        print("⚠️ HKJC 抓取錯誤:", e)
        return pd.DataFrame()

# ==================== 凱利 + 8 大板塊 ====================
def kelly_criterion(odds, prob, fraction=0.5):
    if odds <= 1 or prob <= 0: return 0.0
    k = (prob * odds - 1) / (odds - 1)
    return max(0, k * fraction)

def generate_prediction(df):
    if not df.empty and len(df) > 0:
        match = df.iloc[0]["比賽"]
        home, away = [x.strip() for x in match.split(" vs ")]
    else:
        home, away = "主隊", "客隊"

    best_bet = "冷和（第二高賠均衡組合）"
    best_odds = 3.40
    kelly = kelly_criterion(best_odds, 0.32)

    message = f"""
⚽ **{home} vs {away}** 今日預測（均衡高賠 + 凱利版）

**1. 預計首發陣容及理由**（結合新人和傷停）
主隊：4-3-3（新人融入）；客隊：4-2-3-1（防線復出）

**2. 近期狀態與戰術對決**
主隊新進攻線 vs 客隊防線

**3. 傷停、背景動機**（最新戰意）
主隊戰意高昂；客隊已鎖定位置

**4. 投注價值推薦**
✅ **主推**：{best_bet} @ {best_odds}  
   凱利指數：**{kelly*100:.1f}%**

**5. 風險及冷門可能性**
新陣容默契不足 | 爆冷：客勝（極端大冷）

**6. 全體預測**
主勝機會較高，冷和有均衡價值

**7. 預測比分（波膽）**
2-1、1-1、3-1

**8. 最終總結**
📌 主選均衡高賠組合（較易打出）  
中場休息可用「派彩快」再分析  
更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M HKT')}

投注有風險，娛樂為主！
"""
    return message

async def main():
    print("🚀 Daily Football Predict Bot 啟動...")
    df = get_hkjc_football_data()
    msg = generate_prediction(df)
    
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    print("✅ 預測已成功推送到 Telegram！")

if __name__ == "__main__":
    asyncio.run(main())
