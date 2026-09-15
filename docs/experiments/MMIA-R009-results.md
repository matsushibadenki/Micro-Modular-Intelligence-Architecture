# MMIA-R009：同一update予算の二段階通信 3-seed結果

実施日：2026-09-15。事前登録した3 seed（20260915、20260916、20260917）で、rank 8 end-to-end Adapter（B0）と、rank 8 Stage 1／Stage 2 Adapter（B1）を比較した。B0は432 update、B1は各Stage 216 updateの合計432 updateである。各Stageの学習例は`domain × difficulty × language`の36セルから6件ずつ選んだ。validation 432件を使用し、testは未使用である。

## 主要結果

| seed | B0 end-to-end | Stage 1 | teacher Stage 2 | B1 pipeline | B1 − B0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20260915 | 21.30% | 61.57% | 87.04% | 55.56% | +34.26pt |
| 20260916 | 15.05% | 59.72% | 88.19% | 53.01% | +37.96pt |
| 20260917 | 16.20% | 59.49% | 88.19% | 54.17% | +37.96pt |
| 平均 | **17.52%** | **60.26%** | **87.81%** | **54.24%** | **+36.73pt** |

seedごとの対応差を平均してsemantic groupをbootstrapした主解析の95%区間は**+30.02〜+43.44pt**だった。seedとsemantic groupの両方を再標本化する感度解析でも**+29.71〜+44.14pt**であり、学習順序の変化を含めても区間下限は0を大きく上回った。

結果は3 seedすべてで同方向だった。明示的な整数中間値による計算分割は、総optimizer updateを増やさずにend-to-end学習を上回った。

## 誤差境界

Stage 1平均は60.26%、teacher中間値を使うStage 2上限は87.81%、実pipelineは54.24%だった。Stage 1が正しいのに最終回答を誤った件数はseed順に26、29、24件で、誤った中間値から最終正解へ戻った例は全seedで0件だった。

この結果は、中間契約が性能を監査可能な二つの要因へ分離することも示す。上流の整数予測が第一の制約であり、正しい中間値を受けた後段にも約12%の改善余地がある。

## 学習費用

| 3-seed平均 | update | 入力token | 教師token | 学習時間 | Adapter本体 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 | 432 | 42,282 | 1,965 | 148.73秒 | 2,175,168 bytes |
| B1 Stage 1 | 216 | 17,168 | 820 | 74.53秒 | 2,175,168 bytes |
| B1 Stage 2 | 216 | 14,920 | 983 | 74.34秒 | 2,175,168 bytes |
| B1合計 | 432 | 32,088 | 1,803 | 148.87秒 | 4,350,336 bytes |

B1の入力tokenはB0の75.89%、教師tokenは91.76%だった。壁時計時間は平均でほぼ同じだが、後のseedほどマシン負荷による遅延が見られたため、時間差を構造上の優位性とは解釈しない。B1はAdapter保存量が2倍で、推論completionも2回必要である。

## 研究上の含意

MMIA-R009は、MicroModel階層化の価値が単なる専門Adapterの分割ではなく、**再利用可能で検査可能な中間契約に沿って計算を分割すること**にあるという証拠を強めた。R007の経路別専門化は同容量のmixed modelを上回らなかったが、R009の機能段階分割は全seedで大きく上回った。

この実験は静的に与えた二段階であり、会話で提案された自動的な`cluster → promote → distill`を直接検証してはいない。次は、同じ中間契約を繰り返し利用した履歴から昇格候補を検出し、compiled pathを蒸留する条件を定義する。

- [Done] 3 seedで総update一致比較を完了した。
- [Done] 主解析と階層bootstrap感度解析の区間下限が0を上回った。
- [Done] 実token、時間、保存量、二段階遅延、誤差伝播を記録した。
- [Next] 同一入力token対照を登録し、update数とtoken数の効果を分離する。
- [Next] Stage 1 curriculumを同一予算内で比較する。
- [Later] 利用履歴からの昇格候補検出と、上位Moduleへの蒸留を実装する。
- [Later] confidence低下時に下位pathへ展開するfallbackとdemotionを評価する。

## 成果物

- [集約JSON](../../results/MMIA-R009/aggregate.json)
- [プロトコル](MMIA-R009-protocol.md)
- [seed 20260915詳細](MMIA-R009-seed-20260915-results.md)
- `results/MMIA-R009/seed-20260916/`
- `results/MMIA-R009/seed-20260917/`

**English:** Across three registered seeds, the equal-update two-stage pipeline averaged 54.24% versus 17.52% for end-to-end training, a +36.73-point paired difference. The primary semantic-group bootstrap interval was +30.02 to +43.44 points; the hierarchical seed-and-group interval was +29.71 to +44.14. Both systems used 432 total optimizer updates, while the pipeline used 75.89% of the baseline input tokens. It stored two adapters and required two completions. The next experiment should match input-token budget and test whether repeated contracts can be promoted and distilled into a compiled upper module.

**简体中文：** 在三个预注册seed中，相同更新预算的两阶段pipeline平均达到54.24%，端到端训练为17.52%，配对差值为+36.73个百分点。主要语义组bootstrap区间为+30.02至+43.44；同时重采样seed和语义组的分层区间为+29.71至+44.14。两者总优化更新均为432次，而pipeline仅使用基线75.89%的输入token。其代价是保存两个Adapter并执行两次推理。下一实验应匹配输入token预算，并验证重复出现的中间契约能否晋升并蒸馏为编译后的上层模块。
