# MMIA-R002-P1：層化混合LoRA pilot

実施日：2026-09-14。目的はMMIA-R002の学習予算を見積もり、層化samplingとAdapter評価経路を確認すること。1 seedの探索結果であり、単一LoRA対専門LoRAの本比較ではない。

## 学習条件と費用

pilot-v2 trainから、分野4 × 言語3 × 難易度3の各セルを2行ずつ選んだ。翻訳違いを同じ意味問題として重複選択せず、72行・72意味問題とした。

| 指標 | 実測値 |
| --- | ---: |
| optimizer step | 72 |
| 入力token／target token | 5,650／299 |
| 学習時間 | 18.975秒 |
| process lifetime peak RSS | 4.013 GB（10進） |
| trainable parameter | 540,672（約0.109%） |
| LoRA | rank 8、alpha 16、q_proj/v_proj |

全lossとgradient normは有限だった。最初のlossは3.8733、最後は0.0710、全step平均は0.8269。ただし各stepは異なる問題であり、最初と最後の差を収束の証拠としない。

1 step平均は約0.264秒だった。同じ実装でtrain全432行を1 epoch処理する単純外挿は約114秒だが、これは計画値であり実測ではない。保存・load・評価、seed間変動、長さ分布の差を含まない。

## 探索validation

学習後の混合LoRAを、Core床効果と同じ144意味問題・432翻訳行で評価した。

| 指標 | Core | 72-step mixed LoRA | 差 |
| --- | ---: | ---: | ---: |
| strict accuracy | 21.8% | 41.2% | +19.4pt |
| paired group bootstrap 95%区間 | — | — | +13.9〜+24.8pt |
| 全3言語正解group | 3.5% | 34.0% | +30.6pt |
| format invalid | 93 | 0 | −93 |
| truncated | 43 | 0 | −43 |
| 完了時間p50 | 0.185秒 | 0.191秒 | +3.0% |
| 完了時間p95 | 0.577秒 | 0.252秒 | −56.3% |

p95短縮は主に説明出力・truncationが消えたことに対応し、Adapter演算自体がCoreを高速化したという意味ではない。p50はわずかに増えた。単一run同士の時間差なので性能結論には使わない。

分野別はMath 22.2→30.6%、Physics 1.9→20.4%、Coding 12.0→33.3%、Logic 50.9→80.6%。言語別は英語26.4→42.4%、日本語15.3→41.0%、简体中文23.6→40.3%。難易度別はeasy 38.2→78.5%、medium 11.8→25.0%、hard 15.3→20.1%だった。paired bootstrap差の95%区間はhardのみほぼ0を含み、他の主要sliceは正だった。

## 解釈

少量LoRAが未見templateで出力形式と一部task familyを改善できることは観測された。改善の一部は専門知識ではなく、整数だけを返す応答形式の学習である。これはMMIAのモジュール分割を支持する結果ではなく、C1 mixed LoRAを強いbaselineとして必ず置く必要性を示す。

本比較では次を守る。

- C1 mixedとC2 specialistsで総処理token／optimizer update相当量を揃える。
- 同じ整数出力学習を全群へ与え、専門家だけがformat遵守で有利にならないようにする。
- 3 seedで実行し、同じexampleをpaired比較する。
- validationで条件を決めるまでtestを実行しない。
- hardの改善が小さいため、macro平均だけでなく難易度別を必須とする。

## 成果物

- [学習設定](../../configs/lora-medium-mixed.json)／[学習manifest](../../results/MMIA-R002-P1/run-01/manifest.json)／[stepログ](../../results/MMIA-R002-P1/run-01/steps.jsonl)
- [評価設定](../../configs/lora-medium-mixed-eval.json)／[個別予測](../../results/MMIA-R002-P1/eval-01/predictions.jsonl)／[集計](../../results/MMIA-R002-P1/eval-01/summary.json)
- [group解析](../../results/MMIA-R002-P1/eval-01/group-analysis.json)／[Coreとのpaired比較](../../results/MMIA-R002-P1/eval-01/paired-comparison.json)

## English / 简体中文

**English:** A stratified 72-step mixed-LoRA pilot processed 5,650 input tokens in 18.98 seconds with 4.01GB lifetime peak RSS. Exploratory strict validation accuracy rose from 21.8% to 41.2%, a paired semantic-group difference of +19.4 points (95% bootstrap interval +13.9 to +24.8). Format violations and truncations fell to zero. This one-seed result mainly establishes a strong mixed-LoRA baseline and may partly reflect output-format learning; it does not support specialist modularity yet.

**简体中文：** 分层72步混合LoRA试验处理了5,650个输入token，训练耗时18.98秒，进程生命周期峰值RSS为4.01GB。探索性严格验证正确率从21.8%升至41.2%，按语义组配对bootstrap的差值为+19.4个百分点（95%区间+13.9至+24.8）。格式错误与截断均降至0。该单seed结果主要确立了较强的混合LoRA基线，部分改善可能来自输出格式学习，尚不能支持专业模块化假设。
