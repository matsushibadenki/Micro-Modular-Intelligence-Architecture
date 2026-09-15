# MMIA-R002 seed 20260915：Mixed LoRA対4専門LoRA

実施日：2026-09-15。登録済みMMIA-R002の第1 seedで、rank 8の単一Mixed LoRA（C1）と、正解domain labelで選ぶrank 8の4専門LoRA（C2）を比較した。testは使用していない。

## 学習予算の一致

| 条件 | Adapter数 | update | 入力token | 教師token | 学習時間 | lifetime peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 Mixed | 1 | 432 | 33,939 | 1,788 | 107.98秒 | 4.37 GB |
| C2 Specialists合計 | 4 | 432 | 33,939 | 1,788 | 123.72秒 | 各process最大3.84 GB |

C2はC1と同じtrain行を各1回処理し、updateとtokenを厳密に一致させた。C2の合計学習時間はC1より14.6%長い。全lossは有限で、各Adapterの可学習parameterは540,672である。C2の保存容量と総可学習容量はC1の4倍だが、1問でactiveになるAdapterは1個である。

## Validation品質

144意味group・432翻訳行をstrict integer exact matchで評価した。

| 指標 | C1 Mixed | C2 Oracle specialists | C2 − C1 |
| --- | ---: | ---: | ---: |
| translation macro accuracy | 48.84% | 50.46% | +1.62pt |
| 全3言語正解group率 | 43.75% | 47.22% | +3.47pt |
| format invalid | 1/432 | 0/432 | −1件 |
| paired group bootstrap 95% CI | — | — | −0.93〜+4.40pt |

第1 seedではC2の点推定が高いが、事前登録した品質条件「95%区間下限が0より大きい」は満たさない。残る2 seedを実行するまで採否を決めない。

| 分野 | C1 | C2 | 差 |
| --- | ---: | ---: | ---: |
| 数学 | 31.48% | 33.33% | +1.85pt |
| 物理 | 37.04% | 34.26% | −2.78pt |
| coding | 31.48% | 34.26% | +2.78pt |
| logic | 95.37% | 100.00% | +4.63pt |

改善は分野間で一貫しない。特にlogicは容易に飽和しており、専門化の一般的な根拠として強く数えられない。physicsの悪化は、分野分割によって他分野の整数演算例から得られる正の転移を失った可能性と整合するが、現時点では推測である。

## 推論費用

| 指標 | C1 | C2結合 | 比率 |
| --- | ---: | ---: | ---: |
| 完了時間p50 | 0.1906秒 | 0.2097秒 | 1.100倍 |
| 完了時間p95 | 0.2493秒 | 0.3041秒 | 1.220倍 |

両方とも事前登録上限1.25倍以内だった。C2は4つの独立processで各Adapterを評価したため、model loadは合計16.57秒、C1は3.94秒だった。これは常駐運用の1問推論時間へ含めていないが、低頻度利用では無視できない固定費である。実運用ではCore共有とAdapter cacheを実装して再測定する必要がある。

## 判定と次の工程

- [Done] C1/C2で同じ432 update・33,939入力token・1,788教師tokenを確認。
- [Done] oracle domainによるC2の432予測を欠落・重複・分野不一致検査後に結合。
- [Done] seed 20260915の品質・学習費用・推論時間を保存。
- [Next] seed 20260916と20260917を同じ登録条件で実行し、seedを考慮した推定を行う。
- [Later] C3 rank-32 Mixed LoRAで総容量対照を測定する。

## 再現物

- [登録プロトコル](MMIA-R002-protocol.md)
- [C1/C2比較JSON](../../results/MMIA-R002/seed-20260915/compare-specialists-vs-mixed.json)
- [C1 group解析](../../results/MMIA-R002/seed-20260915/analysis-mixed.json)／[C2 group解析](../../results/MMIA-R002/seed-20260915/analysis-specialists.json)
- [C2結合manifest](../../results/MMIA-R002/seed-20260915/eval-specialists/manifest.json)

**English:** In registered seed 20260915, oracle specialists scored 50.46% versus 48.84% for the mixed LoRA at an exactly matched 432-update and 33,939-input-token budget. The paired difference was +1.62 points, but its 95% bootstrap interval was −0.93 to +4.40, so this seed does not meet the quality criterion. Inference p50/p95 ratios were 1.10/1.22, within the 1.25 limit. Two registered seeds remain.

**简体中文：** 在已注册的seed 20260915中，oracle专家组在完全相同的432次更新和33,939个输入token预算下取得50.46%，混合LoRA为48.84%。配对差值为+1.62个百分点，但95% bootstrap区间为−0.93至+4.40，因此单个seed尚未满足质量条件。推理p50/p95比率为1.10/1.22，低于1.25上限。仍需完成另外两个已注册seed。
