# MMIA Research Roadmap

更新日：2026-09-11。

状態表記：

- [Done] implemented in the current codebase
- [Next] high-priority unfinished work
- [Later] planned, but not the closest next step

現時点では研究文書のみを確認している。以下の[Done]は文書の作成完了を示し、モデル実装・学習・性能実証の完了を意味しない。

| 状態 | 日本語 | English | 简体中文 | 完了条件 |
| --- | --- | --- | --- | --- |
| [Done] | 原設計に基づく研究レビュー作成 | Research review | 研究评估 | [レビュー](research-review-2026-09-11.md)に出典、設計課題、費用モデル、検証案を記載 |
| [Next] | モデル・環境と実験条件の確定 | Freeze pilot configuration | 确定试验配置 | model revision、依存版、precision、予算、評価分割、採否基準を固定 |
| [Next] | 最小評価基盤 MMIA-R001 | Minimal evaluation harness | 最小评估框架 | 三言語の人工問題、採点、Core実行、個別結果と資源ログを再実行可能にする |
| [Next] | 単一LoRA対専門LoRA MMIA-R002 | Single versus specialist adapters | 单适配器与专家适配器对比 | 総tokenを統制し、active容量・総容量の二対照を評価 |
| [Later] | request単位のroutingと合成 | Request routing and composition | 请求级路由与组合 | MMIA-R003〜R005で選択費用を含む改善を検証 |
| [Later] | 大きいDenseとの比較 | Larger dense baseline | 较大稠密模型基线 | MMIA-R006で品質条件付き費用比較 |
| [Later] | 安定知識・更新の比較 | Knowledge and update experiments | 知识与更新实验 | MMIA-R101〜R104でRAG、Memory、Hybridの回収条件を測定 |
| [Later] | Shared Workspace | Shared workspace | 共享工作空间 | 容量・計算対照と通信の介入実験で寄与を分離 |
| [Later] | 階層化・SSD cache | Hierarchy and SSD cache | 层次结构与SSD缓存 | まず常駐メモリが実測上の制約であることを確認 |
| [Later] | 独立モデル間通信 | Independent model communication | 独立模型通信 | Shared Core方式の結果を踏まえて別仮説として登録 |

技能系と知識系は独立した仮説として進める。各実験の実行後に状態を更新し、改善がない結果も保存する。
