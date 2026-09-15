# MMIA-R002：Mixed LoRA対4専門LoRA 3-seed結果

実施日：2026-09-15。事前登録した3 seed（20260915、20260916、20260917）で、rank 8 Mixed LoRA（C1）と、正解domain labelで選択する4つのrank 8専門LoRA（C2）を比較した。各seed・各条件はtrain全432行をちょうど1回処理した。testは未使用である。

## 主要結果

| seed | C1 Mixed | C2 Specialists | C2 − C1 |
| --- | ---: | ---: | ---: |
| 20260915 | 48.84% | 50.46% | +1.62pt |
| 20260916 | 44.21% | 47.69% | +3.47pt |
| 20260917 | 49.07% | 49.07% | 0.00pt |
| 3-seed平均 | 47.38% | 49.07% | **+1.70pt** |

3 seedで平均した各意味groupの対応差をbootstrapすると95%区間は**+0.08〜+3.40pt**であり、事前登録した品質条件「区間下限が0より大きい」をわずかに満たした。ただしseedと意味groupの両方を再標本化する階層bootstrapでは**−0.93〜+4.86pt**となり、学習順序の母集団に対する頑健な優位性は確認できない。

この差を実用上大きいとは評価しない。C2はactive Adapter容量をC1と同じに保つ一方、4倍の総Adapter容量を保存するため、+1.70ptが保存・配信・cache管理の追加費用を正当化するかは別途判断が必要である。

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

## 結論

MMIA-R002は、**既知domainによるoracle選択と、この限定dataset内では、専門Adapter分割に小さな品質上の利点があり得る**ことを示した。主要bootstrapは採択条件を満たすが、階層bootstrap、分野別一貫性、推論p95の再現性は十分でない。

したがって次の研究では、大規模な階層形成へ直ちに進まず、以下を先に行う。

- [Done] 3 seedのactive容量対照C1/C2を完了。
- [Next] rank 32 Mixed LoRA（C3）で4専門家の総容量に近い対照を測る。
- [Next] logicの寄与を除いた事前指定感度分析と、より情報量の高い論理課題を設計する。
- [Later] C2の利点が残る場合のみ、未知domainを選ぶrouter（MMIA-R003）を評価する。
- [Later] 常駐Core＋Adapter cacheでload、memory、p95を再測定する。

## 再現物

- [登録プロトコル](MMIA-R002-protocol.md)
- [3-seed集約JSON](../../results/MMIA-R002/aggregate-3-seeds.json)
- [seed 1詳細](MMIA-R002-seed-20260915-results.md)
- 各seedのimmutable manifest、stepログ、予測、解析は`results/MMIA-R002/seed-*`に保存した。

**English:** Across three registered seeds, oracle specialists averaged 49.07% versus 47.38% for mixed LoRA, a +1.70-point paired difference. The primary fixed-seed group bootstrap interval was +0.08 to +3.40 points, narrowly meeting the registered quality criterion. A hierarchical bootstrap over seeds and groups crossed zero (−0.93 to +4.86), coding regressed on average, and one seed exceeded the inference p95 limit. The result supports only a small, conditional specialization benefit. C3 and a stronger logic benchmark come next.

**简体中文：** 在三个已注册seed中，oracle专家组平均为49.07%，混合LoRA为47.38%，配对差值+1.70个百分点。固定seed的主要语义组bootstrap区间为+0.08至+3.40，勉强满足预注册质量条件；同时对seed和语义组进行层次bootstrap后区间跨越0（−0.93至+4.86），coding平均退化，且一个seed超过推理p95上限。因此结果只支持较小且有条件的专业化收益。下一步是C3和更有区分力的逻辑基准。
