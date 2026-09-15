# MMIA-R002：Mixed LoRA対4専門LoRA 3-seed結果

実施日：2026-09-15。事前登録した3 seed（20260915、20260916、20260917）で、rank 8 Mixed LoRA（C1）、正解domain labelで選択する4つのrank 8専門LoRA（C2）、rank 32 Mixed LoRA総容量対照（C3）を比較した。各seed・各条件はtrain全432行をちょうど1回処理した。testは未使用である。

## 主要結果

| seed | C1 Mixed | C2 Specialists | C2 − C1 |
| --- | ---: | ---: | ---: |
| 20260915 | 48.84% | 50.46% | +1.62pt |
| 20260916 | 44.21% | 47.69% | +3.47pt |
| 20260917 | 49.07% | 49.07% | 0.00pt |
| 3-seed平均 | 47.38% | 49.07% | **+1.70pt** |

3 seedで平均した各意味groupの対応差をbootstrapすると95%区間は**+0.08〜+3.40pt**であり、事前登録した品質条件「区間下限が0より大きい」をわずかに満たした。ただしseedと意味groupの両方を再標本化する階層bootstrapでは**−0.93〜+4.86pt**となり、学習順序の母集団に対する頑健な優位性は確認できない。

この差を実用上大きいとは評価しない。C2はactive Adapter容量をC1と同じに保つ一方、4倍の総Adapter容量を保存するため、+1.70ptが保存・配信・cache管理の追加費用を正当化するかは別途判断が必要である。

## 総容量対照C3

| seed | C1 rank 8 | C2 4 specialists | C3 rank 32 mixed |
| --- | ---: | ---: | ---: |
| 20260915 | 48.84% | 50.46% | **52.31%** |
| 20260916 | 44.21% | 47.69% | **49.31%** |
| 20260917 | 49.07% | 49.07% | **52.08%** |
| 3-seed平均 | 47.38% | 49.07% | **51.23%** |

C3はC1より平均+3.86pt高く、主要group bootstrapは+1.70〜+6.25pt、seedも再標本化する階層bootstrapも+0.77〜+6.79ptだった。C3は3 seedすべてでC1を上回った。

C2はC3より平均−2.16pt低かった。主要group bootstrapは−4.01〜−0.46ptでC3を支持し、階層bootstrapは−4.71〜+0.08ptで境界的だった。したがってC1に対するC2の小さな改善は、同じ総容量の単一Adapterを上回る専門分割効果ではない。

C2の4つの`adapter_model.safetensors`は合計8,700,672 byte、C3は8,663,400 byteで、重み保存量は近い。C3の可学習parameterは2,162,688で、rank 8 Adapter 4個の合計と一致する。

## 分野別平均

| 分野 | C1 | C2 | 差 |
| --- | ---: | ---: | ---: |
| 数学 | 30.86% | 33.02% | +2.16pt |
| 物理 | 33.95% | 34.88% | +0.93pt |
| coding | 30.86% | 29.01% | −1.85pt |
| logic | 93.83% | 99.38% | +5.56pt |

logicの改善が全体差の大部分を占めるが、この分野は二値で飽和に近い。数学・物理の改善はseed間で符号が変わり、codingは平均で悪化した。よって「専門化は全分野に一貫して有効」という仮説は支持されない。

## 学習費用

| seed | C1時間 | C2合計時間 | C2/C1 |
| --- | ---: | ---: | ---: |
| 20260915 | 107.98秒 | 123.72秒 | 1.146 |
| 20260916 | 108.06秒 | 107.32秒 | 0.993 |
| 20260917 | 150.10秒 | 105.50秒 | 0.703 |

すべての比較でC1/C2は432 update、入力33,939 token、教師1,788 tokenに一致した。第3 seedのC1時間は他のC1 runより約39%長く、共有計算機の負荷によるwall-time外れ値と考えられる。energyとFLOPsは未計測であり、wall timeだけから計算効率の優位性を主張しない。

## 推論費用

| seed | p50比 C2/C1 | p95比 C2/C1 | 1.25倍以内 |
| --- | ---: | ---: | --- |
| 20260915 | 1.10 | 1.22 | 達成 |
| 20260916 | 1.25 | 1.42 | 未達 |
| 20260917 | 0.96 | 1.03 | 達成 |
| seed中央値 | 1.10 | 1.22 | 達成 |

seed中央値は登録上限内だが、seed 20260916のp95は超過した。各専門家を独立processで読み込んだため、常駐Core＋Adapter cacheの運用形態とは異なる。レイテンシ条件は「中央値では達成、run単位では不安定」と判定する。

C3/C1の推論時間比はseed中央値でp50 1.12、p95 1.12だった。C3のp95はseed 20260915だけ1.30倍で、他は1.02倍と1.12倍だった。C2/C3もseedによってp50 0.86〜1.13、p95 0.92〜1.39と揺れ、現在の逐次CPU測定だけでは両者の小さい推論費用差を安定して順位付けできない。

## 結論

MMIA-R002は、**既知domainによるoracle選択でも、同じ総Adapter容量なら専門分割が単一Mixed Adapterを上回らない**ことを示した。C2は低active容量のC1より小さく改善したが、同じ総容量のC3が最も高精度だった。現条件では、保存・routing・cache管理を追加してC2を採用する根拠は弱い。

したがって次の研究では、大規模な階層形成へ直ちに進まず、以下を先に行う。

- [Done] 3 seedのactive容量対照C1/C2を完了。
- [Done] rank 32 Mixed LoRA（C3）を3 seed測定し、C1/C2を上回ることを確認。
- [Next] より情報量の高い論理課題と、複数技能を組み合わせる複合課題を別dataset IDで設計する。
- [Later] 新datasetでもC2の利点が残る場合のみ、未知domainを選ぶrouter（MMIA-R003）を評価する。
- [Later] 常駐Core＋Adapter cacheでload、memory、p95を再測定する。

## 再現物

- [登録プロトコル](MMIA-R002-protocol.md)
- [3-seed集約JSON](../../results/MMIA-R002/aggregate-3-seeds.json)
- [C3対C1集約JSON](../../results/MMIA-R002/aggregate-rank32-vs-rank8.json)／[C2対C3集約JSON](../../results/MMIA-R002/aggregate-specialists-vs-rank32.json)
- [seed 1詳細](MMIA-R002-seed-20260915-results.md)
- 各seedのimmutable manifest、stepログ、予測、解析は`results/MMIA-R002/seed-*`に保存した。

**English:** Across three registered seeds, rank-8 oracle specialists averaged 49.07%, rank-8 mixed LoRA 47.38%, and the equal-total-capacity rank-32 mixed control 51.23%. C3 beat C1 by +3.86 points with a hierarchical bootstrap interval of +0.77 to +6.79. C2 trailed C3 by 2.16 points. Under this benchmark, specialist partitioning does not beat a single mixed adapter with similar total trainable parameters and weight storage. A stronger logic and compositional benchmark comes next.

**简体中文：** 三个已注册seed中，rank-8 oracle专家组平均49.07%，rank-8混合LoRA为47.38%，相同总容量的rank-32混合对照C3为51.23%。C3比C1高+3.86个百分点，层次bootstrap区间为+0.77至+6.79；C2则比C3低2.16个百分点。在该基准下，专家分割未能超过具有相近总可训练参数和权重存储量的单一混合Adapter。下一步是更有区分力的逻辑与组合任务基准。
