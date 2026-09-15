# MMIA-R008：明示的二段階MicroModel通信

登録日：2026-09-15。状態：`seed-1-feasibility-completed`。モデル学習前にstage境界、比較条件、停止条件を固定した。E1が停止条件を通過したためE2まで実行した。[結果](MMIA-R008-results.md)を参照。testは未開封。

## 仮説

最終回答だけを直接学習するend-to-end Adapterより、中間値を明示的な整数メッセージとして渡す二段階構成の方が、複合技能問題の失敗箇所を分離できる。品質が改善するかは未確定であり、2回推論と誤差伝播の費用を含めて評価する。

## Stage境界

pilot-v3の保存済み`intermediate_answers`を唯一の境界とする。

```text
original problem → Stage 1 → integer intermediate
integer intermediate + downstream operation → Stage 2 → integer final
```

Stage 1/2のpromptはtask familyとlanguageから決定的に生成する。Stage 2へ元の正解最終値やsplit外情報を渡さない。

## 診断条件

| 条件 | Stage 1入力 | Stage 2入力 | 意味 |
| --- | --- | --- | --- |
| E0 | なし | なし | R007 end-to-end C1 |
| E1 | なし | teacher中間値 | Stage 2能力の上限 |
| E2 | 元問題の前段 | Stage 1予測値 | 完全な二段階構成 |

まずrank 8 Mixed Stage 1とrank 8 Mixed Stage 2をseed 20260915で各train全432行、1 epoch学習する。E1がE0を上回らない場合、分解自体に利益がないためE2と追加seedを停止する。E1が上回る場合だけStage 1を評価してE2を実行する。

主要品質は最終回答のsemantic-group macro exact match。Stage 1 exact match、teacher Stage 2 exact match、end-to-end exact match、完全pipeline exact matchを併記する。E1−E2を上流誤差伝播、E2−E0を構成の純品質差として扱う。

費用は両Stageの学習token・時間・parameter・保存byte、E2の2回分の推論時間とmodel loadを報告する。この初回診断はC1と学習updateを一致させない。二段階を成立させられるかを先に測り、成立時だけ同一総予算対照を別IDで登録する。

**English:** MMIA-R008 turns pilot-v3's stored intermediate target into an explicit integer message between two adapters. Teacher-intermediate Stage 2 is evaluated first; if it cannot beat the R007 end-to-end baseline, the predicted-intermediate pipeline stops. This diagnostic intentionally measures feasibility before registering an equal-total-training-budget comparison.

**简体中文：** MMIA-R008把pilot-v3保存的中间目标作为两个Adapter之间的显式整数消息。先评估使用teacher中间值的第二阶段；若无法超过R007端到端基线，则停止预测中间值pipeline。该诊断先验证可行性，之后才另行注册相同总训练预算的比较。
