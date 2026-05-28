import os
import glob
import time
import re
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
import feedparser
import google.generativeai as genai

# 1. 準備と設定
tz = ZoneInfo("Asia/Tokyo")
now = datetime.now(tz)
date_filename = now.strftime("%Y-%m-%d")
display_time = now.strftime("%Y年%m月%d日 %H:%M")

os.makedirs("docs/articles", exist_ok=True)
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("APIキーが設定されていません。")
    exit()

genai.configure(api_key=api_key)

# --------------------------------------------------
# 【第一部】IT・ガジェット系記事の取得（Gemini 3.5 Flash）
# --------------------------------------------------
print("=== IT・ガジェット系記事の処理を開始 ===")
feed_it = feedparser.parse("https://b.hatena.ne.jp/hotentry/it.rss")
model_it = genai.GenerativeModel('gemini-3.5-flash')

it_count = 0
for entry in feed_it.entries:
    if it_count >= 10: # ITは10件まで
        break
        
    safe_title = re.sub(r'[\\/*?:"<>|]', "", entry.title)[:30]
    filepath_it = f"docs/articles/IT_{date_filename}_{safe_title}.md"
    
    # ガード機能：既存記事はスキップ（以前のプレフィックスなしファイルも考慮）
    legacy_filepath = f"docs/articles/{date_filename}_{safe_title}.md"
    if os.path.exists(filepath_it) or os.path.exists(legacy_filepath):
        continue
        
    print(f"[IT] 「{entry.title}」を生成中...")
    prompt_it = f"ガジェット・最新AI専門ブログとして「{entry.title}」についてまとめ、価格や性能を比較し、サクラレビューを弾いた口コミを含め、アフィリエイトに繋がる提案をMarkdownで作成してください。"
    
    try:
        response = model_it.generate_content(prompt_it)
        if response.text and len(response.text.strip()) > 100:
            with open(filepath_it, "w", encoding="utf-8") as f:
                f.write(f"**最終更新日時:** {display_time}\n\n{response.text}")
            it_count += 1
            time.sleep(3)
    except Exception as e:
        print(f"[IT] エラー発生（API制限の可能性）: {e}")
        print("IT系の処理を中断し、金融系の処理へ移行します。")
        break # 3.5 Flashの上限に達した場合はITのみ中断して次へ進む

# --------------------------------------------------
# 【第二部】金融・投資系記事の取得（Gemini 3.1 Flash Lite）
# --------------------------------------------------
print("=== 金融・投資系記事の処理を開始 ===")
feed_finance = feedparser.parse("https://b.hatena.ne.jp/hotentry/economics.rss")
model_finance = genai.GenerativeModel('gemini-3.1-flash-lite')

finance_count = 0
for entry in feed_finance.entries:
    if finance_count >= 20: # 金融は20件程度まで
        break
        
    safe_title = re.sub(r'[\\/*?:"<>|]', "", entry.title)[:30]
    # 金融記事には「Finance_」という目印をつける
    filepath_finance = f"docs/articles/Finance_{date_filename}_{safe_title}.md"
    
    # ガード機能：既存記事はスキップ
    if os.path.exists(filepath_finance):
        continue
        
    print(f"[金融] 「{entry.title}」を生成中...")
    prompt_finance = f"""
    金融・資産運用・新NISA専門のアフィリエイターとして「{entry.title}」のトレンドを分析してください。
    【厳守】
    1. 自己検証を行い最新情報を記載。
    2. サクラを弾いたリアルな口コミを記載。
    3. 手数料や利回りの比較表を作成。
    4. 投資初心者向けの丁寧な口調。
    5. 最後に証券口座開設など次のアクションを促す。
    Markdown形式で出力してください。
    """
    
    try:
        response = model_finance.generate_content(prompt_finance)
        if response.text and len(response.text.strip()) > 100:
            with open(filepath_finance, "w", encoding="utf-8") as f:
                f.write(f"**最終更新日時:** {display_time}\n\n{response.text}")
            finance_count += 1
            time.sleep(3)
    except Exception as e:
        print(f"[金融] エラー発生: {e}")

# --------------------------------------------------
# 【第三部】2つの独立したトップページ（目次）の作成
# --------------------------------------------------
all_files = sorted(glob.glob("docs/articles/*.md"), reverse=True)
it_links = ""
finance_links = ""

for file_path in all_files:
    fname = os.path.basename(file_path).replace(".md", "")
    # "Finance_" で始まるか判定して振り分け
    if fname.startswith("Finance_"):
        display_title = fname.replace("Finance_", "", 1)
        display_title = display_title.split("_", 1)[-1] if "_" in display_title else display_title
        date_part = fname.replace("Finance_", "", 1).split("_", 1)[0]
        finance_links += f"* [{date_part}： {display_title}](articles/{urllib.parse.quote(fname)}/)\n"
    else:
        # IT_で始まるもの、または過去の無印ファイルはIT枠へ
        display_title = fname.replace("IT_", "", 1)
        display_title = display_title.split("_", 1)[-1] if "_" in display_title else display_title
        date_part = fname.replace("IT_", "", 1).split("_", 1)[0]
        it_links += f"* [{date_part}： {display_title}](articles/{urllib.parse.quote(fname)}/)\n"

# 1. ITトップページ（index.md）
with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write("# 最新ガジェット＆AI アーカイブ\n\nITと最新テクノロジーの比較まとめです。\n\n## 💻 IT・ガジェット最新記事\n\n" + it_links)

# 2. 金融トップページ（finance.md）
with open("docs/finance.md", "w", encoding="utf-8") as f:
    f.write("# マネー＆投資 アーカイブ\n\n新NISAや資産運用の最新トレンド比較まとめです。\n\n## 📈 金融・経済最新記事\n\n" + finance_links)

print("すべての処理とページの更新が完了しました！")