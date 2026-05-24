import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import os
from zoneinfo import ZoneInfo
import glob # フォルダの中身を検索するライブラリ

# 1. 準備と設定
tickers = {
    "日経平均株価": "^N225",
    "S&P 500": "^GSPC",
    "ドル/円": "JPY=X"
}

# 日本時間とファイル名用の日付を取得
tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
today_str_csv = now.strftime("%Y/%m/%d")
date_filename = now.strftime("%Y-%m-%d") # 記事とグラフのファイル名（例：2026-05-24）
display_time = now.strftime("%Y年%m月%d日 %H:%M")

# 保存用のフォルダを準備（フォルダが無ければ自動作成）
os.makedirs("docs/articles", exist_ok=True) # 記事保存用
os.makedirs("docs/charts", exist_ok=True)   # グラフ保存用

# 2. 最新データを取得
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

# グラフに日付をつけて保存（例：chart_2026-05-24.png）
chart_filename = f"chart_{date_filename}.png"
plt.savefig(f"docs/charts/{chart_filename}")
plt.close()

# 5. 【新規】今日の「記事ページ」を作成する
article_content = f"""# {date_filename} のマーケット情報

**最終更新日時:** {display_time}

## 主要指標一覧
{markdown_table}

## 日経平均株価推移（過去1ヶ月）
![チャート画像](../charts/{chart_filename})
"""

# 今日の日付のファイルとして保存（例：docs/articles/2026-05-24.md）
article_filepath = f"docs/articles/{date_filename}.md"
with open(article_filepath, "w", encoding="utf-8") as f:
    f.write(article_content)

# 6. 【新規】トップページ（index.md）を再構築する（記事一覧の作成）
# articlesフォルダの中にある.mdファイルをすべて取得し、新しい順（降順）に並べ替える
article_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)

index_content = f"""# 最新マーケット情報ポータル

システムが毎日自動で情報を収集し、個別の記事として蓄積しています。

[📥 全期間の履歴データ(CSV)をダウンロード](history.csv)

## 📅 過去のマーケット記事一覧
"""

# 取得した記事ファイルのリストから、リンク集を自動で生成する
for file_path in article_files:
    # ファイル名だけを取り出す（"docs/articles/2026-05-24.md" -> "2026-05-24"）
    file_name = os.path.basename(file_path).replace(".md", "")
    # トップページからのリンク用URL
    link_path = f"articles/{file_name}/" 
    # 目次に追加
    index_content += f"- [{file_name} のマーケット情報]({link_path})\n"

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(index_content)

print(f"記事 {date_filename}.md の作成と、トップページの更新が完了しました！")