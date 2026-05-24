import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import os # ファイルの存在確認に使うライブラリを追加
from zoneinfo import ZoneInfo

# 1. 取得したい銘柄のシンボル
tickers = {
    "日経平均株価": "^N225",
    "S&P 500": "^GSPC",
    "ドル/円": "JPY=X"
}

data_dict = {}
today_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d")

# 2. 最新データを取得
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

# --- 【新規】毎日のデータをCSVファイルに自動蓄積する処理 ---
csv_file = "docs/history.csv"
new_row = {"日付": today_str, **data_dict}
new_df = pd.DataFrame([new_row])

if os.path.exists(csv_file):
    # 既にファイルがあれば、過去のデータを読み込んで今日のデータを追加
    history_df = pd.read_csv(csv_file)
    history_df = pd.concat([history_df, new_df], ignore_index=True)
else:
    # 初回は新規作成
    history_df = new_df

# エクセルで文字化けしないように utf-8-sig で保存
history_df.to_csv(csv_file, index=False, encoding="utf-8-sig")
# --------------------------------------------------------

# 表とグラフの作成
markdown_table = pd.DataFrame(display_data).to_markdown(index=False)

nikkei = yf.Ticker("^N225")
nikkei_hist = nikkei.history(period="1mo")

plt.figure(figsize=(10, 5))
plt.plot(nikkei_hist.index, nikkei_hist['Close'], marker='o', color='blue')
plt.title("Nikkei 225 (Past 1 Month)")
plt.grid(True)
plt.tight_layout()
plt.savefig("docs/chart.png")
plt.close()

now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y年%m月%d日 %H:%M")

# ページ全体の内容を組み立て（ダウンロードリンクを追加）
page_content = f"""# 最新マーケット情報ポータル

このページはPythonプログラムによって自動生成されています。
**最終更新日時:** {now}

## 主要指標一覧

{markdown_table}

## 日経平均株価推移（過去1ヶ月）
![チャート画像](chart.png)

## 過去データのダウンロード
システムが毎日自動記録しているデータベースは以下からダウンロードできます。
[📥 履歴データ(CSV)をダウンロード](history.csv)
"""

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(page_content)

print("データの蓄積とサイトの更新が完了しました！")