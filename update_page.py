import pandas as pd
import yfinance as yf
from datetime import datetime

# 1. 取得したい銘柄のシンボル（日経平均、S&P500、ドル円）
tickers = {
    "日経平均株価": "^N225",
    "S&P 500": "^GSPC",
    "ドル/円": "JPY=X"
}

# 2. Yahoo Financeから最新データを取得してリストにまとめる
data = []
for name, symbol in tickers.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d") # 最新1日分のデータを取得
    
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        data.append({
            "指標名": name,
            "シンボル": symbol,
            "現在値": f"{current_price:,.2f}"
        })

df = pd.DataFrame(data)

# 3. データをMarkdown形式の表に変換
markdown_table = df.to_markdown(index=False)

# 4. 現在の時刻を取得
now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

# 5. ページ全体の内容を組み立てる
page_content = f"""# 最新マーケット情報ポータル

このページはPythonプログラムによって自動生成されています。
**最終更新日時:** {now}

## 主要指標一覧

{markdown_table}
"""

# 6. docs/index.md に上書き保存する
with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(page_content)

print("Webサイトを最新のマーケットデータで更新しました！")