"""二級航海(2N)の出題表データから、周期・焼き直し・テーマ別集計を作る。

入力: data/sheet/sheet_2N_raw.json, data/sheet/2N_title_meta.csv
出力: data/sheet/2N_appearances.csv, analysis/01_出題周期と焼き直し分析_2N.md

注意: 入力は「タイトル＋出題年月」のみ。本文・設問・解答は含まない。
"""
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = [2, 4, 7, 10]


def ordinal(period):  # "2019/04" -> 試験回の通し番号（年4回）
    y, m = map(int, period.split("/"))
    return y * 4 + MONTHS.index(m)


def label(o):
    return f"{o // 4}/{MONTHS[o % 4]:02d}"


def main():
    raw = json.loads((ROOT / "data/sheet/sheet_2N_raw.json").read_text(encoding="utf-8"))
    meta = {int(r["row"]): r for r in csv.DictReader(
        open(ROOT / "data/sheet/2N_title_meta.csv", encoding="utf-8"))}

    items = []  # 1行 = 1つの英文（シート上の1行）
    for r in raw:
        title = (r["title"] or "").replace("\n", " ").strip()
        apps = []
        for mk in r["marks"]:
            m = re.match(r"(\d{4}/\d{2})\s*(.*)", mk)
            apps.append((ordinal(m.group(1)), m.group(2).strip()))
        if not apps:
            continue
        # 「2009/04に出題」等、タイトル欄が過去出題メモだけの行は未命名として扱う
        pre2011 = re.findall(r"(20(?:0\d|10)/\d{2})", title)
        m = meta.get(r["row"])
        if not m:  # タイトル欄がシート作成者のメモだけの行
            title = "（タイトル未記入）" + (f"［{'/'.join(pre2011)}既出］" if pre2011 else "")
        items.append({
            "row": r["row"],
            "title": m["title_normalized"] if m else title,
            "titled": bool(m),
            "theme": m["theme"] if m else "不明（タイトル未記入）",
            "source": m["source_estimate"] if m else "",
            "grade": m["source_grade"] if m else "D",
            "apps": sorted(apps),
            "pre2011": pre2011,
        })

    # --- 出現一覧CSV
    with open(ROOT / "data/sheet/2N_appearances.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet_row", "period", "note", "nth_in_sheet", "title", "theme",
                    "source_estimate", "source_grade", "pre2011_notes"])
        for it in items:
            for n, (o, note) in enumerate(it["apps"], 1):
                w.writerow([it["row"], label(o), note, n, it["title"], it["theme"],
                            it["source"], it["grade"], " ".join(it["pre2011"])])

    by_period = defaultdict(list)
    for it in items:
        for n, (o, note) in enumerate(it["apps"], 1):
            by_period[o].append((it, n, note))

    out = []
    p = out.append
    p("# 二級海技士（航海）英語 出題周期・焼き直し分析（出題表ベース・暫定）\n")
    p("> **データの範囲と限界（事実）**")
    p("> - 入力は Google Drive の共有スプレッドシート「◆英語分析◆」の `2N` シート（所有者: 第三者、最終更新 2026-04-09）のみ。")
    p("> - 記録されているのは **英文タイトル（または書き出し）と出題年月** だけ。英文本文・設問・模範解答は含まれない。")
    p("> - 収録範囲は 2011/04〜2026/02。**2026/04・2026/07 は未収録**。成山堂・海文堂・国土交通省原本との照合は未実施。")
    p("> - シート作成者の判定（同一英文かどうか）をそのまま使っている。本文照合で覆る可能性がある。")
    p("> - このファイルは `scripts/analyze_sheet_2N.py` で自動生成。\n")

    # 期ごと
    p("## 1. 試験期ごとの出題（シート記載順）\n")
    p("凡例: 🆕=シート上の初出 / 🔁n=シート上n回目（2011年以前の出題メモは別欄）\n")
    p("| 試験期 | 出題英文 |")
    p("|---|---|")
    for o in sorted(by_period):
        cells = []
        for it, n, note in by_period[o]:
            tag = "🆕" if n == 1 else f"🔁{n}"
            extra = f"（シート注記: {note}）" if note else ""
            pre = f"［2011年以前: {', '.join(it['pre2011'])}］" if it["pre2011"] else ""
            cells.append(f"{tag} {it['title']}{pre}{extra}")
        p(f"| {label(o)} | " + "<br>".join(cells) + " |")
    p("")
    odd = [label(o) for o in sorted(by_period) if len(by_period[o]) != 2]
    p(f"**資料内の不整合（事実）**: 1期あたり2題が基本だが、次の期は記載数が2でない: {', '.join(odd)}。"
      "シート上で初出の印と再出の印が同じ列に重なった可能性がある。原本照合で確定させる必要がある。\n")

    # 再出題間隔
    p("## 2. 焼き直し（同一英文の再出題）と間隔\n")
    p("| 英文 | 出題期 | 間隔（年） | テーマ |")
    p("|---|---|---|---|")
    gaps = []
    rep = [it for it in items if len(it["apps"]) >= 2]
    for it in sorted(rep, key=lambda x: -len(x["apps"])):
        os_ = [o for o, _ in it["apps"]]
        g = [(b - a) / 4 for a, b in zip(os_, os_[1:])]
        gaps += g
        p(f"| {it['title']} | {' → '.join(label(o) for o in os_)} | {', '.join(f'{x:.2f}' for x in g)} | {it['theme']} |")
    p("")
    pre_gaps = []
    for it in items:
        for d in it["pre2011"]:
            pre_gaps.append((it["apps"][0][0] - ordinal(d)) / 4)
    p(f"- 参考: 2011年以前の出題メモ（シート注記）→シート上の初出 の間隔: {len(pre_gaps)}件、"
      f"中央値 {statistics.median(pre_gaps):.2f}年、範囲 {min(pre_gaps):.2f}〜{max(pre_gaps):.2f}年"
      "（2011〜2017年の「🆕」の多くは実際には2005〜2010年の英文の再出題）")
    p(f"- 再出題された英文: **{len(rep)}件**（シート上の英文 {len(items)}件中）")
    p(f"- 再出題間隔: 件数 {len(gaps)}、中央値 **{statistics.median(gaps):.2f}年**、"
      f"平均 {statistics.mean(gaps):.2f}年、最短 {min(gaps):.2f}年、最長 {max(gaps):.2f}年")
    hist = Counter(int(g) for g in gaps)
    p("- 間隔の分布（整数年で切り捨て）: " + ", ".join(f"{k}年台 {hist[k]}件" for k in sorted(hist)))
    p("")

    # 直近の構造
    p("## 3. 直近期の「再出題1題＋新規1題」構造\n")
    p("| 試験期 | 再出題 | 初回出題期 | 間隔（年） | 新規 |")
    p("|---|---|---|---|---|")
    recent = [o for o in sorted(by_period) if o >= ordinal("2022/02")]
    for o in recent:
        reps = [(it, n) for it, n, _ in by_period[o] if n > 1]
        news = [it for it, n, _ in by_period[o] if n == 1]
        r_s = "<br>".join(it["title"] for it, _ in reps) or "—"
        prev = "<br>".join(label(it["apps"][n - 2][0]) for it, n in reps) or "—"
        gap = "<br>".join(f"{(o - it['apps'][n - 2][0]) / 4:.2f}" for it, n in reps) or "—"
        p(f"| {label(o)} | {r_s} | {prev} | {gap} | {'<br>'.join(it['title'] for it in news) or '—'} |")
    p("")

    # テーマ集計
    p("## 4. テーマ別集計（タイトル付き英文のみ）\n")
    p("テーマ分類はタイトルからの推定（本文未照合）。出現回数＝シート上の●の数（2011年以前の注記は除く）。\n")
    p("| テーマ | 英文数 | 出現回数 | 再出題英文数 | 直近出題 | 直近からの空白（回） | 出題期 |")
    p("|---|---|---|---|---|---|---|")
    last_o = max(by_period)
    th = defaultdict(list)
    for it in items:
        if it["titled"]:
            th[it["theme"]].append(it)
    rows = []
    for t, its in th.items():
        os_ = sorted(o for it in its for o, _ in it["apps"])
        rows.append((len(os_), t, len(its), sum(len(it["apps"]) > 1 for it in its), os_))
    for n, t, k, r, os_ in sorted(rows, reverse=True):
        p(f"| {t} | {k} | {n} | {r} | {label(os_[-1])} | {last_o - os_[-1]} | {', '.join(label(o) for o in os_)} |")
    untitled = [it for it in items if not it["titled"]]
    p(f"\n- タイトル未記入の英文: {len(untitled)}件、出現 {sum(len(it['apps']) for it in untitled)}回（テーマ判定不能）。\n")

    # 原典確度
    p("## 5. 原典推定の確度（タイトルベース）\n")
    gc = Counter(it["grade"] for it in items if it["titled"])
    p("| 確度 | 件数 | 意味 |")
    p("|---|---|---|")
    desc = {"A": "原典ほぼ確定（本文照合済みのみ付与。現時点0件）", "B": "かなり可能性が高い（規則番号・見出しが一致）",
            "C": "テーマ・出典系統のみ推定", "D": "原典不明"}
    for g in "ABCD":
        p(f"| {g} | {gc.get(g, 0)} | {desc[g]} |")
    p("\n本文を照合していないため、**A判定は意図的に0件**としている。\n")

    # 未再出題プール
    p("## 6. 再出題の「順番待ち」候補（観察＋仮説）\n")
    p("**観察（事実）**: 2023/02 以降の各期は、シート上「再出題1題＋新規1題」になっている（2025/02〜2026/02 も同様）。"
      "再出題された英文の前回出題期は、おおむね古い順に進んでいる（2024/10→2019/04, 2025/02→2019/10, 2025/04→2020/02, "
      "2025/10→2020/04, 2026/02→2020/07）。\n")
    p("**仮説（推測）**: この順送りが続くなら、次に再出題されやすいのは「2020/10 以降に最後に出題され、まだ再出題されていない英文」。"
      "ただし 2026/04・2026/07 の実際の出題が未確認で、順番がどこまで進んだか分からない。手持ちの問題集で 2026/04・2026/07 を確認すれば、"
      "この表のどこまで消化されたかが分かる。\n")
    p("| 最終出題期 | 英文 | 出現回数 | テーマ | 原典推定（確度） |")
    p("|---|---|---|---|---|")
    for it in sorted(items, key=lambda x: x["apps"][-1][0]):
        lo = it["apps"][-1][0]
        if ordinal("2020/10") <= lo <= ordinal("2022/10"):
            p(f"| {label(lo)} | {it['title']} | {len(it['apps'])} | {it['theme']} | {it['source']}（{it['grade']}） |")
    p("\n上表のうち、2回以上すでに出ている英文（3回目候補）は、過去に3回以上出た例"
      "（stability of inflatable liferafts 4回、PERFORMING THE DECK WATCH 4回、Waves generated by typhoons 3回）があるため除外しない。\n")

    (ROOT / "analysis/01_出題周期と焼き直し分析_2N.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
