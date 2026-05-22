import pandas as pd
from datetime import datetime

# 1. 架空のデータを作成
data = {
    "商品名": ["ゲーミングPC A", "ゲーミングPC B", "ゲーミングPC C"],
    "Amazon価格": ["150,000円", "145,000円", "160,000円"],
    "楽天価格": ["152,000円", "143,000円", "158,000円"],
    "最安値": ["Amazon", "楽天", "楽天"]
}
df = pd.DataFrame(data)

# 2. データをMarkdown形式の表に変換
markdown_table = df.to_markdown(index=False)

# 3. 現在の時刻を取得
now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

# 4. ページ全体の内容を組み立てる
page_content = f"""# 自動更新ポータルサイト（テスト）

このページはPythonプログラムによって自動生成されています。
**最終更新日時:** {now}

## 最新価格比較表

{markdown_table}
"""

# 5. docs/index.md に上書き保存する
with open("docs/index.md", "w", encoding="utf-8") as f:
    f.write(page_content)

print("Webサイトのトップページ（index.md）を更新しました！")