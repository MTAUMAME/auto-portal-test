import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
import glob
import feedparser
import requests
import google.generativeai as genai # Gemini用のライブラリ

# 1. 準備と設定
tickers = {
    "日経平均株価": "^N225",
    "S&P 500": "^GSPC",
    "ドル/円": "JPY=X"
}

tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
today_str_csv = now.strftime("%Y/%m/%d")
date_filename = now.strftime("%Y-%m-%d")
display_time = now.strftime("%Y年%m月%d日 %H:%M")

os.makedirs("docs/articles", exist_ok=True)
os.makedirs("docs/charts", exist_ok=True)

# 2. 最新の金融データを取得
data_dict = {}
display_data = []
for name, symbol in tickers.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        data_dict[name] = round(current_price, 2)
        display_data.append({"指標名": name, "現在値": f"{current_price:,.2f}"})

# 3. CSVへの自動蓄積
csv_file = "docs/history.csv"
new_row = {"日付": today_str_csv, **data_dict}
new_df = pd.DataFrame([new_row])
if os.path.exists(csv_file):
    history_df = pd.read_csv(csv_file)
    history_df = pd.concat([history_df, new_df], ignore_index=True)
else:
    history_df = new_df
history_df.to_csv(csv_file, index=False, encoding="utf-8-sig")

# 4. 表とグラフの作成
markdown_table = pd.DataFrame(display_data).to_markdown(index=False)
nikkei = yf.Ticker("^N225")
nikkei_hist = nikkei.history(period="1mo")
plt.figure(figsize=(10, 5))
plt.plot(nikkei_hist.index, nikkei_hist['Close'], marker='o', color='blue')
plt.title("Nikkei 225 (Past 1 Month)")
plt.grid(True)
plt.tight_layout()
chart_filename = f"chart_{date_filename}.png"
plt.savefig(f"docs/charts/{chart_filename}")
plt.close()

# 5. 気象庁から天気予報を取得する（徳島県）
weather_markdown = ""
try:
    weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/360000.json"
    weather_res = requests.get(weather_url).json()
    area_data = weather_res[0]['timeSeries'][0]['areas'][0]
    area_name = area_data['area']['name']
    today_weather = area_data['weathers'][0].replace(" ", " ")
    tomorrow_weather = area_data['weathers'][1].replace(" ", " ")
    weather_markdown = f"**{area_name}** | 今日: {today_weather} / 明日: {tomorrow_weather}"
except Exception as e:
    weather_markdown = "天気情報の取得に失敗しました。"

# 6. 【AI連携】ネットのトレンド（はてなブックマーク）を取得し、Geminiで記事生成
trend_log_file = "docs/trend_history.csv"
cutoff_date = (now - timedelta(days=14)).strftime("%Y-%m-%d")
recent_trends = []

# 過去14日以内に取り上げた話題のリストを作成
if os.path.exists(trend_log_file):
    with open(trend_log_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()[1:] 
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                date_str, word = parts[0], parts[1]
                if date_str >= cutoff_date:
                    recent_trends.append(word)

# はてなブックマークの総合トレンドRSS（ロボットでもブロックされません）
trend_rss_url = "https://b.hatena.ne.jp/hotentry/all.rss"
feed_trend = feedparser.parse(trend_rss_url)

target_trend = None
for entry in feed_trend.entries:
    trend_word = entry.title
    # 過去2週間に使っていない話題なら採用
    if trend_word not in recent_trends:
        target_trend = trend_word
        break

ai_generated_content = ""
if target_trend:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # AIへの命令文（プロンプト）
        prompt = f"現在日本のネット上で「{target_trend}」という話題がトレンド入りしています。この話題について、①どんな内容か（概要）、②なぜ注目されているのかの背景、③関連する事柄との比較やまとめ、をブログ読者向けに客観的で分かりやすく解説してください。Markdown形式で見出し（## や ###）を使ってきれいに装飾してください。"
        
        try:
            response = model.generate_content(prompt)
            ai_generated_content = response.text
            
            # 使用した話題を履歴ファイルに保存
            file_exists = os.path.exists(trend_log_file)
            with open(trend_log_file, "a", encoding="utf-8-sig") as f:
                if not file_exists:
                    f.write("日付,話題\n")
                f.write(f"{date_filename},{target_trend}\n")
        except Exception as e:
            ai_generated_content = f"AI記事の生成中にエラーが発生しました: {e}"
    else:
        ai_generated_content = "APIキーが設定されていないため、AIによるトレンド解説をスキップしました。"
else:
    ai_generated_content = "新しいトレンドが見つかりませんでした（直近2週間の話題を全て網羅済みです）。"

# 7. 今日の「記事ページ」を組み立てる
article_content = f"""# {date_filename} のトレンド＆マーケット情報

**最終更新日時:** {display_time}

## 🤖 AIトレンド解説：{target_trend if target_trend else "なし"}
{ai_generated_content}

---

## 🌤️ 今日の天気予報
{weather_markdown}

## 📊 マーケット指標一覧
{markdown_table}

## 📈 日経平均株価推移（過去1ヶ月）
![チャート画像](../charts/{chart_filename})
"""

article_filepath = f"docs/articles/{date_filename}.md"
with open(article_filepath, "w", encoding="utf-8") as f:
    f.write(article_content)

# 8. トップページ（index.md）を再構築する
article_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)
index_content = f"""# AI搭載・自動更新ダッシュボード

毎日自動でトレンドのAI解説、天気、金融データを収集して記事を生成しています。

[📥 全期間の株価履歴データ(CSV)をダウンロード](history.csv)

## 📅 最新の記事一覧
"""
for file_path in article_files:
    file_name = os.path.basename(file_path).replace(".md", "")
    link_path = f"articles/{file_name}/" 
    index_content += f"- [{file_name} のトレンド＆マーケット情報]({link_path})\n"

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(index_content)

print(f"記事 {date_filename}.md の作成（AIトレンド解説版）が完了しました！")