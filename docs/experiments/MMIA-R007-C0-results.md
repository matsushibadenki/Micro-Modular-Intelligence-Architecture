# MMIA-R007-C0：pilot-v3 Core床効果

実施日：2026-09-15。モデル評価前に固定したpilot-v3 validationを、Qwen2.5-0.5B-Instruct Coreのみで評価した。学習比較ではなく、複合技能benchmarkの難易度と評価経路の確認である。testは未使用。

## Dataset監査

- 4連携経路 × 3 split × 3難易度 × 12意味問題＝432意味group。
- 英語・日本語・简体中文を合わせて1,296行。validationは144意味group・432行。
- 各問題の中間値と最終値を構造化parameterから再計算。
- 36 template IDはsplit間で非共有。
- `logic→math`は各split・難易度で真6／偽6。
- SHA-256：`07d814abfe4e3f35d3f5f59fe2be372158429f05a1459fb5ea6bd9d08cfa450b`。

## Core結果

| 指標 | 結果 |
| --- | ---: |
| strict exact match | 13/432（3.01%） |
| semantic-group bootstrap 95% CI | 1.39〜4.86% |
| 全3言語正解group | 0/144 |
| 1言語以上正解group | 12/144（8.33%） |
| format invalid | 109/432 |
| truncated | 48/432 |
| error／timeout | 0／0 |
| 成功行completion p50／p95 | 0.218／0.593秒 |
| model load | 4.767秒 |
| lifetime peak RSS | 3.543 GB |

| 連携経路 | strict accuracy |
| --- | ---: |
| math→physics | 2/108（1.85%） |
| code→math | 2/108（1.85%） |
| logic→math | 9/108（8.33%） |
| code→physics | 0/108（0.00%） |

## 解釈

pilot-v3はpilot-v2のCore床効果21.8%より大幅に難しい。単一操作を連結しただけでも0.5B Coreは最終整数へ安定して到達せず、特に`code→physics`は完全な床にある。学習後の全条件が同様に低精度なら、専門化の差を検出できないためdatasetを成功とはみなさない。

一方、正解が0に近いことだけでは「二段階推論が必要だった」と証明できない。長いprompt、より大きい数、出力形式の失敗も原因に含まれる。R007ではC1/C2/C3すべてのformat遵守と分野別精度を併記し、中間値の介入評価は後続実験に分離する。

## 状態

- [Done] pilot-v3生成・中間値／最終値監査・hash固定。
- [Done] Core-only validation 432行を保存。
- [Next] 短いrank 8 Mixed LoRA pilotで、床から離れて比較可能になるか確認。
- [Later] 比較可能なら登録済みC1/C2/C3を3 seed実行。

## 成果物

- [dataset](../../datasets/pilot-v3.jsonl)／[監査](../../datasets/pilot-v3-audit.json)
- [登録プロトコル](MMIA-R007-protocol.md)
- [設定](../../configs/pilot-v3-core.json)
- [予測](../../results/MMIA-R007/core-seed-20260915/predictions.jsonl)／[集計](../../results/MMIA-R007/core-seed-20260915/summary.json)／[group解析](../../results/MMIA-R007/core-seed-20260915/group-analysis.json)

**English:** pilot-v3 contains 432 semantic groups and 1,296 multilingual rows across four two-skill paths. Intermediate and final targets are recomputed during audit. Core-only validation accuracy was 13/432 (3.01%, group-bootstrap 95% interval 1.39–4.86%); code-to-physics scored zero. This establishes a difficult floor but may be too low for comparison. A short mixed-LoRA pilot must first show that training moves accuracy away from the floor.

**简体中文：** pilot-v3包含四条双技能路径、432个语义组和1,296条多语言样本，审计时重新计算中间值与最终值。Core-only验证正确率为13/432（3.01%，语义组bootstrap 95%区间1.39%–4.86%），其中code→physics为0。该结果形成了较难的基线，但也可能过低而无法比较。下一步先用短程混合LoRA确认训练能否使正确率脱离地板效应。
