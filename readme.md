# Micro Modular Intelligence Architecture（MMIA）

**マイクロモデルの専門化・動的連携・知識記憶・動的階層形成による、AIの学習・推論コスト削減に関する研究。**

[日本語](#日本語) · [English](#english) · [简体中文](#简体中文)

## 日本語

### 研究テーマ

必要な能力だけを選択して動作させるモジュール型AIによって、回答品質を維持しながら、学習・推論・知識更新に必要な総コストを削減できるかを研究します。

初期段階では、マイクロモデルを独立した小型LLMとして実装するのではなく、**共有する小型Coreモデルと、専門能力を学習したLoRA／Adapter**で構成します。この構成を検証した後に、共有メモリを介した連携や独立モデル間の通信を検討します。

### 研究目的

- 専門能力の獲得・追加・更新に必要な学習時間とメモリを減らす。
- 必要な専門モジュールだけを起動し、同等の品質を得るための推論費用を減らす。
- 安定した知識を小型モジュールの重みに保存し、検索拡張生成（RAG）と比較する。
- 連携や読み込みの負担も含め、モジュール化が有利になる条件と不利になる条件を明らかにする。

**学習対象パラメータの削減は、そのまま推論計算の削減を意味しません。** Coreの計算は残るため、より大きなDenseモデルの代替や入力文脈の短縮など、実際の節約経路を検証します。

### 研究内容

| 研究項目 | 検証する内容 |
| --- | --- |
| 専門モジュール | 数学・物理・プログラミング・形式論理を小型Adapterへ学習させ、混合データで学習した単一LoRAと比較する |
| 動的選択・合成 | Hard Routing、Soft Composition、Self Activationを比較し、選択費用と専門家同士の干渉を測る |
| Parametric Memory | 人工的な事実をAdapterへ学習させ、RAGと精度・遅延・文脈長・学習費用を比較する |
| 知識更新 | 事実の変更・追加に対する更新時間、古い回答の残存、無関係な知識の忘却を測る |
| Shared Workspace | 小さな共有潜在メモリを介した連携が、追加計算に見合う改善を生むかを検証する |
| 動的階層形成 | 安定したMicroMoEの連携を検出し、マクロ化・蒸留・上位モジュールへの昇格と降格によって計算構造を再編する |
| 拡張性 | モジュールの階層化、SSDからの読み込み、キャッシュ、独立モデル間通信を段階的に検討する |

### 主要な研究仮説

1. **専門化の効果**：共有Coreと専門Adapterの組み合わせは、単一LoRAやDenseモデルより、品質とコストの関係を改善できるか。
2. **連携方式の効果**：自己活性や複数Adapterの合成は、中央Routerによる選択より有利になるか。
3. **知識記憶の効果**：安定した知識では、Parametric MemoryがRAGに近い品質を維持し、学習・更新費用を含めても安くなるか。
4. **動的階層形成の効果**：繰り返されるMicroModel群の連携を上位モジュールへ昇格させることで、蒸留・管理・フォールバック費用を含めても総コストを削減できるか。

これらは検証前の仮説です。RAGの完全置換は目的とせず、検索と重みへの記憶を使い分ける条件も調べます。

### 動的階層形成：Dynamic Hierarchical Module Formation

MicroModelのネットワークからMicroMoEを形成し、安定した役割分担や処理パターンを再利用可能な上位モジュールへ昇格させます。**経験から計算構造そのものを整理する仕組み**を研究の中心テーマの一つとして扱います。

```text
連携履歴 → 構造検出 → マクロ化 → 蒸留 → 上位モジュール化
                          ↑                    │
                          └── 降格・再展開 ────┘
```

例えば `Physics → Math → Logic` が安定して使われる場合、まず下位モジュールを呼び出す仮想マクロとして登録します。その後、処理結果を教師として上位モジュールXへ蒸留し、品質を維持して計算を短縮できるかを測ります。マクロ化だけでは下位の計算は消えず、蒸留後も呼び出し回数の減少だけで高速化を判断しません。

昇格候補は共起頻度だけでなく、性能寄与、計算削減、再利用率、干渉率から評価します。下位モジュールは保持し、低信頼・例外・未知問題では元の経路へ展開します。利用減少、精度低下、処理パターン変化に応じた降格も検証し、`merge / split / promote / demote` を区別して扱います。

階層例は `primitive MicroModels → learned MicroMoE → reusable functional modules → abstract reasoning modules → task/domain systems` です。下位は具体的知識、中位は処理パターン、上位は抽象的関係を学ぶ分担を仮説とします。上位ほど大きくする必要はなく、容量と階層深度に上限を設けます。この流れを作業上 **Hierarchical Neural Compilation** と呼びますが、名称の新規性や効果は未検証です。

詳細は[動的階層形成の研究設計](docs/dynamic-hierarchical-module-formation.md)を参照してください。

### 研究の進め方

最初に評価・計測基盤を整備し、「技能の専門化」と「知識の保存・更新」を別の実験系として進めます。初期Coreは0.5〜1.5B程度を候補とし、実行環境で小規模な試験を行ってモデルと設定を決めます。

各実験は一つの仮説を対象とし、比較条件・評価指標・採否基準を事前に記録します。人工知識と未見の質問を使い、学習データの漏洩を防ぎます。評価は英語・日本語・简体中文で行い、言語別の結果を記録します。

主な評価軸は、正答率・複合問題への対応、学習時間、総推論計算量、初回tokenまでの時間、回答完了時間、最大メモリ使用量、更新費用です。エネルギーは測定可能な場合に記録します。学習・検索・選択・読み込み・再試行まで含め、**必要な品質を満たす条件での総コスト**を比較します。

### 現在の進捗

- [Done] 研究設計書と文献調査に基づく研究レビューを文書化。
- [Done] 比較実験、コストモデル、採否基準、ロードマップを整理。
- [Done] 動的階層形成・昇格・蒸留・降格の研究テーマと検証計画を文書化。
- [Done] 最小評価基盤とMMIA-R001予備実験。CPUで24問を2回実行し、全token・採点の一致と標準generateとの一致を確認。
- [Done] pilot-v2を1,296行で作成し、均衡・分割・正解を自動監査。Core床効果はstrict 94/432（21.8%）。
- [Done] 4 stepのLoRA学習・保存・再読込を確認。学習対象は540,672 parameter、Adapter重みは約2.1MB。
- [Done] 層化72 stepの混合LoRAを18.98秒で学習。探索validationはstrict 21.8%から41.2%。
- [Next] 同じ学習予算で混合LoRAと4専門LoRAを3 seed比較。
- [Next] 混合単一LoRAと専門LoRA群の比較実験。
- [Later] 動的連携、知識記憶・更新、Workspace、階層化、SSD配信、独立モデル間通信。
- [Later] 連携履歴に基づくマクロ化、上位モジュールへの蒸留、フォールバックと降格の比較実験。

現在は最小評価基盤、pilot-v2、Core床効果、層化72 stepの混合LoRA探索評価まで実装しています。strict validationはCoreの94/432行（21.8%）から混合LoRAの178/432行（41.2%）へ改善しました。1 seedの探索結果であり、専門LoRAとの本比較、RAG比較、昇格機構は未実装です。コスト削減効果は未検証です。

[実行方法](docs/harness-usage.md)と[予備実験結果](docs/experiments/MMIA-R001-results.md)を参照してください。

### 関連文書

- [研究設計書](docs/Micro-Modular-Intelligence-Architecture.md)：全体構想と研究仮説。
- [研究レビュー](docs/research-review-2026-09-11.md)：先行研究の出典、設計課題、コストモデル、実験計画。
- [動的階層形成の研究設計](docs/dynamic-hierarchical-module-formation.md)：MicroMoEの構造検出・昇格・蒸留・降格。
- [ロードマップ](docs/ROADMAP.md)：実装・検証の優先順位と完了条件。
- [MMIA-R001結果](docs/experiments/MMIA-R001-results.md)：初回のCore評価、再現性検証、失敗記録、次の課題。
- [MMIA-R001B結果](docs/experiments/MMIA-R001B-results.md)：pilot-v2の監査、Core床効果、分野・言語・難易度別結果。
- [MMIA-R002プロトコル](docs/experiments/MMIA-R002-protocol.md)：単一LoRAと4専門LoRAの比較条件。
- [MMIA-R002-P0結果](docs/experiments/MMIA-R002-P0-results.md)：LoRA学習・保存・再読込のsmoke test。
- [MMIA-R002-P1結果](docs/experiments/MMIA-R002-P1-results.md)：層化学習の費用と探索validation。

## English

### Research theme

MMIA investigates whether specialization, dynamic composition, knowledge memory, and dynamic hierarchy formation in small modules can reduce the total cost of AI training and inference while maintaining answer quality.

The initial architecture uses a **shared small backbone with specialized LoRA adapters**, rather than independent small language models. Shared latent communication and independent models are later research stages.

### Objectives and scope

- Reduce the training time and memory required to acquire and update specialized capabilities.
- Activate only useful modules and test whether they can replace a larger dense model at comparable quality.
- Compare knowledge stored in adapter weights with retrieval-augmented generation (RAG).
- Identify both beneficial and unfavorable operating conditions, including coordination, loading, and update costs.

Reducing trainable parameters does not automatically reduce backbone inference computation. Cost savings must come from a demonstrated mechanism, such as replacing a larger model or shortening retrieved context.

| Research area | Planned investigation |
| --- | --- |
| Specialization | Compare math, physics, coding, and formal-logic adapters with a single adapter trained on mixed data |
| Selection and composition | Compare hard routing, soft composition, and self-activation, including routing overhead and interference |
| Parametric memory | Compare adapter-based synthetic knowledge with RAG in quality, latency, context length, and preparation cost |
| Knowledge updates | Measure update cost, stale answers, and forgetting of unaffected facts |
| Shared workspace | Test whether latent communication provides gains beyond its additional capacity and computation |
| Dynamic hierarchy formation | Detect stable MicroMoE cooperation patterns, promote them through macros and distillation, and evaluate demotion and expansion |
| Scaling | Investigate hierarchy, SSD loading, caching, and communication between independent models in later stages |

### Hypotheses and method

The main hypotheses concern the cost–quality benefit of specialization, the benefit of alternatives to central routing, and the conditions under which parametric memory can amortize training and update costs relative to RAG. Full replacement of RAG is not the goal.

Start with a reproducible evaluation harness and a candidate backbone in the 0.5–1.5B range. Keep capability experiments separate from knowledge-storage experiments. Register one hypothesis, comparison protocol, and acceptance rule per experiment before evaluating the test set.

Use synthetic knowledge and held-out questions, with grouped splits to prevent leakage. Evaluate English, Japanese, and Simplified Chinese separately. Measure quality, training time, inference computation, time to first token, completion latency, peak memory, and update costs; report energy only when measured. Compare total cost at a predefined quality requirement, including retrieval, routing, loading, and retries.

### Dynamic Hierarchical Module Formation

A fourth hypothesis asks whether reusable cooperation patterns can be promoted into higher modules at lower total cost, including distillation, management, and fallback. This is a central research theme: reorganizing computation through experience.

The proposed stages are **pattern discovery → virtual macro → distillation → reusable higher module**. A macro still invokes its original modules; distillation attempts to replace that computation with a learned module. Promotion requires measured quality and savings, not just frequent co-occurrence or fewer calls.

Keep the lower modules available for low-confidence, exceptional, or unfamiliar inputs. Evaluate demotion when usage declines, quality deteriorates, or patterns change. Distinguish merge, split, promote, and demote, with capacity and depth limits to avoid uncontrolled growth.

An illustrative hierarchy is primitive MicroModels → learned MicroMoE → reusable functional modules → abstract reasoning modules → task/domain systems. Lower levels may learn concrete knowledge, middle levels processing patterns, and upper levels abstract relations; this division is a hypothesis, and higher modules need not be larger. We use **Hierarchical Neural Compilation** as a working name, without claiming established novelty or effectiveness.

See the [detailed research proposal](docs/dynamic-hierarchical-module-formation.md). Implementation follows baseline evaluation and collection of cooperation traces.

### Status and documents

- [Done] Research design, literature review, cost model, experiment proposals, and roadmap documented.
- [Done] Dynamic hierarchy formation, promotion, distillation, and demotion proposal documented.
- [Done] Implemented the pilot harness; two CPU runs matched all 24 token sequences and grades, also matching standard generate.
- [Done] Built and audited the 1,296-row pilot-v2; Core-only strict accuracy was 94/432 (21.8%).
- [Done] Completed a four-step LoRA train/save/reload smoke test with 540,672 trainable parameters and a 2.1MB adapter weight file.
- [Done] Trained a stratified 72-step mixed LoRA in 18.98 seconds; exploratory strict validation rose from 21.8% to 41.2%.
- [Next] Compare mixed and four specialist LoRAs across three seeds at a matched training budget.
- [Later] Dynamic coordination, knowledge memory and updates, workspace, hierarchy, SSD delivery, and independent models.
- [Later] Trace-based macros, distilled higher modules, fallback, and demotion experiments.

Core inference and an exploratory stratified mixed-LoRA run have been tested. Strict validation improved from 94/432 (21.8%) to 178/432 (41.2%). This is a one-seed pilot; the registered specialist comparison, RAG, and promotion mechanisms remain unimplemented, and cost reductions have not been demonstrated. See the [mixed-LoRA pilot](docs/experiments/MMIA-R002-P1-results.md).

See the [architecture design](docs/Micro-Modular-Intelligence-Architecture.md), [research review and references](docs/research-review-2026-09-11.md), and [roadmap](docs/ROADMAP.md). The detailed documents are primarily in Japanese.

## 简体中文

### 研究主题

MMIA研究如何通过小型模块的专业化、动态组合、知识记忆与动态层次形成，在保持回答质量的同时，降低AI训练、推理和知识更新的总成本。

初期采用**共享小型主干模型与专业LoRA适配器**，而不是多个独立的小型语言模型。共享潜在空间通信与独立模型之间的协作属于后续研究阶段。

### 研究目标与内容

- 减少学习、添加和更新专业能力所需的训练时间与内存。
- 仅激活有用的模块，验证其能否以相近质量替代更大的稠密模型。
- 将稳定知识存入适配器权重，并与检索增强生成（RAG）比较。
- 将协作、加载和更新成本纳入评估，明确模块化的适用条件与失败条件。

减少可训练参数并不意味着主干推理计算会自动减少。成本优势需要通过替代更大模型、缩短检索上下文等具体途径加以验证。

| 研究方向 | 计划验证的内容 |
| --- | --- |
| 专业模块 | 将数学、物理、编程和形式逻辑适配器与混合数据训练的单适配器比较 |
| 动态选择与组合 | 比较硬路由、软组合和自激活，统计选择开销与模块间干扰 |
| 参数化记忆 | 将适配器中的人工知识与RAG比较，评估质量、延迟、上下文长度及准备成本 |
| 知识更新 | 测量更新成本、旧答案残留，以及未修改知识的遗忘 |
| 共享工作空间 | 检验潜在空间通信带来的收益是否超过额外容量与计算的作用 |
| 动态层次形成 | 检测稳定的MicroMoE协作模式，通过宏封装与蒸馏晋升为上层模块，并验证降级与展开 |
| 扩展性 | 分阶段研究层次结构、SSD加载、缓存及独立模型之间的通信 |

### 研究假设与方法

主要假设包括：专业化能否改善质量与成本的关系；中央路由之外的协作方式是否更有效；参数化记忆在什么条件下能回收相对于RAG增加的训练与更新成本。研究不以完全替代RAG为目标。

首先建立可重复运行的评估框架，并从约0.5〜1.5B参数的主干模型开始小规模试验。专业能力实验与知识存储实验分别进行。每个实验只检验一个假设，在查看测试结果前确定比较条件、指标和验收标准。

使用人工知识和未见问题，通过分组划分避免数据泄漏。分别评估英语、日语和简体中文。记录质量、训练时间、推理计算量、首token延迟、完整回答延迟、峰值内存及更新成本；能实际测量时再报告能耗。在预先规定的质量要求下，比较包含检索、路由、加载和重试的总成本。

### 动态层次形成：Dynamic Hierarchical Module Formation

第四个假设是：将可复用的协作模式晋升为上层模块后，能否在包含蒸馏、管理和回退开销的条件下减少总成本。**通过经验整理计算结构本身**是本研究的核心主题之一。

计划流程为 **模式发现 → 虚拟宏 → 蒸馏 → 可复用上层模块**。宏封装仍调用原有下层模块；蒸馏则尝试用学到的新模块替代这些计算。晋升需验证质量与实际节省，不能只依据共现频率或调用次数。

保留下层模块，在低置信度、异常或未知问题上展开原始路径。当使用频率下降、质量退化或协作模式变化时，验证降级机制。区分merge、split、promote与demote，并限制容量及层次深度，防止无控制增长。

层次示例为基础MicroModel → 学习形成的MicroMoE → 可复用功能模块 → 抽象推理模块 → 任务／领域系统。下层学习具体知识、中层学习处理模式、上层学习抽象关系是一项待验证的分工假设；上层模块不一定更大。暂用 **Hierarchical Neural Compilation** 描述这一流程，不预先宣称其新颖性或有效性。

详见[动态层次形成研究设计](docs/dynamic-hierarchical-module-formation.md)。实现将在基础评估与协作轨迹收集之后开展。

### 当前进度与文档

- [Done] 已形成研究设计、文献评估、成本模型、实验方案和路线图。
- [Done] 已记录动态层次形成、晋升、蒸馏与降级的研究方案。
- [Done] 已实现最小框架；两次CPU运行的24条token序列与评分完全一致，也与标准generate一致。
- [Done] 已生成并审计1,296条pilot-v2数据；Core单模型严格正确率为94/432（21.8%）。
- [Done] 已完成四步LoRA训练、保存与重新加载；可训练参数540,672，适配器权重约2.1MB。
- [Done] 分层72步混合LoRA训练耗时18.98秒；探索性严格验证从21.8%提升至41.2%。
- [Next] 在相同训练预算下，用3个seed比较混合LoRA与4个专业LoRA。
- [Later] 动态协作、知识记忆与更新、共享工作空间、层次结构、SSD加载和独立模型通信。
- [Later] 基于轨迹的宏封装、上层模块蒸馏、回退与降级实验。

目前已完成Core基线与分层72步混合LoRA探索评估。严格验证从94/432（21.8%）提升至178/432（41.2%）。这是单seed试验；专业LoRA正式对比、RAG与晋升机制尚未实现，成本降低效果仍待验证。参见[混合LoRA试验](docs/experiments/MMIA-R002-P1-results.md)。

详细内容参见[研究设计](docs/Micro-Modular-Intelligence-Architecture.md)、[研究评估与参考文献](docs/research-review-2026-09-11.md)和[路线图](docs/ROADMAP.md)。详细文档以日语为主。
