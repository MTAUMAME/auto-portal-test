import os
import glob
import time
import re
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import feedparser
import google.generativeai as genai

# 1. 準備と設定
tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
date_filename = now.strftime("%Y-%m-%d")
display_time = now.strftime("%Y年%m月%d日 %H:%M")

os.makedirs("docs/articles", exist_ok=True)
trend_log_file = "docs/trend_history.csv"
cutoff_date = (now - timedelta(days=14)).strftime("%Y-%m-%d")

# 過去14日間のトレンド履歴を読み込む
recent_trends = []
if os.path.exists(trend_log_file):
    with open(trend_log_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] >= cutoff_date:
                recent_trends.append(parts[1])

# 2. 【修正】IT・テクノロジー・ガジェット特化のトレンドを取得
trend_rss_url = "https://b.hatena.ne.jp/hotentry/it.rss"
feed_trend = feedparser.parse(trend_rss_url)

# まだ記事にしていない最新トレンドを「最大10個」リストアップ
target_trends = []
for entry in feed_trend.entries:
    if entry.title not in recent_trends:
        target_trends.append(entry.title)
    if len(target_trends) >= 10:
        break

# 3. AIによる記事の連続生成
api_key = os.environ.get("GEMINI_API_KEY")
generated_files = []

if api_key and target_trends:
    genai.configure(api_key=api_key)
    # 最新のFlashモデルを正しく指定
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    for trend in target_trends:
        print(f"「{trend}」の記事を生成中...")
        
        # サクラを除外し、比較とアフィリエイト導線を意識した最強プロンプト
        prompt = f"""
        あなたはガジェットおよび最新AIテクノロジー専門のトップアフィリエイターです。
        トレンドテーマ「{trend}」について、読者が商品やサービスを導入したくなるような比較・まとめ記事を書いてください。

        【厳守ルール】
        1. Google、X、Instagram等のリアルな声を統合すること。ただし、サクラやBotによる不自然な高評価（短すぎる「最高です」「星5つ」や同じ文言の繰り返し）は完全に無視し、具体的なメリット・デメリットが書かれたリアルな声のみを採用すること。
        2. 読者が知りたい「価格」「性能」「他との違い」を目に見えて分かりやすい形で比較すること（表組み推奨）。
        3. ブログとして自然な「です・ます調」で統一し、不自然な直訳やAI特有の堅苦しい表現は排除すること。
        4. 最後に、読者が次に取るべきアクション（購入や登録など）を促す一文を入れること。

        【構成】
        # {trend}の最新まとめ＆徹底比較
        ## 1. なぜ今話題になっているのか？
        ## 2. 価格と性能の徹底比較
        ## 3. リアルな口コミ・レビュー（サクラ厳禁）
        ## 4. 【結論】ズバリ、どんな人におすすめか？
        ## 5. 次のステップへ
        """
        
        try:
            response = model.generate_content(prompt)
            article_body = response.text
            
            # ファイル名に使えない記号を削除して安全な名前を作成
            safe_title = re.sub(r'[\\/*?:"<>|]', "", trend)[:30]
            filename = f"{date_filename}_{safe_title}"
            filepath = f"docs/articles/{filename}.md"
            
            # 個別記事ファイルの作成
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"**最終更新日時:** {display_time}\n\n{article_body}")
            
            generated_files.append({"title": trend, "filename": filename})
            
            # 履歴に保存
            file_exists = os.path.exists(trend_log_file)
            with open(trend_log_file, "a", encoding="utf-8-sig") as f:
                if not file_exists:
                    f.write("日付,話題\n")
                f.write(f"{date_filename},{trend}\n")
                
            # APIの制限（無料枠）に引っかからないよう4秒待機
            time.sleep(4)
            
        except Exception as e:
            print(f"エラー発生 ({trend}): {e}")

# 4. トップページ（目次）の再構築
article_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)
index_content = """# 最新ガジェット＆AI 比較ポータル

毎日自動で最新テクノロジーのトレンドを収集し、リアルな口コミをもとに徹底比較しています。
気になる記事をクリックして詳細を確認してください。

## 📅 最新の記事一覧（アーカイブ）
"""

for file_path in article_files:
    fname = os.path.basename(file_path).replace(".md", "")
    # ファイル名から日付とタイトルを抽出して綺麗に表示
    display_title = fname.split("_", 1)[-1] if "_" in fname else fname
    date_part = fname.split("_", 1)[0] if "_" in fname else ""
    
    index_content += f"* [{date_part}： {display_title}](articles/{urllib.parse.quote(fname)}/)\n"

with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(index_content)

print("すべての記事生成とトップページの更新が完了しました！")