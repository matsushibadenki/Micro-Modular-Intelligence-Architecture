# MMIA-R009：同一update予算の二段階通信 seed 20260915

実施日：2026-09-15。Stage 1とStage 2へ216 updateずつ配分し、MMIA-R007のend-to-end Adapter 432 updateと総optimizer updateを一致させた。各Stageは`domain × difficulty × language`の36セルから6件ずつ選択した。validation 432件を評価し、testは未使用である。

## 品質

| 条件 | strict accuracy |
| --- | ---: |
| B0 end-to-end | 21.30% |
| Stage 1 中間値 | 61.57% |
| teacher中間値 → Stage 2 | 87.04% |
| B1 実二段階pipeline | **55.56%** |

B1−B0は**+34.26pt**、semantic groupで対応を取ったbootstrap 95%区間は**+27.08〜+41.44pt**だった。点推定と区間下限がともに0を上回り、事前登録した残り2 seedへの継続条件を通過した。

| 経路 | B0 | B1 pipeline |
| --- | ---: | ---: |
| math→physics | 8.33% | 39.81% |
| code→math | 7.41% | 41.67% |
| logic→math | 67.59% | 94.44% |
| code→physics | 1.85% | 46.30% |

Stage 1は266/432件、pipelineは240/432件で正解した。正しい中間値からStage 2で失敗したものは26件、誤った中間値から最終正解へ戻ったものは0件だった。teacher Stage 2とpipelineの差は31.48pt（95%区間+24.77〜+38.66pt）で、残る主な制約は中間値予測である。

## 費用

| 学習対象 | update | 入力token | 教師token | 時間 | Adapter本体 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 end-to-end | 432 | 42,282 | 1,965 | 130.58秒 | 2,175,168 bytes |
| Stage 1 | 216 | 17,171 | 817 | 53.10秒 | 2,175,168 bytes |
| Stage 2 | 216 | 14,910 | 976 | 50.87秒 | 2,175,168 bytes |
| B1合計 | 432 | 32,081 | 1,793 | 103.97秒 | 4,350,336 bytes |

B1はB0に対して入力token 75.9%、教師token 91.2%、学習時間79.6%だった。updateだけでなく実tokenも少ないため、このseedでは学習計算量を増やして得た改善ではない。ただし独立Adapterを2つ保存するためAdapter本体は2倍である。

二段階completion合計p50/p95は0.380/0.488秒で、B0の0.291/0.399秒に対して1.31/1.22倍だった。モデルloadとAdapter切替時間を含まないため、常駐実装の実運用遅延とは区別する。

## 判断

- [Done] seed 20260915で同一432 update比較を完了した。
- [Done] 全セル均等化、実token、時間、保存量、誤差伝播を記録した。
- [Next] seed 20260916と20260917でB0/B1を再学習し、seedとsemantic groupの階層bootstrapを行う。
- [Later] 3 seed成立後に同一入力token対照とStage 1 curriculumを事前登録する。

**English:** With the same total 432 optimizer updates, the explicit two-stage pipeline reached 55.56% versus 21.30% for the end-to-end adapter. The paired semantic-group difference was +34.26 points (95% interval +27.08 to +41.44). The pipeline used 75.9% of the baseline input tokens and 79.6% of its training time, but stored two adapters and required two inference completions. This seed passes the preregistered gate for two additional seeds.

**简体中文：** 在相同的432次总优化更新下，显式两阶段pipeline达到55.56%，端到端Adapter为21.30%。按语义组配对的差值为+34.26个百分点（95%区间+27.08至+41.44）。pipeline使用基线75.9%的输入token和79.6%的训练时间，但需保存两个Adapter并执行两次推理。本seed通过了继续另外两个seed的预注册门槛。
