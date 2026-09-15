# MMIA-R009：同一update予算の二段階通信

登録日：2026-09-15。状態：`completed-3-seeds`。MMIA-R008の成立性確認後、学習前に予算配分と判断基準を固定した。seed 20260915、20260916、20260917を完了した。testは未開封。

## 問い

明示的なStage 1→Stage 2整数通信は、end-to-end Adapterと総optimizer updateを一致させても品質を改善するか。

## 条件

| 条件 | 学習 | 総update |
| --- | --- | ---: |
| B0 | MMIA-R007 E0 rank 8 end-to-end | 432 |
| B1 | rank 8 Stage 1を216 + rank 8 Stage 2を216 | 432 |

B1の各stageはtrainについて`domain × difficulty × language`の36セルから6行ずつ選び、216行とする。seed 20260915。LoRA、optimizer、learning rate、decodeはR008と同じ。各stageは別Adapterを持つため、active学習parameterの総和と保存量はB0の2倍である。

update数は一致するが、stage promptはend-to-end promptより短い。このため実入力token、教師token、学習時間を保存し、tokenが一致した比較とは表現しない。成立時にはtoken一致対照を別条件で追加する。

## 評価

Stage 1、teacher Stage 2、予測中間値pipelineを同じvalidation 432行で評価する。主要比較はB1 pipeline−B0のsemantic-group macro exact matchとpaired bootstrap 95%区間。B1の点推定がB0を上回り、区間下限が0より大きければ、残る2 seedへ進む。

品質に加え、2回分のcompletion p50/p95、学習token・時間、Adapter byte、Stage 1誤差伝播を報告する。B1がB0を上回らない場合は、同一token比較やrouterへ進まず停止する。

**English:** MMIA-R009 allocates the same total 432 optimizer updates as the end-to-end baseline: 216 balanced updates to Stage 1 and 216 to Stage 2. Actual token counts remain measured because stage prompts are shorter. Seed 1 must show a paired improvement with a positive 95% lower bound before two more seeds are run.

**简体中文：** MMIA-R009把与端到端基线相同的432次总更新分配为Stage 1和Stage 2各216次，并在领域、难度和语言上保持均衡。由于stage prompt更短，仍单独记录实际token数。只有seed 1的配对改善及95%区间下限均大于0时，才继续另外两个seed。
