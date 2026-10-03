# 過去問データ（1問1行）

写真から文字起こしした過去問をここに入れる。まだ0件（写真未取得のため）。

## questions.csv の列（`questions_template.csv` をコピーして使う）

| 列 | 内容 |
|---|---|
| question_id | `2N-YYYYMM-Qn`（例 `2N-202602-Q1`）。同一英文の再出題も期ごとに1行。同一英文の束ねは `similar_ids` と `rework_type` で行う |
| year / period / q_no | 年 / 月(02,04,07,10) / 問題番号 |
| in_seizando / in_kaibundo / in_mlit | 各資料に収録されていれば 1。3資料の「両方にある/片方のみ」はこの3列で判定 |
| title | 英文の見出し（ない場合は空） |
| english_text | 英文全文。**原則として国交省原本**。原本がなければ問題集版。判読できない箇所は `［判読不明］` |
| question_prompt | 設問文（例「次の英文を和訳せよ」） |
| model_answer_ref | 問題集の模範解答の所在（書名・頁）。**訳文そのものは公開リポジトリに転記しない**（著作物） |
| translation_ja_own | 自分（分析側）で作った訳 |
| format | 全文和訳 / 下線部和訳 / 内容説明 / 空欄補充 / 英作文 / 語句説明 など |
| theme | `data/sheet/2N_title_meta.csv` と同じ分類名を使う |
| key_terms / key_phrases / key_structures | `;` 区切り |
| difficulty | 1〜3 |
| similar_ids | 類似・同一英文の question_id（`;` 区切り） |
| rework_type | 完全一致 / ほぼ同一 / 一部変更 / 語句だけ変更 / 数字・船種のみ変更 / 同一出典 / 同一条約 / 同一規則 / テーマ同じ / 構文同じ |
| source_estimate / source_grade | 推定原典 / A〜D |
| source_match_type | 完全引用 / 一部引用 / 要約 / 改変 / 単語変更 |
| sheet_row | 出題表（◆英語分析◆ 2N）の行番号。照合用 |
| illegible_notes | 判読不明箇所のメモ |

## source_diffs.csv（資料間差分。統一せず全部残す）

1つの差分につき1行。`field` は english_text / question_prompt / year / q_no / model_answer など。
`adopted` は採用した版（原則 mlit）。差分があっても問題集側の表記は消さない。
