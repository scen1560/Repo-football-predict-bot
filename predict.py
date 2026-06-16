import requests
import json
import os

# =====================================================================
# 1. 自動讀取 GitHub Secrets 保險箱密鑰
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# =====================================================================
# 2. 智能雷達：抓取真實賽事與多間莊家數據（用作計算凱利指數）
# =====================================================================
def get_international_odds():
    print("🔄 正在啟動智能雷達，搜尋今日真實賽事及莊家賠率...")
    
    if not ODDS_API_KEY:
        print("❌ 錯誤：找不到 ODDS_API_KEY！請檢查 GitHub 保險箱設定。")
        return None

    # 📡 2026年6月焦點：世界盃分組賽黃金期，優先鎖定世界盃
    SPORTS_TO_TRY = [
        'soccer_fifa_world_cup',       # 2026 世界盃
        'soccer_conmebol_copa_america',# 美洲盃
        'soccer_usa_mls',              # 美職聯
        'soccer_japan_j_league'        # 日職聯
    ]
    
    for sport in SPORTS_TO_TRY:
        print(f"🔍 正在尋找聯賽：{sport} ...")
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",          # 抓取歐洲主流大莊家數據
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                match_list = response.json()
                if match_list and len(match_list) > 0:
                    match = match_list[0]
                    home_team = match.get("home_team", "主隊")
                    away_team = match.get("away_team", "客隊")
                    start_time = match.get("commence_time", "即將開賽")
                    
                    # 搜集前幾間主流莊家數據以供 AI 計算凱利指數
                    bookmakers_data = []
                    for bk in match.get('bookmakers', [])[:3]: # 取前3間大莊家
                        bk_title = bk.get('title')
                        outcomes = bk['markets'][0]['outcomes']
                        h_p, d_p, a_p = 0.0, 0.0, 0.0
                        for o in outcomes:
                            if o['name'] == home_team: h_p = o['price']
                            elif o['name'] == away_team: a_p = o['price']
                            elif o['name'] == 'Draw': d_p = o['price']
                        bookmakers_data.append({
                            "name": bk_title, "h": h_p, "d": d_p, "a": a_p
                        })

                    if len(bookmakers_data) > 0:
                        print(f"🎯 成功鎖定真實賽事：{home_team} vs {away_team}")
                        return {
                            "match_name": f"{home_team} vs {away_team}",
                            "match_time": start_time,
                            "main_odds": bookmakers_data[0], # 以第一間為主賠率
                            "all_bookmakers": bookmakers_data
                        }
        except Exception as e:
            print(f"⚠️ 嘗試 {sport} 時發生錯誤：{e}")
            continue 

    print("ℹ️ 今日雷達名單內的所有聯賽均無即將開賽的數據。")
    return None

# =====================================================================
# 3. 呼叫 最新 Gemini 3.5 Flash 大腦 (固定短網址版，融入凱利指數與次選高賠策略)
# =====================================================================
def generate_report_with_gemini(match_info):
    if not match_info:
        return None
        
    print("🧠 正在啟動 Gemini 3.5 Flash 大腦進行【凱利指數】與【均衡高賠】深度分析...")
    
    if not GEMINI_API_KEY:
        print("❌ 錯誤：找不到 GEMINI_API_KEY！")
        return None

    # 🛠️ 終極防錯：網址保持絕對固定同超短，完全不放變數，金鑰改放在 params 參數傳送
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    query_params = {"key": GEMINI_API_KEY}
    headers = {"Content-Type": "application/json"}
    
    main_bk = match_info['main_odds']
    bk_json = json.dumps(match_info['all_bookmakers'], ensure_ascii=False)

    prompt = f"""你現在是一位精通香港馬會波經、擅長利用大數據精算「凱利指數（Kelly Index）」的頂級足球衍生品分析師。
請根據以下提供的多間國際莊家即時賠率，為今日賽事進行深度推演。

【真實賽事資料】：
球賽：{match_info['match_name']}
開賽時間：{match_info['match_time']}
主流莊家賠率 ({main_bk['name']})：主勝 {main_bk['h']} | 和局 {main_bk['d']} | 客勝 {main_bk['a']}

【多間莊家對比數據（用作計算凱利指數）】：
{bk_json}

⚠️ 【核心策略指令】：
1. 必須在分析中展現「凱利指數分析」，對比各莊家賠率與市場平均勝率，指出哪一個選項（主/平/客）的凱利指數異常偏低，代表莊家在低調控賠，具備防範風險價值。
2. 精準鎖定【次選均衡高賠組合】：如果不想觸碰極端大冷，請在「和局（冷平）」或「受讓客勝（冷客）」中，找出冷門程度適中、市場拉力均衡、相對更容易打出的第二高賠選項，並將其列為重點推薦！
3. 如果球隊名是英文，請在分析時自動將其翻譯為香港球迷最熟悉的中文譯名（例如：Netherlands -> 荷蘭，Japan -> 日本）。
4. 必須嚴格按照以下「8大板塊」的順序輸出，每板塊加上清晰的 Emoji 標題，文字精煉吸睛，適合 Telegram 閱讀：

1. 預計首發陣容及戰術對決
2. 傷停情況與即時戰意背景
3. 📊 莊家凱利指數深度解密（對比多間莊家，點出控賠方向）
4. 💎 次選均衡高賠組合推薦（精選冷門程度適中、最易打出的第二高賠平/客選項）
5. 風險與極端大冷防範
6. 全體預測
7. 預測比分（波膽推薦）
8. 最終總結（加入溫馨提示：若半場形勢有暗湧，用家可自行決定使用馬會「派彩快」提早走印鎖定利潤）
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(url, headers=headers, params=query_params, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"❌ Gemini API 錯誤：{response.text}")
    except Exception as e:
        print(f"❌ 呼叫 Gemini 發生錯誤：{e}")
    return None

# =====================================================================
# 4. 外賣仔出 Post
# =====================================================================
def send_to_telegram(text):
    if not text:
        return
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ 錯誤：找不到 BOT_TOKEN 或 CHANNEL_ID，停止發送。")
        return
        
    print("🚀 正在將包含凱利指數的最新預測發送到 Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # 支援數值型（如 -100xxx）或字串型（如 @xxx）的 CHANNEL_ID
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("🎉【凱利次選高賠全自動完成！】預測已成功出 Post！")
        else:
            print(f"❌ Telegram 發送失敗：{res.text}")
    except Exception as e:
        print(f"❌ Telegram 連線失敗：{e}")

# =====================================================================
# 5. 主程式執行
# =====================================================================
if __name__ == "__main__":
    data = get_international_odds()
    if data:
        report = generate_report_with_gemini(data)
        send_to_telegram(report)
    else:
        print("⏸️ 今日雷達找不到真實賽事。為保證準確，今日提早收工不出 Post。")
