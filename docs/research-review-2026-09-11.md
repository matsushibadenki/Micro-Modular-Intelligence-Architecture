# MMIA：学習・推論コスト削減の研究レビュー

調査日：2026-09-11。対象：[原設計書](Micro-Modular-Intelligence-Architecture.md)。

本レビュー後に追加した研究テーマH4は、[動的階層形成の研究設計](dynamic-hierarchical-module-formation.md)を参照してください。構造検出・マクロ化・蒸留・昇格・降格を扱います。この追加テーマの先行研究調査と実験は未実施です。

本書は一次資料の文献調査、設計の検討、実験計画である。学習・推論実験は未実施であり、性能改善を実証した報告ではない。原設計書は変更せず、本書を検証用の補足とする。文献は論文要旨と公開ページを中心に確認した。網羅的な系統レビュー、全論文の実装再現、新規性の確定は行っていない。

## 1. 結論

**Shared Core + 小型Adapterは、専門適応の学習・保存コストを下げる出発点として妥当。ただし、同じCoreへAdapterを追加してもCoreの推論計算は減らない。** 推論の低コスト化を実証するには、より大きなDenseモデルを代替する、入力コンテキストを短くする、生成や再試行を減らす、という具体的な節約経路が必要である。

初期研究の中心は「動的にネットワークを構成できるか」から、**どの要求品質・問い合わせ回数・更新頻度において、単一LoRA／Dense／RAGより総コストが低くなるか**へ絞ることを提案する。

優先する研究は次の二つ。

1. **技能研究**：混合データで学習した単一LoRAに対し、専門LoRAの選択が同じ計算予算で改善するか。
2. **知識研究**：安定した人工知識について、学習費用を含めてもParametric MemoryがRAGより安くなる利用条件はあるか。

Workspace、階層化、SSD配信は、この二つから独立した後続実験とする。H1が不成立でもH3が不成立とは限らないため、知識研究をWorkspace成功の後まで待たせる必要はない。

### English summary

Shared-backbone adapters are a reasonable starting point for reducing adaptation and storage costs. They do not remove backbone inference computation. Separate specialization experiments from knowledge-memory experiments, and compare against a mixed-task single adapter and strong retrieval baselines. Measure end-to-end cost, including training, routing, loading, updates, and retries, at a predefined quality threshold. No model experiments have been run; the thresholds below are proposed acceptance criteria.

### 简体中文摘要

共享主干加小型适配器适合降低任务适配与存储成本，但不会自动减少主干的推理计算。建议将专业能力实验与知识记忆实验分开，分别对比混合任务单适配器和较强的检索基线。在预先确定的质量要求下，统计训练、路由、加载、更新及重试的完整成本。目前尚未运行模型实验；下文数值是建议的验收标准，并非实测结果。

## 2. 先行研究との対応

論文で報告された成果は、その論文のモデル・データ・ハードウェア条件での結果であり、MMIAやMacBookでの再現を意味しない。

| 原設計の要素 | 確認した一次資料 | 本研究への含意 |
| --- | --- | --- |
| Frozen Core + LoRA | [LoRA, 2021](https://arxiv.org/abs/2106.09685) | 学習対象削減の根拠。小さい学習対象と小さい推論計算は区別する |
| 疎なExpert選択 | [Switch Transformers, 2021](https://arxiv.org/abs/2101.03961) | 既存の疎計算研究。FFN置換型と、DenseにAdapterを追加する方式は別物 |
| Expertが自分で選択 | [Expert Choice Routing, 2022](https://arxiv.org/abs/2202.09368) | Expert側選択には先行例がある。バッチ内token選択とオンライン自己活性は区別 |
| LoRA動的合成 | [LoraHub, 2023／COLM 2024](https://arxiv.org/abs/2307.13269) | 合成自体を新規性としない。入力単位の動的合成にも[2024年の研究](https://aclanthology.org/2024.findings-emnlp.326/)がある |
| Module間Workspace | [Shared Global Workspace, 2021](https://arxiv.org/abs/2103.01197) | 帯域制約付き共有通信に先行例。小型言語モデルで費用対効果が出るかが検証点 |
| 合成時の干渉 | [TIES-Merging, 2023](https://arxiv.org/abs/2306.01708) | 重み合成には符号などの干渉がある。単純和だけで合成の限界を判断しない |
| 知識の学習と検索 | [Fine-Tuning or Retrieval?, 2023／EMNLP 2024](https://arxiv.org/abs/2312.05934) | この比較ではRAGが教師なし追加学習を上回る。QAによる教師あり学習まで一括否定する根拠ではない |
| 新知識のmulti-hop | [Fine-Tuning vs. RAG, 2026-01](https://arxiv.org/abs/2601.07054) | 要旨ではSFTが最高精度、RAGが新知識で改善と報告。7Bの結果を0.5Bへ外挿しない |
| 潜在表現の外部記憶 | [Memorizing Transformers, 2022](https://arxiv.org/abs/2203.08913) | latent memoryは必ずしもparametricではない。重みに保存する方式と検索メモリを区別 |
| Expert offloading | [Fast Inference with Offloading, 2023](https://arxiv.org/abs/2312.17238) | 配信・キャッシュにも先行研究。大きなMoEの知見を小型LoRAへ直接適用しない |
| 階層ごとのLoRA連携 | [HotMoE, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/40383) | Expert間関係と層別routingも既存の研究対象 |
| 費用対効果に基づく起動 | [Value-of-Information Routing, 2026-08](https://arxiv.org/abs/2608.02528) | 不確実性と追加Expertの利益を区別する直近のプレプリント。要旨の理論・評価計画を実測の優位性と扱わない |

**新規性候補は構成部品の組み合わせだけでは弱い。** 小型Coreで、更新・通信・読み込み費用まで含めた採用可能領域と失敗領域を示すこと、未知の技能組み合わせで改善する条件を再現可能に示すことを研究貢献の候補とする。これは本調査からの提案であり、未発見の先行研究がないという主張ではない。

## 3. 原設計で明確にしたい点

### 3.1 学習対象パラメータと推論計算

LoRAの線形層を `y = Wx + BAx` とする。Wが `d_out × d_in`、rankがrなら、追加学習パラメータは `r(d_in + d_out)`。乗算と加算を各1 FLOPと数える近似では、1 tokenの追加計算は `2r(d_in + d_out)` となる。元のWの計算は残る。

同じCore、同じtoken列、同じ実装条件なら、未mergeのAdapter追加でCore計算が減るとはいえない。静的に `W' = W + BA` へmergeすれば線形層の形は元に戻るが、merge作業・保存・切り替えの費用は別に発生する。量子化時は再量子化や精度差も評価対象とする。

学習でもFrozenは「逆伝播が全部不要」という意味ではない。途中層のAdapterを学習するには、凍結層を通る入力方向の勾配計算や活性保持が必要になる。学習対象数の削減率を、そのまま学習時間削減率に変換しない。

### 3.2 「Soft Routing」を実装単位で定義する

| 方式 | 何を混ぜるか | 注意点 |
| --- | --- | --- |
| 層内LoRA出力和 | 同じxへの `Σ α_i B_i A_i x` | Core一回に追加分岐の費用。初期のSoft方式として採用 |
| 重み合成 | `W + Σ α_i B_i A_i` | 係数を固定できる区間とmerge費用を記録 |
| モデル出力ensemble | 完成した複数モデルのlogit等 | Coreを複数回実行する費用。上の二つと同じ名称にしない |

同じ入力の同じ線形層で係数が固定されていれば、最初の二つは代数的に対応する。しかしネットワーク全体の出力平均とは一般に等価ではない。また、`(Σ B_i)(Σ A_i)` は交差項を含み、`Σ B_i A_i` ではない。rank連結は和を表現できる一方、rankと実行費用が増える。

原設計のHard Routingも「request単位のLoRA選択」と「token単位のFFN置換MoE」を区別する。最初は前者とし、後者の比較実装を完了したかのように記録しない。

### 3.3 Self Activationでも選択コストは存在する

`score_i = f_i(h)` をまとめれば、数学的にはgating関数になる。中央Routerがないこと自体は計算削減の証明にならない。全Expertの本体を実行してからconfidenceを求めると、疎実行の利点を失う。

初期案は常駐する小型score headのみを評価し、起動数に上限を設ける方式。requestごとに0／1／2個を選び、0個ならCoreのみで回答する。promptの表現を得るために追加のCore forwardが必要なら、その費用を含める。prefix計算を再利用できる設計かも明記する。

原設計の `relevance × confidence / cost` は未校正のheuristicである。まず同じ特徴量・学習予算の中央gateと比較する。発展案は「追加Expertによる期待損失減少／追加費用」だが、上記2026年のValue-of-Information研究と重なるため独自発明とは扱わない。期待利益の教師データを作る全Expert評価も研究費に含める。

### 3.4 Workspaceは学習可能な通信契約が必要

同じCoreから派生していても、専門Adapterが同じslotの意味を共有する保証はない。read/writeの射影、挿入層、学習損失、更新順、反復上限を指定する。Frozen Coreへ任意のlatentを渡して自然に理解されるとは仮定しない。

全対全通信の辺は概ねN²、固定S個のslotを介した通信はNSだが、これは通信構造の比較である。直列チェーンの辺はN程度なので「共有方式は常に安い」とはならない。Coreの再実行回数、投影、attention、反復も測定する。

採用時は「同じ追加パラメータ数のMLP」「同じ計算量の反復」「Workspaceをzero／shuffleする介入」と比較し、単なる容量追加や追加計算との違いを確かめる。因果言語モデルでは未来tokenへのアクセスを禁止する。

### 3.5 人工知識でも漏洩対策は必要

ランダムなentity IDとrelation割当で既知事実への依存を減らせる。しかし同じQAテンプレートや回答を分割間に流すと、記憶と汎化を取り違える。

知識は学習用文章とRAGコーパスの双方へ同じ内容を渡す。評価質問は別に生成する。「事実を学んだうえで未見の言い換えへ回答」と「一度も与えていない事実」は別の評価であり、後者は不明回答の対象となる。

## 4. コストモデル

主要な判定は、**事前に定めた品質条件を満たす候補の中で最小の総コスト**とする。QAFなどの比率は補助指標とする。低品質でも安い方式が比率だけで勝つことを防ぐためである。

```text
C_total(N, U)
  = C_prepare + C_train + C_index
  + Σ(u=1..U) C_update(u)
  + Σ(q=1..N) C_query(q)

C_query
  = C_route + C_load + C_retrieve + C_prefill
  + C_decode + C_workspace + C_verify + C_retry
```

費用はそれぞれ秒、J、金額で別々に算出し、異なる単位を加算しない。共通Coreの事前学習は両方式で固定して条件付き比較とする。ゼロからの事前学習まで安くなったとは結論しない。蒸留やLLMによるデータ生成を追加した場合は教師の費用も含める。

### Parametric Memoryの損益分岐点

更新なしの簡略モデルで、Pをparametric、RをRAGとする。

```text
N* = (C_prepare,P + C_train,P - C_prepare,R - C_index,R)
     / (C_query,R - C_query,P)
```

分母が正ならN*を超えて初期費用を回収できる可能性がある。分母が0以下なら問い合わせを増やしても推論側の節約で回収できない。初期差が負の場合は一般式の不等式を直接確認する。頻繁な更新では更新費用を分子へ加え、次回更新までの問い合わせ数と比較する。

**算術例のみ、実測ではない**：初期追加費用3,600秒、1問あたり0.1秒短縮なら36,000問で同額になる。更新までに1,000問しか使わない知識では回収できない。この計算はJや金額の節約を示すものではない。

### 記録する資源

- Core、Router、選択Adapterを含む演算量。全token・全反復を積算し、推定方法を記録する。
- 学習対象数、保存総パラメータ数、1 forwardの有効パラメータ数を分離する。
- 実メモリのpeak、重み、KV cache、optimizer、活性、Expert cache、I/O量。
- TTFTと完了時間のp50／p95、生成token数、再試行、timeoutと失敗率。
- warm実行とアプリ側cacheが空の実行。OS page cacheの状態は別に記録し、真のSSD coldと混同しない。
- 電力を測れる場合は測定範囲・サンプリング・idle差引きを記録する。未計測はnullとし、時間からJを創作しない。

25Mパラメータは16-bit重みだけで約50MB（10進）であり、25MBではない。4-bitの理想payloadは約12.5MBだがmetadataや作業領域は別。Unified Memoryの共有量をCPU分とGPU分で二重計上しない。Macの実行可否は重み容量だけでは判断せず、実際の環境で短いpilotを行う。

## 5. 反証可能な実験計画

以下は全て**未実施の提案**。IDは原設計の例と衝突しないよう `MMIA-R001` から開始する。pilot結果を見て本試験の条件を確定し、その後testを開封する。testを見て変更した仮説は別IDで扱う。

### 共通プロトコル

Coreは原設計の0.5〜1.5B範囲の一つで開始し、model revision、tokenizer、license、precision、backendを固定する。具体的モデル選定と依存版の互換性確認は実装前の作業として残す。初回から複数backendを開発しない。

数学・物理・コード・形式論理は決定的な採点器を用意し、容易すぎる問題だけで構成しない。混合問題には「式の構築と数値計算」「条件推論とコード生成」のような未見の組み合わせを含める。コード評価は外部ネットワークなし・時間上限付き隔離環境で実行する。

英語・日本語・简体中文は同じ意味の問題から作り、翻訳違いを同一groupにまとめて分割する。言語別精度・token数・時間を報告し、単なる翻訳差を専門化効果と誤認しない。データ生成の増加費用も記録する。

品質比較とシステム比較を分ける。品質比較は同じdecode条件・最大出力長で実施し、長さ上限到達も失敗として残す。システム比較では固定長token列の計測も併記して、早く誤答した方式が速く見える問題を分離する。

学習は3 seedから開始。世界の生成seedと学習seedを別に管理する。domain別とmacro平均を記録し、意味的に関連する質問群単位でpaired bootstrapの95%区間を求める。3 seedだけで一般化を保証しない。pilotで分散を見積もり、3〜5ptの差を検出する本試験件数をtest閲覧前に決める。多数のrank・gate探索はvalidationのみで行い、確認実験を分ける。

### 技能研究

| ID | 一つの問い | 比較と固定条件 | 次へ進む判断 |
| --- | --- | --- | --- |
| MMIA-R001 | 評価・計測系は再実行可能か | Coreのみ。同じ入力・seed・出力を保存。非同期処理完了後に時間測定 | 評価器、失敗記録、資源ログが揃う。速度変動を説明できる |
| MMIA-R002 | 分割そのものに価値があるか | 混合単一LoRA対4専門LoRA＋既知のdomain選択。総学習tokenを揃える | validationで専門化の利益が確認できる。domain選択は診断用で実運用精度ではない |
| MMIA-R003 | 学習gateで利益を維持できるか | R002の専門LoRAを固定し、domain選択をrequest top-1 gateへ変更 | gate費用を含め、単一LoRAに対する品質・コスト条件を満たす |
| MMIA-R004 | 2専門家合成は追加費用に見合うか | R003に対し、同じCore内のtop-2 LoRA出力和だけを変更 | 複合問題の改善が追加計算に見合う |
| MMIA-R005 | 自己活性が中央gateより有利か | 同じ特徴量と起動予算でgate方式のみ変更 | 総費用でPareto改善。全Expert発火を監視 |
| MMIA-R006 | 大きいDenseを代替できるか | 選抜MMIA対より大きいDense。品質条件と実行環境を揃える | 同等品質で実測コスト減。小Core単体も残す |

単一LoRAの対照は二種類必要である。

- **active容量を揃える対照**：各専門家と同じrankの単一LoRA。選択実行の比較になるが、専門家群の総容量は大きい。
- **総学習容量を揃える対照**：4専門家分に対応する大きいrankの単一LoRA。保存容量を揃えられるが、実行量は異なる。

両者を混ぜずに報告する。rankは最初8／16／32程度の小さい探索案とし、実パラメータ数は挿入層の形状から算出する。1M〜100Mの全範囲を最初から探索しない。全パラメータfine-tuningはpilotで予算内と判定された場合の追加対照であり、未実施なら優越性を主張しない。

### 知識研究

| ID | 一つの問い | 条件 | 判定 |
| --- | --- | --- | --- |
| MMIA-R101 | 安定知識の重み記憶に費用上の利点があるか | Core／RAG／Memory LoRA。同じ約1,000事実、未見言い換えQA | 精度非劣性と総費用の損益分岐点 |
| MMIA-R102 | 未見の関係合成に対応できるか | R101のモデルを固定。既知の辺から作る未見multi-hop質問 | 記憶単独、検索失敗、推論失敗を区別 |
| MMIA-R103 | 更新後も費用の利点が残るか | 事実の1%／10%を変更し各方式を更新。変更されない事実も評価 | 新知識精度、旧値回答、忘却、更新費用 |
| MMIA-R104 | Hybridが最良単独方式を改善するか | MemoryとRAGの切替ルールのみ追加。validationで閾値を固定 | 検索・校正・fallbackを含む費用と品質 |

RAGは弱いvector検索だけに限定しない。少なくともlexical検索、dense検索、validationで選抜するhybridを比較し、multi-hopでは必要に応じて複数回検索の予算を与える。必要な根拠を全て含むoracle contextを診断用に用意し、検索とCoreの限界を分ける。人工関係データにはkey-value／graph lookup＋Coreも実用対照として置く。

Memory側だけに大量の合成QAを与える場合、その効果には教材変換が含まれる。対照として同じQAで調整したCore＋RAGを追加し、知識格納先の効果と学習教材の効果を分離する。QA数だけでなく総token、生成費用、探索予算を記録する。

更新評価は、変更事実・未変更事実・新規追加事実・不明事実を分ける。忘却率は「更新前に正解だった未変更質問のうち、更新後に不正解になった割合」と定義し、分母も保存する。出典IDの生成正解率と、実際に取得した根拠が回答を支える割合は別指標とする。Adapterへ出典文字列を覚えさせただけでは検索と同じ追跡性を保証しない。

知識規模は1,000→10,000→100,000事実と段階化し、小規模で品質と費用の見通しがつくまで拡大しない。

## 6. 成功・停止基準の提案

以下の数値は原設計を具体化した**目標値**であり、実測成果ではない。

| 対象 | 本試験前に固定する基準案 |
| --- | --- |
| 技能・計算固定 | 総推論FLOPsを±5%以内に合わせ、macro accuracy +5ptを目標。差の95%区間が0を上回ることも確認 |
| 技能・品質固定 | accuracy差の95%区間下限が−1pt以上で、主要コストを30%以上削減。主要コストをFLOPs／時間／Jから事前指定 |
| 知識 | RAGとのaccuracy差の95%区間下限が−3pt以上で、文脈token70%削減または完了時間30%削減 |
| 実用性 | 上記の品質条件に加え、想定更新期間の問い合わせ数で初期・更新費用を回収できる |

文脈token減少だけで総費用削減の成功とはしない。p95遅延、各domain・言語の劣化も別に点検する。検出力不足なら「不明」とし、差がないと断定しない。

R002で専門家に選択上の有利な条件を与えても単一LoRAに勝てない場合、RouterやWorkspaceを複雑化する前に、データ品質・Core能力・rank不足を調べる。事前に定めた限定的な追加試験後も改善しなければ、その条件での技能分割を停止する。R101で初期費用を回収できない場合は、頻度の高い安定知識に対象を絞るか、検索方式を採用する。

## 7. 研究ログの最低契約

原設計の項目へ次を追加する。

```text
status: planned | running | completed | failed | inconclusive
hypothesis_registered_at, primary_metric, acceptance_rule
source_hash, git_commit (Git未初期化ならnull)
model_revision, tokenizer_revision, dataset_hash, split_group_key
world_seed, training_seed, language, domain
backend_versions, hardware, precision, batch_size
input_tokens, output_tokens, truncation_count
train_tokens_total, data_generation_cost, tuning_cost
router_time, load_time, retrieval_time, prefill_time, decode_time
peak_memory_bytes, memory_measurement_method
estimated_flops, flops_estimation_method
energy_joules (未計測ならnull), energy_measurement_method
per_example_predictions, failures, paired_quality_interval
interpretation, next_experiment_id
```

負の結果はcompletedとして保存する。OOMや依存関係エラーはfailedであり、仮説が反証されたこととは違う。統計的に判断できなければinconclusiveとする。原設計の `results/failed/` だけに否定結果をまとめず、全試行をIDで追跡する。

## 8. 推奨する次の成果物

直近はモデルの大規模実装ではなく、**MMIA-R001を完了できる最小Research Harness**とする。決定的な人工問題生成、三言語の分割、評価器、Coreのみの実行、per-example JSONL、時間・メモリ計測までを一つの工程にする。その次に混合単一LoRAと専門LoRAの比較へ進む。

後続の改善案は、利用頻度と更新頻度に応じて知識をAdapterまたは検索側へ配置する方式である。人気のある安定知識だけを重みに移し、低頻度・頻繁更新の知識は外部に残す。ただし配置判定と再学習の費用を含め、全件RAGや固定配置を対照にする。これは現時点では検証前の提案である。

ローカル実験の段階ではVPSやDB基盤は不要。分散実験・共有結果管理が必要になった時点で、研究費用に基盤運用費も含めて構成を決める。
