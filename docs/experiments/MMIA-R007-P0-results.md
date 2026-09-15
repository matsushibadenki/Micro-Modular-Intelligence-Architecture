# MMIA-R007-P0：pilot-v3学習可能性

実施日：2026-09-15。複合技能pilot-v3が0.5B Core＋LoRAで比較可能な精度域へ移るかを確認した。72-step層化Mixed LoRAと、登録比較C1の第1 seedに相当する432-step Mixed LoRAをCore-onlyと比較した。testは未使用。

## 結果

| 条件 | 学習行 | strict accuracy | format invalid | truncated |
| --- | ---: | ---: | ---: | ---: |
| Core only | 0 | 3.01% | 109 | 48 |
| rank 8 Mixed pilot | 72 | 10.19% | 6 | 0 |
| rank 8 Mixed C1 seed 1 | 432 | 21.30% | 0 | 0 |

432-step C1のCoreに対する差は+18.29pt、paired semantic-group bootstrap 95% CIは+12.96〜+24.07pt。学習時間130.58秒、入力42,282 token、教師1,965 token、lifetime peak RSS 3.855 GBだった。

| 連携経路 | Core | 72-step | 432-step |
| --- | ---: | ---: | ---: |
| math→physics | 1.85% | 3.70% | 8.33% |
| code→math | 1.85% | 1.85% | 7.41% |
| logic→math | 8.33% | 33.33% | 67.59% |
| code→physics | 0.00% | 1.85% | 1.85% |

## 判断

出力形式とlogic経路は学習可能だが、非logic 3経路は全量1 epoch後も1.85〜8.33%で、比較の床効果が強い。全体21.30%だけを根拠に3-seed本比較へ進むと、logic経路の寄与を専門化一般の効果として誤認する恐れがある。

次はC2経路専門Adapterをseed 1だけ診断実行する。C2が非logic各経路を明確に床から離せる場合はC2/C3を継続する。離せない場合は、現在の0.5Bモデルと数値範囲によるR007を停止し、数値範囲縮小、段階別採点、またはCoreサイズ変更を別実験IDで登録する。

- [Done] 72-step学習可能性pilot。
- [Done] C1 seed 1全量学習・validation。
- [Next] C2 seed 1経路専門Adapterによる床効果診断。
- [Later] 診断通過時のみ残るseedとC3を実行。

## 成果物

- [72-step学習manifest](../../results/MMIA-R007/learnability-mixed/manifest.json)／[評価](../../results/MMIA-R007/learnability-mixed-eval/group-analysis.json)
- [C1学習manifest](../../results/MMIA-R007/seed-20260915/train-mixed/manifest.json)／[評価](../../results/MMIA-R007/seed-20260915/eval-mixed/group-analysis.json)
- [C1対Core](../../results/MMIA-R007/seed-20260915/eval-mixed/compare-vs-core.json)

**English:** A 72-step mixed LoRA raised pilot-v3 validation from 3.01% to 10.19%; the full 432-step C1 seed reached 21.30% (+18.29 points, paired 95% interval +12.96 to +24.07). However, logic-to-math reached 67.59% while the other three paths remained at 1.85–8.33%. C2 seed 1 will be used as a diagnostic: continue the full comparison only if path specialization breaks these floors.

**简体中文：** 72步混合LoRA将pilot-v3验证正确率从3.01%提高到10.19%；完整432步C1 seed达到21.30%（+18.29个百分点，配对95%区间+12.96至+24.07）。但logic→math达到67.59%，其余三条路径仍只有1.85%–8.33%。下一步以C2 seed 1进行诊断，只有路径专业化能突破这些地板效应时才继续完整比较。
