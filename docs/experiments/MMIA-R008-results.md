# MMIA-R008：明示的二段階MicroModel通信 seed 1

実施日：2026-09-15。pilot-v3の保存済み中間値を境界に、rank 8 Stage 1 Adapterとrank 8 Stage 2 Adapterを構成した。まずteacher中間値によるStage 2上限（E1）を確認し、停止条件通過後にStage 1予測値を実際に渡す完全pipeline（E2）を評価した。testは未使用。

## 品質

| 条件 | 内容 | strict accuracy |
| --- | --- | ---: |
| E0 | rank 8 end-to-end Mixed | 21.30% |
| E1 | teacher中間値 → Stage 2 | 90.74% |
| Stage 1 | 元問題前段 → 中間値 | 56.71% |
| E2 | Stage 1予測値 → Stage 2 | **52.31%** |

E1−E0は+69.44pt、paired semantic-group bootstrap 95% CIは+62.73〜+75.69pt。分解後の後段処理は十分に学習可能であり、事前の停止条件を通過した。

E2−E0は+31.02pt、95% CIは+23.61〜+38.66pt。明示的な整数中間値を渡す二段階構成は、このseedのend-to-end Adapterを大幅に上回った。

E1−E2は+38.43pt、95% CIは+30.79〜+45.83ptで、主な制約はStage 1の中間値予測にある。

| 経路 | E0 | E1 teacher | Stage 1 | E2 pipeline |
| --- | ---: | ---: | ---: | ---: |
| math→physics | 8.33% | 93.52% | 33.33% | 33.33% |
| code→math | 7.41% | 96.30% | 33.33% | 33.33% |
| logic→math | 67.59% | 94.44% | 100.00% | 94.44% |
| code→physics | 1.85% | 78.70% | 60.19% | 48.15% |

Stage 1正解は245/432、pipeline最終正解は226/432だった。中間値と最終値がともに正解したものは226件、正しい中間値からStage 2で失敗したものは19件、誤った中間値から偶然最終正解へ戻ったものは0件。したがって誤差伝播を明確に追跡できた。

## 費用

| 学習対象 | update | 入力token | 教師token | 時間 | peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| E0 end-to-end | 432 | 42,282 | 1,965 | 130.58秒 | 3.855 GB |
| Stage 1 | 432 | 34,335 | 1,635 | 108.38秒 | 3.799 GB |
| Stage 2 | 432 | 29,829 | 1,965 | 102.10秒 | 3.516 GB |
| E2合計 | 864 | 64,164 | 3,600 | 210.48秒 | 逐次process最大3.799 GB |

E2は成立性診断であり、E0よりupdateが2倍、入力tokenが1.52倍、学習時間が1.61倍である。品質差を同一学習予算での優位性とは解釈しない。

E2の2回推論を合計したcompletion p50/p95は0.378/0.486秒。E0の0.291/0.399秒に対して約1.30/1.22倍である。モデルload時間とAdapter切替はこの合計に含まれず、常駐Coreでの実装後に再測定が必要。

## 結論

MMIA-R008は、**中間表現を明示して計算を分割すると、最終回答だけを学習する小型Adapterより複合課題を解きやすくできる**という初期証拠を得た。R007の経路別end-to-end専門化17.59%とは異なり、E2は52.31%に達した。重要なのは専門家の名前やroutingではなく、監査可能な中間契約で計算を分割した点である。

ただし1 seedであり、学習予算も一致していない。次の研究では次を行う。

- [Done] teacher中間値Stage 2上限を測定。
- [Done] Stage 1実予測からStage 2 dataset viewを生成し、全432行を追跡。
- [Done] 誤差伝播と2回分の推論時間を測定。
- [Next] E0と総updateを一致させたStage 1/2の予算分配比較を登録する。
- [Next] Stage 1の算術・code中間値精度を改善するcurriculumを、総予算内で比較する。
- [Later] 3 seed反復と、整数以外の構造化message contractを検証する。

## 成果物

- [プロトコル](MMIA-R008-protocol.md)
- [Stage view監査](../../datasets/pilot-v3-stage-views-audit.json)
- [E1解析](../../results/MMIA-R008/stage2-teacher-eval/group-analysis.json)／[E1対E0](../../results/MMIA-R008/stage2-teacher-eval/compare-vs-end-to-end.json)
- [Stage 1解析](../../results/MMIA-R008/stage1-eval/group-analysis.json)
- [E2解析](../../results/MMIA-R008/stage2-predicted-eval/group-analysis.json)／[pipeline解析](../../results/MMIA-R008/stage2-predicted-eval/pipeline-analysis.json)
- [E2対E0](../../results/MMIA-R008/stage2-predicted-eval/compare-vs-end-to-end.json)／[E1対E2](../../results/MMIA-R008/stage2-predicted-eval/compare-teacher-vs-predicted.json)

**English:** Explicit two-stage communication reached 52.31% versus 21.30% for the end-to-end rank-8 adapter (+31.02 points, paired 95% interval +23.61 to +38.66). Teacher-intermediate Stage 2 reached 90.74%, while Stage 1 intermediate accuracy was 56.71%, identifying upstream prediction as the main bottleneck. This is a feasibility result: the two-stage system used twice as many updates and 1.52× the training input tokens. The next experiment must match total training budget.

**简体中文：** 显式两阶段通信达到52.31%，端到端rank-8 Adapter为21.30%（+31.02个百分点，配对95%区间+23.61至+38.66）。使用teacher中间值的Stage 2达到90.74%，Stage 1中间值正确率为56.71%，说明上游预测是主要瓶颈。这只是可行性结果：两阶段系统使用了两倍更新次数和1.52倍训练输入token。下一实验必须匹配总训练预算。
