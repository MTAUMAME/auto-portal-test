import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
from zoneinfo import ZoneInfo

# 1. 取得したい銘柄のシンボル
tickers = {
    "日経平均株価": "^N225",
    "S&P 500": "^GSPC",
    "ドル/円": "JPY=X"
}

# 2. 最新データを取得してリストにまとめる
data = []
for name, symbol in tickers.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        data.append({
            "指標名": name,
            "シンボル": symbol,
            "現在値": f"{current_price:,.2f}"
        })

df = pd.DataFrame(data)
markdown_table = df.to_markdown(index=False)

# 3. 【新規】日経平均株価の過去1ヶ月のデータを取得してグラフ化する
nikkei = yf.Ticker("^N225")
nikkei_hist = nikkei.history(period="1mo") # 過去1ヶ月分

# グラフの見た目を設定（※クラウド上での文字化けを防ぐため、英語表記にしています）
plt.figure(figsize=(10, 5))
plt.plot(nikkei_hist.index, nikkei_hist['Close'], marker='o', color='blue')
plt.title("Nikkei 225 (Past 1 Month)")
plt.xlabel("Date")
plt.ylabel("Closing Price")
plt.grid(True)
plt.tight_layout()

# グラフを「chart.png」という名前の画像としてdocsフォルダ内に保存
plt.savefig("docs/chart.png")
plt.close()

# 4. 現在の時刻を取得
now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y年%m月%d日 %H:%M")

# 5. ページ全体の内容を組み立てる（画像の表示指定を追加）
page_content = f"""# 最新マーケット情報ポータル

このページはPythonプログラムによって自動生成されています。
**最終更新日時:** {now}

## 主要指標一覧

{markdown_table}

## 日経平均株価推移（過去1ヶ月）
![チャート画像](chart.png)
"""

# 6. docs/index.md に上書き保存する
with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(page_content)

print("Webサイトを更新し、チャート画像を生成しました！")