# Dynamic Hierarchical Module Formation

追加日：2026-09-11。ユーザー提供の会話を、MMIAの追加研究テーマとして整理した設計案。実装・実験・追加の先行研究調査は未実施であり、効果や新規性を確定するものではない。

関連：[README](../readme.md)、[原設計](Micro-Modular-Intelligence-Architecture.md)、[研究レビュー](research-review-2026-09-11.md)、[ロードマップ](ROADMAP.md)。

## 1. 研究テーマと仮説H4

**MicroModel群の安定した連携を検出し、再利用可能な上位モジュールへ昇格させることで、経験に応じて計算構造自体を整理できるか。**

H4：品質条件を維持しながら、動的に形成した階層が、平坦なMicroMoEや固定階層より、構造検出・教師生成・蒸留・管理・フォールバック・更新を含む総コストを削減できる。

この過程を作業上「Hierarchical Neural Compilation」と呼ぶ。人間のチャンク化やコンパイラ最適化は着想を説明する類比であり、機構の同一性や性能を裏づける証拠とはしない。提供会話中のRISAについては仕様が本資料にないため、同一機構とは位置づけない。

## 2. 四つの段階

| 段階 | 操作 | 何が変わるか | 削減候補 |
| --- | --- | --- | --- |
| 1. 構造検出 | 頻出する順序・依存関係・役割分担を抽出 | 昇格候補ができる | この段階だけでは実行量は減らない |
| 2. マクロ化 | A→B→Cを仮想モジュールXとして登録 | 内部は元のモジュールを呼ぶ | 選択・調停の負担 |
| 3. 蒸留 | 元の経路を教師にXを学習 | 計算の一部または全体を学習済み処理へ置換 | 実行時間・計算量。ただし要実測 |
| 4. 再利用と再階層化 | Xを別の連携の構成要素として扱う | 上位の再利用構造が形成される | 再利用に伴う償却と計算短縮 |

例：`Physics → Math → Logic` を `Physics-Math Reasoner` としてマクロ化し、その後に蒸留する。「1,000回中800回」のような共起例は説明用であり、採用閾値や実測値ではない。

初期MMIAではXも共有Core上のAdapterまたはcontrollerとして実装する候補を優先する。独立したUpper Modelを必須としない。元のA/B/Cが同じCore forward内の分岐なら、「3モデルから1モデル」になってもCoreの計算が3分の1になるわけではない。実際のforward回数、分岐、token、通信を記録する。

## 3. 階層は意味上の抽象化

| Level | 役割の例 | 物理推論の例 |
| --- | --- | --- |
| 0 | primitive MicroModels | 加算、比較、単位変換、因果推定 |
| 1 | learned MicroMoE | 数式処理、物理量処理 |
| 2 | reusable functional modules | 力学推論 |
| 3 | abstract reasoning modules | 物理問題解決 |
| 4 | task/domain systems | 科学推論システム |

これは検証対象の例であり、各機能の難易度や規模が同じとは仮定しない。下位は具体的知識、中位は処理パターン、上位は抽象的関係を学ぶ分担を検証する。未知の値・entity・組み合わせへの転移評価で、特定回答の暗記と構造の学習を区別する。

上位ほど大きい必要はないが、小さくなる保証もない。初期は階層深度を一段追加する比較に限定し、`100→10→1` は将来像として扱う。複数の親による下位の共有を許す場合は木よりDAGが自然な候補となるため、循環依存を禁止し、展開深度と実行予算を制限する。

## 4. 昇格の判断

共起頻度だけでは、頻繁な誤動作まで固定する可能性がある。候補の検出と採用を分離する。

- **共起と構造安定性**：順序、入力条件、役割分担が複数の観測期間で再現するか。
- **性能寄与**：構成要素を外す介入や平坦な対照と比べ、品質へ寄与するか。
- **計算削減**：選択、実行、ロード、検証、fallbackを含む実コストが下がるか。
- **再利用率**：異なる問題群や期間で利用されるか。同一入力の反復だけなら回答cacheも対照とする。
- **干渉率・重複**：関連する課題の劣化と、既存上位モジュールとの役割重複を測る。

会話中の `reuse_frequency × latency_saved × accuracy_gain` は着想用のheuristicとする。精度が同等で遅延だけ改善する候補を排除しないため、実験では品質を制約、総費用を目的として分離する。

更新までの予測利用回数をN、元経路の平均費用をC_base、上位経路をC_fast、fallback率をp、追加の展開費用をC_expandとする。

```text
C_promoted = C_gate + C_fast + p × C_expand
NetSaving = N × (C_base - C_promoted)
            - C_discovery - C_teacher - C_distill - C_validation
            - C_management - C_update
```

これは上位を実行してからfallbackする場合の概算である。事前gateで直接下位へ送る場合は経路ごとの費用を別に集計する。秒・J・金額はそれぞれ別計算とする。利用回数やfallback率の見積もり誤差も含めて検証する。

品質非劣性、正の純節約、メモリ上限、干渉の許容範囲を全て満たす候補だけを採用する。閾値はpilot後に登録し、test結果から変更しない。重複が高い場合は新規追加だけでなく、既存候補の再利用・置換・採用見送りを比較する。

## 5. 下位保持と動的な再編

上位Xと、その教師となった下位A/B/Cのversionを保持する。通常は高速経路Xを使用し、信頼度不足・例外・未知問題では下位経路へ展開する。ただしconfidenceが正確とは仮定せず、held-out校正、誤答率と回答率、未知分布の評価、検証器の費用を測定する。下位経路にも正解の保証はない。

| 操作 | 定義 |
| --- | --- |
| promote | 下位連携を上位の呼び出し単位として採用する。重み統合は必須ではない |
| demote | 上位経路を既定の選択から外し、下位経路へ戻す。即時削除はしない |
| merge | 複数の役割・構造を統合する。重みmergeを行う場合は別の検証が必要 |
| split | 広すぎる／干渉する役割を分ける。失われた元モデルの自動復元を意味しない |

降格条件の候補は、再利用率低下、品質条件違反、fallback増加、更新後の構造変化、純節約の消失。昇格と降格に異なる閾値・最低観測期間を設け、行き来する費用も測る。下位の更新は依存する上位を再検証待ちにし、古い上位による回答の残存を記録する。

上位数、総保存容量、常駐容量、最大深度、蒸留予算を制約する。元経路を保持する費用も計上し、巨大な一枚岩や大量の重複moduleへ戻ることを防げるかを評価する。

## 6. 比較実験案

全て未実施。基礎評価と専門LoRAの実行履歴が得られた後に開始する。Workspaceや独立モデルの完成は必須条件としない。

| ID | 一つの問い | 比較 |
| --- | --- | --- |
| MMIA-R201 | 発見した構造をマクロ化する価値があるか | 平坦な同一モジュール群対発見マクロ。下位重み固定。発見費用も計上 |
| MMIA-R202 | 蒸留がマクロより安くなるか | 同じ候補のマクロ対蒸留X。同じ品質条件で教師生成・学習費用を償却 |
| MMIA-R203 | fallbackが品質と費用の関係を改善するか | 同じXのfallback有無。元の下位経路も診断対照として維持 |
| MMIA-R204 | 降格が分布変化に有効か | 同じ昇格済み構成に対して固定運用対降格あり。利用頻度・知識・処理パターンを変化 |
| MMIA-R205 | 学習した階層は手設計より有利か | 平坦構造、手設計固定階層、自動形成階層。同じ総資源・探索予算を記録 |
| MMIA-R206 | 再帰的な上位化が追加利益を生むか | 一段階対二段階。深度以外を可能な限り統制し、誤差伝播と総費用を測る |

分割は「候補発見・教師生成用」「閾値と構造選択用」「最終評価用」に分ける。翻訳された同一問題は英語・日本語・简体中文で同じsplitに置く。自己生成教師への一致だけで成功とせず、独立の正解・採点器で評価する。

品質、p50/p95遅延、総FLOPs、メモリ、純節約、回収問い合わせ数に加え、構造再利用率、干渉、fallback率、昇降格回数、更新後回復時間を記録する。費用を削減しない候補は採用せず、効果が不明な結果も残す。

## 7. 追加ログ

```text
module_id, version, abstraction_level, module_kind
child_module_versions, input_output_contract, dependency_graph
discovery_split_hash, trace_ids, pattern_frequency, observation_window
teacher_versions, distillation_data_hash, teacher_cost, training_cost
promotion_rule, validation_quality, measured_net_saving
fallback_rule, fallback_rate, expansion_cost
promotion_events, demotion_events, reason, replacement_module_id
```

module_kindはmacro／distilled adapter／independent model等を区別する。過去の実験を再実行できるよう、昇格時点の下位versionと設定を保存する。

## 8. English / 简体中文

**English:** This proposed fourth research theme studies stable cooperation patterns as reusable higher modules. Separate discovery, macros, distillation, and recursive reuse. Preserve lower paths, calibrate fallback, and evaluate demotion under drift. Compare flat, fixed, and learned hierarchies at matched quality, accounting for discovery, teacher generation, training, maintenance, and retained modules. No effectiveness or novelty has been demonstrated.

**简体中文：** 第四项研究主题将稳定协作模式转化为可复用上层模块，区分发现、宏封装、蒸馏和递归复用。保留下层路径，校准回退机制，并在分布变化时验证降级。在相同质量要求下比较平坦、固定和学习形成的层次结构，纳入发现、教师生成、训练、维护和保留下层模块的成本。目前尚未验证其效果或新颖性。
