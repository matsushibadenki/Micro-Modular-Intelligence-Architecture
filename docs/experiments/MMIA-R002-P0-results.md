# MMIA-R002-P0：LoRA学習smoke test

実施日：2026-09-13。目的は学習経路、target-only loss、計測、Adapter保存・再読込の動作確認。単一LoRA対専門LoRAの品質比較ではない。

## 結果

- Qwen2.5-0.5B-Instructの`q_proj`と`v_proj`へrank 8、alpha 16のLoRAを追加。
- 総494,573,440 parameter中、trainableは540,672（約0.109%）。
- pilot-v2 trainからseed固定で4行を選び、batch 1、4 optimizer step、258入力token／21 target tokenを処理。
- prompt部分を`-100`でmaskし、assistant回答と終了tokenだけをloss対象とした。
- 4 lossは1.0306、1.7144、3.5037、2.3380で全て有限。異なる問題を一度ずつ処理したため、増減から学習効果を判断しない。
- 学習loopは1.054秒、process lifetime peak RSSは3.547 GB。モデルload・Adapter準備を学習時間から除外し、RSSには含める。
- Adapter safetensorsは約2.1MB。tokenizer一式を含む保存ディレクトリは約17MB。
- 新しいCoreへAdapterを再読込し、shape `[1, 34, 151936]` の全て有限なlogitsを得た。

採否基準だった4 step完了、有限loss、target-only mask、safetensors保存、再読込可能を満たした。[Done]

## 制約

品質、過学習、validation改善、学習再現性は検証していない。4行は全domain・language・difficultyを均衡に抽出したものではなく、比較データではない。時間はCPUでの単一run。FLOPsとエネルギーは未計測。

依存はPEFT 0.17.1とAccelerate 1.10.1をリポジトリ内`.deps`へ置き、既存のPython 3.10、PyTorch 2.10.0、Transformers 4.57.6、NumPy 1.25.2を使用した。入れ子venvは既存PyTorchを継承できなかったため、完全に隔離されたlock環境ではない。実行時にはoptional C++ extensionのTorch 2.11以上要求と、既存librosaの非推奨警告が出たが、CPU学習と再読込は完了した。

この結果から、rank 8の保存容量と短いCPU stepが技術的に実行可能だと確認できた。本比較の総学習時間は4 stepの単純比例で断定せず、層化samplingによる中規模pilotで測る。

## 成果物

- [固定設定](../../configs/lora-smoke.json)
- [manifest](../../results/MMIA-R002-P0/run-01/manifest.json)
- [stepログ](../../results/MMIA-R002-P0/run-01/steps.jsonl)
- [Adapter設定](../../results/MMIA-R002-P0/run-01/adapter/adapter_config.json)／[LoRA safetensors](../../results/MMIA-R002-P0/run-01/adapter/adapter_model.safetensors)
- [再読込検証](../../results/MMIA-R002-P0/run-01/reload-verification.json)

## English / 简体中文

**English:** A four-step CPU LoRA smoke test completed with 540,672 trainable parameters (about 0.109% of the model), finite losses, target-only loss masking, a 2.1MB adapter weight file, and a successful fresh reload and forward pass. The training loop took 1.054 seconds and lifetime peak RSS was 3.547GB. This validates the mechanism only; it provides no quality or cost comparison.

**简体中文：** 四步CPU LoRA冒烟测试已完成：可训练参数为540,672（约占模型0.109%），loss均为有限值，仅答案token参与loss，适配器权重约2.1MB，并成功重新加载和执行前向传播。训练循环耗时1.054秒，进程生命周期峰值RSS为3.547GB。本结果仅验证机制，不构成质量或成本对比。
