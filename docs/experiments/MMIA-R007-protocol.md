# MMIA-R007：複合技能Adapter比較プロトコル

登録日：2026-09-15。状態：`stopped-after-seed-1-diagnostic`。pilot-v3の生成規則、dataset hash、比較条件をモデル評価前に固定した。その後、事前の学習可能性確認とC2 seed 1診断により非logic経路の強い床効果が解消されなかったため、残るseedとC3を停止した。[停止判断](MMIA-R007-C2-diagnostic-results.md)を参照。testは未開封である。

## 問い

二つの技能を順に必要とする問題では、連携経路別Adapterが、同じactive容量のMixed Adapterおよび同じ総容量の大きいMixed Adapterより品質・費用関係を改善するか。

R002では単一分野問題において、4専門Adapterはrank 8 Mixedを小さく上回ったが、同じ総容量のrank 32 Mixedを下回った。R007は、専門化の価値が複合処理で現れる可能性を検査する。

## 固定dataset

`pilot-v3.jsonl`、SHA-256 `07d814abfe4e3f35d3f5f59fe2be372158429f05a1459fb5ea6bd9d08cfa450b`。

- 4連携経路：`math→physics`、`code→math`、`logic→math`、`code→physics`。
- train／validation／test × easy／medium／hard × 12意味問題。
- 各意味問題は英語・日本語・简体中文の3翻訳。432意味group、1,296行。
- 各行は構造化parameter、中間値、最終値を持つ。監査器は中間値と最終値を独立に再計算する。
- 36 template IDはsplit間で非共有。翻訳された同一問題は同じsplitに置く。
- `logic→math`の論理分岐は各split・難易度で真6／偽6。

人工的な制御datasetであり、一般的な複合推論能力を代表しない。最終値だけを採点するため、正答しても内部で宣言された中間処理を実行したとは断定しない。中間値への介入評価は後続実験とする。

## 比較条件

| 条件 | 構成 | 学習予算 | 選択 |
| --- | --- | --- | --- |
| C0 | Core only | なし | なし |
| C1 | rank 8 Mixed LoRA | train全432行を1回 | 単一 |
| C2 | 4つのrank 8経路専門LoRA | 各経路108行、合計432行を1回 | oracle経路label |
| C3 | rank 32 Mixed LoRA | train全432行を1回 | 単一 |

seedは`20260915`、`20260916`、`20260917`。LoRA対象層、alpha/r比、optimizer、learning rate、系列長、precision、decode、timeoutはMMIA-R002と同じに固定する。C1/C2/C3の実処理入力tokenと教師tokenをmanifestで照合する。

## 主要評価と判断

主要指標は3翻訳の平均を各意味groupのscoreとするmacro exact match。C2−C1とC2−C3を同一問題・seedで対応付ける。固定3 seedで各groupの差を平均したcluster bootstrapと、seed・groupの階層bootstrapを報告する。

専門分割を次段階へ進める条件は、C2−C3の点推定が正で、主要95%区間下限も0より大きいこと。C1だけに勝ってC3に勝てない場合は、分割ではなく総容量増加で説明できるため不採択とする。

推論p50/p95、学習時間、peak RSS、active/total parameter、Adapter重みbyteを併記する。C2はoracle selectionであり、router費用を含まない。oracleでもC3に勝てなければMMIA-R003のrouter実装へ進まない。

## 後続の二段階介入

この比較はend-to-end Adapter同士であり、MicroModel間の明示的通信をまだ実装しない。C2が有望な場合、各問題の保存済み中間値を境界として、stage 1出力をstage 2入力へ渡す逐次構成を登録する。teacher中間値、予測中間値、単一end-to-endの3条件を比較し、誤差伝播と通信費用を分離する。

**English:** MMIA-R007 uses the fixed multilingual pilot-v3 to compare rank-8 mixed, four oracle path-specialist rank-8 adapters, and an equal-total-capacity rank-32 mixed adapter on two-skill tasks. Advancement requires specialists to beat C3, not merely C1. The dataset contains 432 semantic groups and recomputable intermediate and final targets; test remains unopened.

**简体中文：** MMIA-R007使用固定的多语言pilot-v3，在双技能任务上比较rank-8混合Adapter、四个oracle路径专家Adapter，以及相同总容量的rank-32混合Adapter。只有专家组超过C3时才进入下一阶段，而非仅超过C1。数据包含432个语义组，并可重新计算中间值与最终值；test仍未打开。
