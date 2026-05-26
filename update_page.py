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
    
    prompt = f"""
あなたは月間100万PVを誇る、ガジェットおよび最新AIテクノロジー専門のトップブロガー兼アフィリエイターです。
現在トレンドとなっているテーマ「{target_trend}」について、読者が「この記事を読んで商品を買いたい・サービスを使いたい」と思えるような、圧倒的に質が高く、オリジナリティ溢れる比較・まとめ記事を作成してください。

以下の【厳守ルール】と【記事構成】に従い、Markdown形式で出力してください。

【厳守ルール】
1. 情報の統合とリアルな評価
   - Google、Yahoo、X（旧Twitter）、Instagram等のSNSで語られている最新の空気感を分析し、反映させること。
   - レビューや口コミを紹介する際は「人間味」を重視すること。ただし、サクラやBotによる不自然な高評価（短すぎる「最高です」「星5つ」や、同じ文言の繰り返し）は完全に除外・無視し、具体的なメリット・デメリットが書かれたリアルな声のみを抽出・要約して記載すること。

2. 比較の明瞭化
   - 読者が最も知りたい「価格帯」「主要スペック（性能）」「他社製品・従来技術との違い」を目に見えて分かりやすい形で比較すること（箇条書きやMarkdownの表組みを推奨）。

3. 統一されたトーン＆マナー
   - ブログの読者に語りかけるような、親しみやすくも説得力のある「丁寧なブログ口調（です・ます調）」で統一すること。日本語の不自然な直訳表現や、AI特有の堅苦しい表現は排除すること。

4. アフィリエイトの王道テクニック（収益化への導線）
   - 「読者の悩みの代弁」→「解決策の提示」→「具体的な比較と証拠（口コミ）」→「行動の提案」という、成約率が高いアフィリエイト記事の王道フロー（PASONAの法則など）に沿って展開すること。
   - 記事の最後には、読者が次に取るべきアクション（商品の購入検討、公式サイトでの詳細確認、アカウント登録など）へ自然に誘導する一文を入れること。

【記事構成テンプレート】
# 【最新比較】{target_trend}の真実：口コミから見えた性能とコスパ

## 1. いま「{target_trend}」が爆発的に話題になっている理由
（SNSやネットニュースでなぜ今トレンドなのか、読者のどんな悩みを解決するのかを共感ベースで解説）

## 2. 徹底比較！価格とスペックの本当のところ
（競合製品や従来技術との違いを、価格・性能の面からシビアに比較・解説。表組み推奨）

## 3. リアルな口コミ・レビュー（サクラ厳禁）
（SNS等での実際のユーザーの「良い声」と「悪い声」を忖度なく紹介し、人間味のある分析を加える）

## 4. 【結論】ズバリ、どんな人におすすめか？
（これまでの比較と口コミを踏まえ、最終的にどういう人が買うべきか、あるいは見送るべきかを断言する）

## 5. 次のステップ（行動の提案）
（アフィリエイトリンクへの誘導を見据えた、読者の背中を押すクロージング文章）
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