# MMIA Research Roadmap

更新日：2026-09-13。

状態表記：

- [Done] implemented in the current codebase
- [Next] high-priority unfinished work
- [Later] planned, but not the closest next step

文書整備に加え、最小Core評価基盤と推論予備実験を完了した。[Done]は各行の範囲での完了を示す。専門学習・コスト削減・階層形成の実証はまだ完了していない。

| 状態 | 日本語 | English | 简体中文 | 完了条件 |
| --- | --- | --- | --- | --- |
| [Done] | 原設計に基づく研究レビュー作成 | Research review | 研究评估 | [レビュー](research-review-2026-09-11.md)に出典、設計課題、費用モデル、検証案を記載 |
| [Done] | 動的階層形成の研究設計 | Dynamic hierarchy proposal | 动态层次研究方案 | [追加設計](dynamic-hierarchical-module-formation.md)にH4、昇格・蒸留・降格と比較実験を記載。実装は未完了 |
| [Done] | 予備実験のモデル・環境と条件の確定 | Frozen pilot configuration | 固定预试验配置 | Qwen2.5-0.5Bのrevision、CPU float32、ライブラリ版、評価分割、採否基準を記録 |
| [Done] | 最小評価基盤 MMIA-R001 | Minimal evaluation harness | 最小评估框架 | [結果](experiments/MMIA-R001-results.md)：三言語24問を2回実行しtokenと採点が一致。6件の単体テスト合格 |
| [Done] | 学習比較用pilot-v2 | Dataset for training comparisons | 训练对比数据 | [MMIA-R001B結果](experiments/MMIA-R001B-results.md)：432意味問題、3言語1,296行。均衡・分割・target再計算を自動監査 |
| [Done] | pilot-v2 Core床効果 | Core-only floor on pilot-v2 | pilot-v2 Core基线 | 432 validation行を保存。strict 21.8%、group bootstrap区間と分野・言語・難易度別結果を記録 |
| [Done] | LoRA学習経路 MMIA-R002-P0 | LoRA training path | LoRA训练流程 | [結果](experiments/MMIA-R002-P0-results.md)：4 step、有限loss、540,672 trainable parameters、保存・再読込を確認 |
| [Next] | 学習環境と計測の固定 | Frozen training environment and profiling | 固定训练环境与计量 | 完全なlock、層化samplingの中規模pilot、学習時間・メモリ・token予算を確認 |
| [Next] | 単一LoRA対専門LoRA MMIA-R002 | Single versus specialist adapters | 单适配器与专家适配器对比 | [draft protocol](experiments/MMIA-R002-protocol.md)をpilot結果で確定し、3 seedでactive容量・総容量の二対照を評価 |
| [Later] | request単位のroutingと合成 | Request routing and composition | 请求级路由与组合 | MMIA-R003〜R005で選択費用を含む改善を検証 |
| [Later] | 大きいDenseとの比較 | Larger dense baseline | 较大稠密模型基线 | MMIA-R006で品質条件付き費用比較 |
| [Later] | 安定知識・更新の比較 | Knowledge and update experiments | 知识与更新实验 | MMIA-R101〜R104でRAG、Memory、Hybridの回収条件を測定 |
| [Later] | Shared Workspace | Shared workspace | 共享工作空间 | 容量・計算対照と通信の介入実験で寄与を分離 |
| [Later] | 構造検出・マクロ化・蒸留 | Discovery, macros, distillation | 结构发现、宏封装与蒸馏 | MMIA-R201〜R202で平坦構造と比較し、学習費用を含む純節約を測定 |
| [Later] | 展開・降格・再帰的昇格 | Fallback, demotion, recursive promotion | 回退、降级与递归晋升 | MMIA-R203〜R206で品質、分布変化、固定階層との比較、容量制約を検証 |
| [Later] | SSD cache | SSD cache | SSD缓存 | まず常駐メモリが実測上の制約であることを確認 |
| [Later] | 独立モデル間通信 | Independent model communication | 独立模型通信 | Shared Core方式の結果を踏まえて別仮説として登録 |

技能系と知識系は独立した仮説として進める。各実験の実行後に状態を更新し、改善がない結果も保存する。

動的階層形成は中心研究テーマの一つとし、評価基盤と連携履歴を前提に着手する。マクロ化・蒸留はWorkspaceや独立モデルの完成を待つ必要はない。
