import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
import glob
import feedparser
import requests
import google.generativeai as genai

# 1. 準備と設定
tickers = {"日経平均株価": "^N225", "S&P 500": "^GSPC", "ドル/円": "JPY=X"}
tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
date_filename = now.strftime("%Y-%m-%d")
display_time = now.strftime("%Y年%m月%d日 %H:%M")

os.makedirs("docs/articles", exist_ok=True)
os.makedirs("docs/charts", exist_ok=True)

# 2. 金融データ取得
display_data = []
for name, symbol in tickers.items():
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        display_data.append({"指標名": name, "現在値": f"{current_price:,.2f}"})

# 3. グラフ作成（色調をデザインに合わせる）
plt.style.use('ggplot')
nikkei = yf.Ticker("^N225")
nikkei_hist = nikkei.history(period="1mo")
plt.figure(figsize=(10, 4))
plt.plot(nikkei_hist.index, nikkei_hist['Close'], color='#455a64', linewidth=2)
plt.title("Nikkei 225 Market Trend", fontsize=14)
plt.fill_between(nikkei_hist.index, nikkei_hist['Close'], color='#455a64', alpha=0.1)
plt.tight_layout()
chart_filename = f"chart_{date_filename}.png"
plt.savefig(f"docs/charts/{chart_filename}")
plt.close()

# 4. トレンド取得（はてなブックマーク）
trend_rss_url = "https://b.hatena.ne.jp/hotentry/all.rss"
feed_trend = feedparser.parse(trend_rss_url)
target_trend = feed_trend.entries[0].title if feed_trend.entries else "マーケットの変動"

# 5. 【AI大改造】独自視点のコラム生成ロジック
api_key = os.environ.get("GEMINI_API_KEY")
ai_generated_content = ""

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    # オリジナリティを出すための「思考フレームワーク」を与えたプロンプト
    prompt = f"""
    あなたは凄腕の資産運用コンサルタント兼トレンドアナリストです。
    話題のテーマ「{target_trend}」について、以下の制約を守り、読者に利益をもたらす独自の分析記事を書いてください。

    【絶対制約】
    1. 他サイトの文章のコピーや、特定のニュースサイト名（Yahoo!など）を出さないこと。
    2. 一般論ではなく「この話題が私たちの生活や家計にどう影響するか」という独自の切り口で書くこと。
    3. 似たような概念や過去の事例との「比較」を必ず含めること。
    4. 最後に、この情報を踏まえて読者が「次に取るべき具体的なアクション（例：新NISAの検討、特定ジャンルの学習など）」を提案すること。

    【構成案】
    ## 独自の視点：{target_trend}から読み解く未来
    ### 1. この話題の本質的な価値
    ### 2. 知っておくべき類似事例との決定的な違い
    ### 3. 私たちのライフ戦略への影響と対策
    ### 4. 賢い選択：今すぐ検討すべき次のステップ
    
    Markdown形式で、読みやすくプロフェッショナルな口調（だ・である調）で出力してください。
    """
    
    try:
        response = model.generate_content(prompt)
        ai_generated_content = response.text
    except Exception as e:
        ai_generated_content = f"分析記事の生成に失敗しました。: {e}"

# 6. 記事の組み立て
markdown_table = pd.DataFrame(display_data).to_markdown(index=False)
article_content = f"""
# {date_filename} 特別レポート：マーケットと社会の潮流

![Market Chart](../charts/{chart_filename})

---

{ai_generated_content}

---

## 📊 本日の主要マーケット指標
{markdown_table}

---
*免責事項：本記事はAIによる自動生成コンテンツであり、特定の投資を勧誘するものではありません。最終的な判断はご自身で行ってください。*
"""

with open(f"docs/articles/{date_filename}.md", "w", encoding="utf-8") as f:
    f.write(article_content)

# 7. インデックス（目次）の更新
article_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)
index_content = "# Premium Asset Media\n\nAIがマーケットの深層を読み解き、あなたの資産形成をサポートする情報を毎日配信します。\n\n## 📋 最新の特別レポート\n\n"
for file_path in article_files:
    fname = os.path.basename(file_path).replace(".md", "")
    index_content += f"*   [{fname} ： 戦略的マーケットレポート](articles/{fname}/)\n"

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(index_content)