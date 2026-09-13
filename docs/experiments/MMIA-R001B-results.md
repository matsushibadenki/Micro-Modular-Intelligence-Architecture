# MMIA-R001B：pilot-v2 Core床効果

実施日：2026-09-13。目的は、改善したpilot-v2に対するCore単独の床効果と、MMIA-R002前の評価上の問題を確認すること。専門化やコスト削減の実験ではない。

## データ監査

pilot-v2は432意味問題、英語・日本語・简体中文の計1,296行。train／validation／testは各144意味問題、easy／medium／hardも各144意味問題である。12 task familyを各36意味問題含む。

各domain・split・difficultyセルは12意味問題。論理問題は全セルで真6／偽6。36個のtemplate IDはsplit間で共有されない。全targetを構造化parameterから再計算し、dataset hash `9b2b13d2e561703b288156753df9ce4b3d0c80eccebb9bc79acf211dd1d88f11` とともに監査結果を保存した。

論理記号名を乱数由来の不透明なIDにし、問題番号の偶奇から真偽を推測できるshortcutを除いた。これは生成途中の監査で発見し、Core実行前にdatasetを再生成した変更である。

## Core単独の実測

validationの144意味問題・432翻訳行を、Qwen2.5-0.5B-Instruct、CPU、float32、4 threads、greedy、32生成token上限で一回実行した。

| 指標 | 結果 |
| --- | ---: |
| 保存行 | 432/432 |
| 厳格integer-only正解 | 94/432（21.8%） |
| 意味group bootstrap 95%区間 | 16.9%–26.9% |
| 全3言語で正解した意味group | 5/144（3.5%） |
| 1言語以上で正解した意味group | 55/144（38.2%） |
| format invalid | 93/432 |
| truncated | 43/432 |
| error／timeout | 0／0 |
| 成功行のTTFT中央値 | 0.110秒 |
| 成功行の完了時間中央値／p95 | 0.185秒／0.577秒 |
| モデルload | 5.439秒 |
| process lifetime peak RSS | 3.538 GB（10進） |

truncatedは品質上の失敗として正答率の分母に含む。成功行の遅延分布には含めず、件数を明示した。時間は単一runで、OS cache・端末負荷の影響を受ける。FLOPsとエネルギーは未計測。

| slice | strict accuracy |
| --- | ---: |
| Math | 24/108（22.2%） |
| Physics | 2/108（1.9%） |
| Coding | 13/108（12.0%） |
| Logic | 55/108（50.9%） |
| English | 38/144（26.4%） |
| 日本語 | 22/144（15.3%） |
| 简体中文 | 34/144（23.6%） |
| Easy | 55/144（38.2%） |
| Medium | 17/144（11.8%） |
| Hard | 22/144（15.3%） |

論理50.9%は均衡した二値問題の定数予測50%に近い。これだけでは順序推論能力を示さない。物理1.9%は強い床効果であり、専門LoRAが改善しない場合に、モジュール分割の効果がないと単独で結論づけられない。

日本語では41件がtruncated、83件がformat invalidだった。英語と简体中文でも各1件がtruncatedした。32 token上限を後から変更して同じ実験の結果へ混ぜず、R002では全群に共通の条件を事前固定する。意味上の最終回答を説明文から抽出する緩い採点を主要指標へ変更しない。

## 実行上の失敗

最初のrun-01は制限外環境で`python3`がPython 3.14を指し、PyTorchが存在しなかったためモデルload前にfailedとなった。run-02では前回使用したPython 3.10の絶対パスを指定して完了した。今後はinterpreter pathと環境lockをmanifestへより明確に保存する。

## 判断

- pilot-v2の構造監査は合格。[Done]
- Core床効果runは全行を保持して完了。[Done]
- strict出力、特に日本語の形式遵守は弱い。R002では学習効果の一部として測る。[Next]
- R002は物理の床効果と論理のchance baselineを明記して開始する。[Next]
- LoRA／Accelerateの隔離・固定環境と、短い学習pilotがまだ必要。[Next]

## 成果物

- [dataset](../../datasets/pilot-v2.jsonl)／[監査](../../datasets/pilot-v2-audit.json)
- [固定設定](../../configs/pilot-v2-core.json)
- [run-01失敗記録](../../results/MMIA-R001B/run-01/manifest.json)
- [run-02個別結果](../../results/MMIA-R001B/run-02/predictions.jsonl)／[通常集計](../../results/MMIA-R001B/run-02/summary.json)／[group解析](../../results/MMIA-R001B/run-02/group-analysis.json)／[manifest](../../results/MMIA-R001B/run-02/manifest.json)

## English / 简体中文

**English:** pilot-v2 contains 432 semantic groups and 1,296 multilingual rows, balanced by domain, split, and difficulty; logic labels are exactly balanced. The Core-only validation run achieved strict accuracy 94/432 (21.8%, semantic-group bootstrap 95% interval 16.9–26.9%). Physics was 1.9%; logic was 50.9%, close to the balanced constant baseline. Forty-three outputs were truncated, mostly Japanese. This establishes a floor and exposes limitations; it does not demonstrate specialization or cost savings.

**简体中文：** pilot-v2包含432组语义问题与1,296条多语样本，在领域、数据划分和难度上保持均衡，逻辑标签完全平衡。Core单模型验证的严格正确率为94/432（21.8%，按语义组bootstrap的95%区间为16.9%–26.9%）。物理为1.9%，逻辑为50.9%，接近均衡二值任务的常数基线。共有43条输出被截断，主要是日语。本结果只确定基线并暴露限制，尚未证明专业化或成本节省。
