# MMIA-R007 C2 seed 1：経路専門化診断

実施日：2026-09-15。pilot-v3の強い床効果を経路専門Adapterが破れるか確認するため、登録比較のC2 seed 1を診断実行した。4専門家は各経路のtrain 108行を1回処理し、oracle経路labelで選択した。testは未使用。

## 予算照合

| 条件 | update | 入力token | 教師token | 学習時間 |
| --- | ---: | ---: | ---: | ---: |
| C1 rank 8 Mixed | 432 | 42,282 | 1,965 | 130.58秒 |
| C2 rank 8 specialists合計 | 432 | 42,282 | 1,965 | 124.51秒 |

各Adapterのactive可学習parameterは540,672。C2は4 Adapterを保存するため総容量はC1の4倍である。全学習lossは有限だった。

## 品質

| 条件 | strict accuracy | format invalid | truncated | completion p50／p95 |
| --- | ---: | ---: | ---: | ---: |
| C1 Mixed | 21.30% | 0 | 0 | 0.291／0.399秒 |
| C2 Specialists | 17.59% | 0 | 0 | 0.227／0.289秒 |

C2−C1は−3.70pt、paired semantic-group bootstrap 95% CIは−8.33〜+0.93pt。C2は品質を改善しなかった。

| 経路 | C1 | C2 | C2−C1 |
| --- | ---: | ---: | ---: |
| math→physics | 8.33% | 1.85% | −6.48pt |
| code→math | 7.41% | 3.70% | −3.70pt |
| logic→math | 67.59% | 60.19% | −7.41pt |
| code→physics | 1.85% | 4.63% | +2.78pt |

唯一改善した`code→physics`も5%未満で、比較可能な精度域へ達していない。専門化は非logic経路の床効果を解消しなかった。

## 判断

MMIA-R007の残るseedとC3は停止する。理由は、現在の最終回答だけを教師にするend-to-end設定では、C1/C2とも3経路が床に近く、C2 seed 1もC1を下回ったためである。追加seedはこの実装の分散を狭めても、MicroModel間連携の機序を直接検証しない。

次はpilot-v3に保存済みの中間値を境界として使う。

1. Stage 1 MicroModelへ元問題から中間値を出力させる。
2. Stage 2 MicroModelへ中間値と後段操作を渡し、最終値を出力させる。
3. teacher中間値、予測中間値、end-to-end C1を比較する。
4. teacher条件で成功し予測条件で失敗する割合を、stage 1誤差伝播として測る。

これにより、単なるAdapter容量比較から、明示的通信を持つMicroModel構成の検証へ移る。

- [Done] C2 seed 1の同一token/update診断。
- [Done] oracle専門家予測432行のcoverage・重複・経路不一致検査。
- [Done] R007 end-to-end比較の停止判断。
- [Next] 中間値境界を用いる二段階実験のdataset viewとプロトコルを作る。

## 成果物

- [C1/C2比較](../../results/MMIA-R007/seed-20260915/compare-specialists-vs-mixed.json)
- [C2結合予測](../../results/MMIA-R007/seed-20260915/eval-specialists/predictions.jsonl)／[解析](../../results/MMIA-R007/seed-20260915/eval-specialists/group-analysis.json)
- [C2結合manifest](../../results/MMIA-R007/seed-20260915/eval-specialists/manifest.json)

**English:** With exactly matched 432-update and 42,282-input-token budgets, seed-1 path specialists scored 17.59% versus 21.30% for mixed LoRA, a −3.70-point difference (paired 95% interval −8.33 to +0.93). Only code-to-physics improved, from 1.85% to 4.63%, still near the floor. The remaining end-to-end seeds and C3 are stopped. The next experiment will explicitly pass the stored intermediate value from a stage-1 MicroModel to a stage-2 MicroModel.

**简体中文：** 在完全相同的432次更新和42,282个输入token预算下，seed-1路径专家为17.59%，混合LoRA为21.30%，差值−3.70个百分点（配对95%区间−8.33至+0.93）。只有code→physics从1.85%提高到4.63%，仍接近地板。停止其余end-to-end seed与C3。下一实验将明确把保存的中间值从第一阶段MicroModel传递给第二阶段MicroModel。
