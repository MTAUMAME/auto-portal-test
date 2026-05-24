import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import os
from zoneinfo import ZoneInfo
import glob
import feedparser # 【新規】RSS（ニュース）を読み取るライブラリ

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
        display_data.append({
            "指標名": name,
            "現在値": f"{current_price:,.2f}"
        })

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

# 5. 【新規】Yahoo!ニュース（主要トピックス）を取得する
rss_url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
feed = feedparser.parse(rss_url)

# ニュースを箇条書きのリンクとしてまとめる
news_markdown = ""
for entry in feed.entries[:5]: # 上位5件だけを取得
    news_markdown += f"- [{entry.title}]({entry.link})\n"

# 6. 今日の「記事ページ」を作成する（ニュースを追加）
article_content = f"""# {date_filename} のマーケット＆ニュース情報

**最終更新日時:** {display_time}

## 📰 今日の主要ニュース（Yahoo!ニュース）
{news_markdown}

## 📊 主要指標一覧
{markdown_table}

## 📈 日経平均株価推移（過去1ヶ月）
![チャート画像](../charts/{chart_filename})
"""

article_filepath = f"docs/articles/{date_filename}.md"
with open(article_filepath, "w", encoding="utf-8") as f:
    f.write(article_content)

# 7. トップページ（index.md）を再構築する
article_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)

index_content = f"""# 最新ポータル情報まとめ

システムが毎日自動で金融データとニュースを収集し、蓄積しています。

[📥 全期間の株価履歴データ(CSV)をダウンロード](history.csv)

## 📅 過去の自動生成記事一覧
"""

for file_path in article_files:
    file_name = os.path.basename(file_path).replace(".md", "")
    link_path = f"articles/{file_name}/" 
    index_content += f"- [{file_name} のマーケット＆ニュース情報]({link_path})\n"

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(index_content)

print(f"記事 {date_filename}.md の作成（ニュース追加版）が完了しました！")