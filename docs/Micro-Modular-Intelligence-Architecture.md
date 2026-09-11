最初から巨大な完成形を作るのではなく、**「Micro Model連携は本当にDense/RAGより有利か」を低コストで反証可能にする研究設計書**です。

追加研究テーマ（2026-09-11）：[Dynamic Hierarchical Module Formation](dynamic-hierarchical-module-formation.md)。MicroMoEの安定した連携を検出し、マクロ化・蒸留によって上位モジュールへ昇格させ、下位経路を保持したまま降格・再展開する機構をH4として検証します。以下の原構想に対する追加設計であり、効果は未検証です。

この研究では特に、前の議論をそのまま採用するのではなく、むしろ次の3点を疑うことを中心にします。

1. Micro Modelを分割すると本当に効率が上がるのか
2. Router以外の連携方式が有効なのか
3. Parametric Micro MemoryはRAGの一部を本当に代替できるのか

以下をそのままCodexへ渡せる設計書として使えます。

---

# Micro Modular Intelligence Architecture

## 動的Micro Model連携・Parametric Memory・RAG代替可能性の研究設計書

### 1. 研究目的

現在のLLMは、一つの巨大なニューラルネットワークへ知識・推論能力・技能を集中させる設計が中心である。

本研究ではこれを分解し、

```text
Core Intelligence
        │
        ├── Micro Expert
        ├── Micro Expert
        ├── Parametric Memory
        ├── Shared Workspace
        ├── RAG
        └── Tools
```

というモジュール構造によって、

**「巨大モデル全体を毎回動かさず、必要な能力だけ動的に構成するAI」**

が成立するか検証する。

特に、従来の

```text
Input
 ↓
Router
 ↓
Expert
```

という単純なMoEを超え、

```text
Input
 ↓
Shared Workspace
 ↕
複数Micro Modules
 ↕
Parametric Memory
 ↕
RAG
 ↓
Dynamic Assembly
 ↓
Output
```

を研究対象とする。

---

# 2. 最重要研究仮説

## H1：Micro Model化はDense Modelより高効率になる

同一程度の推論性能に対して、

```text
Active Parameters
Memory Bandwidth
FLOPs
Peak RAM
Energy
```

を減らせるか検証する。

単純に総parameter数ではなく、

```text
Quality / Active FLOPs
Quality / Joule
Quality / Active Parameters
```

を主要評価指標とする。

---

## H2：Central Routerは最適ではない

通常MoEのような

```text
Router → Expert
```

ではなく、

```text
Self Activation
Shared Workspace
Soft Composition
Competition
Consensus
Dynamic Assembly
```

がより優れている可能性を検証する。

---

## H3：Micro ModelはRAGの一部を代替できる

現在、

```text
Question
 ↓
Vector Search
 ↓
Documents
 ↓
Context
 ↓
LLM
```

としている部分を、

```text
Documents
 ↓
Knowledge Compiler
 ↓
Micro Parametric Memory
 ↓
LLM
```

に変換できるか検証する。

ただし、

**RAG完全置換を目的としない。**

正確な引用、新情報、頻繁に更新される情報についてはRAGの方が原理的に有利である可能性が高い。

---

# 3. 最初に重要な設計判断

最初から、

```text
100M LLM
100M LLM
100M LLM
100M LLM
```

という独立モデル群を作らない。

理由は、それぞれのlatent spaceが一致しないためである。

例えば、

```text
Model A hidden state = [0.5, -0.1, ...]
```

と

```text
Model B hidden state = [0.5, -0.1, ...]
```

は同じ意味を表している保証がない。

したがってPhase 1では、

**Shared Backbone + Micro Modules**

を使用する。

---

# 4. 基本アーキテクチャ

最初の研究モデルを

**MMIA-1
Micro Modular Intelligence Architecture v1**

と呼ぶ。

構造：

```text
                       ┌─ Micro Math
                       │
                       ├─ Micro Physics
                       │
Input → Shared Core ───┼─ Micro Coding
                       │
                       ├─ Micro Logic
                       │
                       └─ Parametric Memory
                              │
                              ↓
                    Shared Latent Workspace
                              │
                              ↓
                         Shared Core
                              │
                              ↓
                           Output
```

---

# 5. Shared Core

最初は0.5〜1.5B程度を推奨する。

MacBook Airクラスでも繰り返し実験可能なサイズを優先する。

Coreには、

```text
Language
General reasoning
Token representation
Basic world model
Instruction following
```

のみを担当させる。

専門知識は可能な限りMicro Module側へ分離する。

---

# 6. Micro Module

Micro Moduleは独立LLMではなく、最初は、

```text
LoRA
Adapter
Small FFN
Residual MLP
Low-rank expert
```

として実装する。

例えば：

```text
Shared Transformer Block

x
│
├───────────────┐
│               │
Base FFN      Micro Adapter
│               │
└────── + ──────┘
        │
       next
```

Micro Moduleのサイズは実験的に、

```text
1M
5M
10M
25M
50M
100M
```

程度まで変える。

重要なのは0.1Bという数字自体ではない。

**どのサイズから専門能力が形成されるか**

を測定する。

---

# 7. Micro Moduleの種類

初期実験では4種類に限定する。

```text
Math
Physics
Programming
Formal Logic
```

理由は評価が比較的客観的だからである。

例えば文学や歴史から始めると、「能力向上」の定量評価が難しい。

---

# 8. Router以外の連携方式

ここが本研究の中心となる。

最低でも以下を比較する。

## A. Hard Routing

通常のMoE。

```text
Input
 ↓
Router
 ↓
Top-1 / Top-2 Expert
```

比較基準として必要。

---

## B. Soft Routing

```text
Math     0.6
Physics  0.3
Logic    0.1
```

として出力を混合する。

```text
y =
0.6 Math(x)
+ 0.3 Physics(x)
+ 0.1 Logic(x)
```

---

## C. Self Activation

中央Routerを置かない。

各Micro Module自身が、

```text
activation_score = f(hidden_state)
```

を出す。

例えば：

```text
Math      0.91
Physics   0.75
Coding    0.04
Logic     0.62
```

閾値以上のみ活動させる。

この方式では、

**「RouterがExpertを選択する」**

のではなく、

**「Expert自身が必要性を判断する」**

ことになる。

---

# 9. Competitive Activation

さらに一歩進める。

各Expertが、

```text
bid = relevance × confidence / computational_cost
```

を出す。

例えば：

```text
Math

relevance = .92
confidence = .80
cost = .20

bid = 3.68
```

Physics:

```text
.85 × .90 / .35
= 2.18
```

Mathが優先される。

つまり、

**性能だけでなく計算コストまで考慮したExpert選択**

を可能にする。

---

# 10. Shared Latent Workspace

研究上かなり重要な部分。

例えば、

```text
Workspace = 16 slots × hidden dimension
```

程度の小さな共有メモリを作る。

```text
             ┌ Math
             ↓
        ┌──────────┐
Physics → Workspace ← Logic
        └──────────┘
             ↑
           Coding
```

各Micro Moduleは、

```text
read()
write()
update()
```

を行う。

自然言語を経由させない。

---

# 11. Workspace通信

例えばPhysics Moduleが、

```text
Problem contains:
- acceleration
- mass
- force
```

というlatent representationを書き込む。

Math Moduleがそれを読み、

```text
equation structure
```

をWorkspaceへ追加する。

Logic Moduleが、

```text
constraint consistency
```

を追加する。

最終的にCoreがWorkspaceを読む。

---

# 12. Workspaceの重要な実験

次の二つを比較する。

```text
A → B → C
```

という直列通信と、

```text
     A
     ↓
B → Workspace ← C
```

という共有通信。

仮説としては、Micro Module数が増えるほどShared Workspace方式が有利になる。

---

# 13. Iterative Workspace

一回だけ通信するのではなく、

```text
Iteration 1
Math writes

Iteration 2
Physics reads/writes

Iteration 3
Logic reads/writes

Iteration 4
Math revises
```

とする。

つまり、小型モデル間の内部討論に近い。

ただし自然言語は使用しない。

---

# 14. Dynamic Composition

次の実験。

Micro Moduleを単純に呼び出すのではなく、

```text
Core
+
Physics Adapter
+
Math Adapter
+
Logic Adapter
```

として一時的なネットワークを構成する。

概念的には、

```text
Model(t)
=
Core
+
Σ α_i Module_i
```

とする。

---

# 15. Dynamic Weight Composition

最初は単純な線形合成から開始する。

```text
ΔW =
α1 ΔW_math
+
α2 ΔW_physics
+
α3 ΔW_logic
```

ただし、この方式は干渉する可能性がある。

そのため、

```text
Linear Merge
Rank Concatenation
Orthogonal Merge
Layer Selective Merge
Activation Composition
```

を比較する。

---

# 16. Module Conflict

非常に重要な研究項目。

例えば、

```text
Math Module
```

と

```text
Coding Module
```

を同時にactivateした結果、性能が落ちる可能性がある。

そこで、

```text
Interference Matrix
```

を作る。

例：

| Module A | Module B | Synergy |
| -------- | -------- | ------: |
| Math     | Physics  |   +0.18 |
| Math     | Logic    |   +0.11 |
| Physics  | Coding   |   +0.02 |
| Math     | Language |   -0.04 |

これを学習してDynamic Assemblyへ利用する。

---

# 17. Module Graph

最終的には単純なexpert集合ではなく、

```text
        Math
       /    \
Physics      Logic
   \          /
     Geometry
         |
      Coding
```

のようなGraphとして扱う。

Edgeには、

```text
compatibility
communication
dependency
activation probability
```

を持たせる。

---

# 18. Parametric Memory研究

ここからRAGとの比較になる。

例えば1000個の人工的な事実を作る。

```text
Planet A has 3 moons.
Planet B has blue vegetation.
Country C uses currency X.
Element D melts at 811 units.
```

現実世界の知識ではなく、

**完全に人工的な世界**

を最初に使う。

理由はモデルが事前学習ですでに知っている可能性を排除するため。

---

# 19. Synthetic Knowledge World

例えば、

```text
10,000 entities
50 relations
100,000 facts
```

程度を生成する。

例：

```text
A lives in B
B belongs to C
C produces D
D requires E
```

さらにmulti-hop問題を生成する。

```text
Aが所属する組織が生産する製品は何か？
```

---

# 20. RAG Baseline

通常の、

```text
Embedding
 ↓
Vector Search
 ↓
Top-k chunks
 ↓
Core Model
```

をBaselineとする。

---

# 21. Parametric Micro Memory

同じデータを、

```text
Synthetic Documents
 ↓
Knowledge Compiler
 ↓
Micro Adapter Training
 ↓
Knowledge Module
```

へ変換する。

質問時には検索しない。

```text
Question
 ↓
Knowledge Module
 ↓
Answer
```

---

# 22. Knowledge Compiler

非常に重要なサブシステム。

単純に文章をfine-tuneするのではなく、

```text
Document
 ↓
Fact extraction
 ↓
Relations
 ↓
Synthetic QA
 ↓
Reasoning chains
 ↓
Negative examples
 ↓
Adapter training
```

とする。

例えば、

```text
Document:
Planet X has two moons.
```

から、

```text
Q: How many moons does Planet X have?
A: 2
```

だけでなく、

```text
Q: Does Planet X have more than one moon?
A: yes
```

などを自動生成する。

---

# 23. RAG vs Parametric Memory

次を測る。

```text
Accuracy
Latency
TTFT
Tokens consumed
RAM
Energy
Update cost
Forgetting
Hallucination
Source traceability
```

---

# 24. 最重要比較

次の条件を必ず同一データで比較する。

```text
A. Core only

B. Core + RAG

C. Core + Micro Memory

D. Core + RAG + Micro Memory

E. Core + full fine-tuning
```

これで、

**Micro Memory自体の寄与**

を分離できる。

---

# 25. Knowledge Update Test

RAGの最大の強みは更新性なので、ここを厳しく検証する。

例えば、

```text
Day 1

Planet A has 3 moons.
```

を学習。

その後、

```text
Day 2

Planet A has 5 moons.
```

へ変更。

測定：

```text
更新時間
旧知識の残存率
新知識のaccuracy
無関係知識への影響
```

---

# 26. Catastrophic Interference Test

特に重要。

知識Moduleへ新知識を追加した結果、

```text
旧知識1000件
```

の何件が壊れるか調べる。

これを、

```text
Forget Rate
```

として記録する。

---

# 27. Micro Model差分学習

理想的には、

```text
Physics-v100
       ↓
new paper
       ↓
Physics-v101
```

で変更されるweightが非常に小さいことが望ましい。

そこで、

```text
ΔW sparsity
```

を測定する。

---

# 28. Delta Module

さらに、

```text
Physics Base
+
2026 Update Adapter
```

という構造も検証する。

毎回Physics Module全体を再学習しない。

```text
Physics
├ Base
├ Update 01
├ Update 02
└ Update 03
```

とする。

Gitのcommitに近い。

---

# 29. Knowledge Fragmentation

知識Micro Moduleも巨大化する可能性がある。

そこで、

```text
Physics
├ Mechanics
├ Quantum
├ Relativity
└ Thermodynamics
```

へ分割する。

さらに、

```text
Quantum
├ QFT
├ QM
└ Quantum Computing
```

へ階層化できるか検証する。

---

# 30. Hierarchical Activation

例えば、

```text
Question
 ↓
Science
 ↓
Physics
 ↓
Quantum
 ↓
Entanglement
```

と段階的に絞る。

ただし中央Routerだけに依存させない。

各階層が、

```text
activation proposal
```

を出す方式も比較する。

---

# 31. SSD Expert Streaming

後期実験では、

```text
GPU/Unified Memory
   ↑
RAM Expert Cache
   ↑
SSD Expert Store
```

を実装する。

Micro Moduleが例えば25MBなら、

```text
必要なModuleだけSSDからロード
```

する。

---

# 32. Prefetch Prediction

現在使っているModuleから次に必要なModuleを予測する。

例えば、

```text
Physics
 ↓
80% → Math
15% → Logic
5% → Coding
```

ならPhysics実行中にMathをprefetchする。

---

# 33. Expert Cache

LRUではなく、

```text
usage frequency
transition probability
load cost
module size
task context
```

を使う。

例えば、

```text
cache_score =
future_probability
× load_cost
/ memory_size
```

とする。

---

# 34. 独立Micro Model実験

Shared Backbone方式が成立した後で初めて、

```text
Independent 100M Model A
Independent 100M Model B
Independent 100M Model C
```

を試す。

---

# 35. Latent Translator

独立モデル間には、

```text
Model A latent
 ↓
Projection Network
 ↓
Shared Latent Space
 ↓
Projection Network
 ↓
Model B latent
```

を配置する。

---

# 36. Universal Latent Bus

将来的には、

```text
Model A ─┐
Model B ─┼→ Universal Latent Bus
Model C ─┤
Vision ──┤
Audio ───┘
```

を目指す。

これはMicro Model版のシステムバスに相当する。

---

# 37. 実験Baseline

必ず以下と比較する。

```text
Dense Small Model
Dense Larger Model
Hard-MoE
RAG
LoRA Expert
Soft-MoE
Shared Workspace
Dynamic Assembly
Hybrid
```

最大モデルに勝つ必要はない。

重要なのは、

**同一Active Computeで勝つか**

である。

---

# 38. 評価指標

最低限記録する。

品質：

```text
Accuracy
Exact Match
Pass@1
Reasoning success
Multi-domain composition
```

計算：

```text
Active Parameters
FLOPs
Tokens/sec
TTFT
```

メモリ：

```text
Peak RAM
Active weights
KV cache
Expert cache
SSD I/O
```

学習：

```text
Training time
Samples required
Update time
Energy
```

知識：

```text
Recall
Forgetting rate
Update accuracy
Hallucination
Provenance
```

---

# 39. 特に重要な指標

独自指標として、

```text
QAF = Quality / Active FLOPs
```

を導入する。

さらに、

```text
QAM = Quality / Active Memory
```

```text
QAE = Quality / Energy
```

も記録する。

将来的なMicro Model architectureでは、parameter数よりこちらが重要になる。

---

# 40. Phase構成

## Phase 0

Research Harnessを作る。

モデル構造には触らない。

目的：

```text
training
evaluation
profiling
logging
benchmark
```

を完全自動化する。

---

## Phase 1

Shared Core + LoRA Experts。

```text
Core
+
Math
Physics
Coding
Logic
```

のみ。

Hard RouterとSoft Router比較。

---

## Phase 2

Self Activation。

中央Routerを削除する。

---

## Phase 3

Shared Workspace。

Micro Modules間latent communicationを実装。

---

## Phase 4

Dynamic Assembly。

複数Adapterの動的合成。

---

## Phase 5

Parametric Memory。

Synthetic Knowledge WorldでRAG比較。

---

## Phase 6

Incremental Learning。

Knowledge updateを高速化。

---

## Phase 7

Hierarchical Micro Modules。

Module数を、

```text
4
16
64
256
```

程度へ増やす。

---

## Phase 8

SSD Streaming。

全ModuleをRAMへ置かない実験。

---

## Phase 9

Independent Micro Models。

Shared Backboneを取り除いた構成を比較する。

---

# 41. 最初のMVP

最初から全部作らない。

最初のMVPは、

```text
Core Model
+
4 LoRA Experts
+
Hard Router
+
Soft Composition
+
RAG
+
Synthetic Knowledge Benchmark
```

のみとする。

これで最初の重要仮説のかなりの部分を調べられる。

---

# 42. 推奨リポジトリ構成

```text
/micro-modular-intelligence/
│
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── configs/
│   ├── base.yaml
│   ├── model.yaml
│   ├── experts.yaml
│   └── experiments/
│
├── src/
│   └── mmia/
│       ├── core/
│       │   ├── backbone.py
│       │   └── tokenizer.py
│       │
│       ├── modules/
│       │   ├── adapter.py
│       │   ├── expert.py
│       │   └── registry.py
│       │
│       ├── routing/
│       │   ├── hard_router.py
│       │   ├── soft_router.py
│       │   ├── self_activation.py
│       │   └── bidding.py
│       │
│       ├── workspace/
│       │   ├── latent_workspace.py
│       │   └── communication.py
│       │
│       ├── composition/
│       │   ├── merge.py
│       │   ├── dynamic_adapter.py
│       │   └── interference.py
│       │
│       ├── memory/
│       │   ├── parametric.py
│       │   ├── delta_memory.py
│       │   └── compiler.py
│       │
│       ├── rag/
│       │   ├── retriever.py
│       │   └── baseline.py
│       │
│       ├── cache/
│       │   ├── expert_cache.py
│       │   └── prefetch.py
│       │
│       ├── training/
│       │   ├── trainer.py
│       │   └── continual.py
│       │
│       └── evaluation/
│           ├── metrics.py
│           ├── profiler.py
│           └── benchmark.py
│
├── experiments/
│
├── datasets/
│   ├── synthetic_world/
│   └── domain/
│
├── scripts/
│
├── results/
│
└── docs/
    ├── architecture.md
    ├── hypotheses.md
    └── experiment-log.md
```

---

# 43. 技術スタック

最初は研究速度を重視する。

```text
Python 3.10+
PyTorch
Transformers
PEFT
Accelerate
safetensors
FAISS or equivalent
MLX optional
```

ユーザー環境ではNumPy 1系を維持する。

```text
pip install "numpy<2.0"
```

Apple Silicon用最適化は、研究ロジックが安定してからMLX版を追加する方がよい。

最初からPyTorch版とMLX版を同時開発すると、architecture研究よりbackend差異のデバッグに時間を取られる。

---

# 44. Apple Silicon対応方針

研究初期：

```text
PyTorch MPS
```

研究後期：

```text
Core → MLX
Adapter → MLX
Expert Cache → Unified Memory
SSD Streaming → mmap
```

へ移行する。

Apple SiliconのUnified Memoryはこの研究と相性がよい。

CPUとGPUの間で巨大Expertを毎回コピーしない設計ができるためである。

---

# 45. Codexの開発原則

Codexには次のルールを与える。

```text
1 experiment = 1 hypothesis

一度に複数のarchitecture変更をしない。

変更前後で必ずbenchmarkを実施する。

性能改善だけでは採用しない。

Quality
Compute
Memory
Latency

を同時記録する。

結果が悪かったexperimentも削除しない。
results/failed/へ保存する。
```

---

# 46. Experiment ID

例えば、

```text
EXP-001
Hard Router baseline

EXP-002
Soft Router

EXP-003
Self Activation

EXP-004
Shared Workspace

EXP-005
Dynamic Adapter Composition
```

のようにする。

---

# 47. Codexに必ず守らせること

研究では特に重要。

```text
仮説
↓
変更
↓
実行
↓
結果
↓
解釈
↓
次実験
```

の順序を崩さない。

結果を見てから仮説を書き換えない。

---

# 48. 実験記録

各実験について、

```text
experiment_id
git_commit
model
dataset
seed
architecture
trainable_parameters
active_parameters
peak_memory
training_time
inference_latency
quality
result
interpretation
```

を保存する。

---

# 49. 成功条件

この研究が有望と判断する最初の基準を設定する。

例えば同一Active FLOPsで、

```text
Dense baseline
accuracy = 70
```

に対して、

```text
Micro architecture
accuracy >= 75
```

程度を第一目標とする。

あるいは同一qualityで、

```text
Active FLOPs -30%
```

でも成功とする。

---

# 50. Parametric Memory成功条件

RAGを完全に上回る必要はない。

安定知識について、

```text
RAG accuracy - 3pt以内
```

かつ、

```text
context tokens -70%
```

または

```text
latency -30%
```

程度なら十分研究価値がある。

---

# 51. 失敗条件

逆に次の場合は重要な否定結果となる。

Micro化によって、

```text
通信コスト
+
routing
+
module loading
+
coordination
```

がDense Modelの節約量を超える。

これは十分起こり得る。

Micro Modelが小さすぎると、

**専門化の利益よりcoordination overheadの方が大きくなる**

可能性がある。

---

# 52. 最も知りたい曲線

この研究で最重要のグラフの一つ。

横軸：

```text
Micro Module Size
```

縦軸：

```text
Quality / Active FLOPs
```

例えば、

```text
1M
5M
10M
25M
50M
100M
250M
```

と変える。

おそらくどこかに最適点がある。

小さすぎれば知能不足、

大きすぎればMoE分割のメリットが減る。

---

# 53. 第二の重要曲線

横軸：

```text
Number of Modules
```

縦軸：

```text
Coordination Overhead
```

と、

```text
Quality
```

を同時に測る。

これによって、

**Micro-MoEがどこまでMicro化できるのか**

が分かる。

---

# 54. 本研究で最も重要な問い

最終的には、

> 「LLMは巨大な一枚岩のニューラルネットワークである必要があるのか？」

を検証する研究になる。

仮に、

```text
4B Core
+
100M × 数千Modules
+
Parametric Memory
+
RAG
```

という総容量数百B〜1T級システムを作っても、

実際には、

```text
4B Core
+
100M × 3 modules
```

程度しか動かさなくて済むなら、

巨大AIのローカル化に非常に大きな意味を持つ。

---

# 55. 私なら最初に検証する構成

全体構想の中でも、最初はかなり絞ります。

```text
Frozen Core 0.5〜1.5B

      +
      
4 Micro Adapters
Math / Physics / Logic / Coding

      +

3 coordination methods
Hard Router
Soft Composition
Self Activation

      +

Synthetic Knowledge World

      +

RAG baseline
```

これだけです。

Shared Workspaceすら最初には入れません。

まず、

**「専門化した小さな差分Moduleを組み合わせること自体にDense Modelを超える意味があるか」**

を確認します。

ここで効果がなければ、巨大なMicro Modelシステムを作る意味は薄い。

逆にここで明確な改善が出た場合、

```text
Router
↓
Self Activation
↓
Workspace
↓
Dynamic Assembly
↓
Parametric Memory
↓
SSD Streaming
```

と進めます。

この順番なら、MacBook Air M4 / 32GBでも研究初期のかなりの部分をローカルで回せる規模に抑えられます。

そしてこの研究で本当に新規性が出そうなのは、単なる「Micro-MoE」より、

**Self-Organizing Micro Modules + Shared Latent Workspace + Dynamic Neural Assembly + Parametric Knowledge Compilation**

の組み合わせです。

つまり最終目標を、

> **モデルを選択するAIではなく、問題に応じてその場でニューラルネットワークそのものを構成するAI**

と置くのがよいと思います。

これは現在のMoEの単なる細分化ではなく、**固定LLMから「動的に構成されるニューラル計算機」への変更**として研究できます。
