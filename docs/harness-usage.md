# 最小評価基盤の実行方法

この基盤はCoreとLoRA Adapterの再現可能な予備実験用。target-only LoRA学習、Adapter評価、domain限定評価、意味group解析まで実装済み。RAGと昇格機構はまだ実装していない。

## 実行

リポジトリルートでPython 3.10以上を使用する。データ生成と単体テストは標準ライブラリのみで動く。モデル推論はpyproject.tomlのinference依存が必要。NumPyは2未満を維持する。今回の実測では既存のPython環境を使用した。

```sh
# データは既に同梱。再生成するときは別名を使用する。
PYTHONPATH=src python3 -m mmia.harness generate --output datasets/pilot-v1-copy.jsonl

PYTHONPATH=src python3 -m unittest discover -s tests -v

# 初回のみ公開モデルを約1GBダウンロード。
hf download Qwen/Qwen2.5-0.5B-Instruct --revision 7ae557604adf67be50417f59c2c2f167def9a775 --local-dir .models/qwen2.5-0.5b-instruct

# 同じ出力先を再利用しない。
PYTHONPATH=src python3 -m mmia.harness run --config configs/pilot-core.json --output results/MMIA-R001/run-04
```

設定は[固定設定](../configs/pilot-core.json)を参照。現在の実装はfloat32、eager attention、greedy、batch size 1に固定されている。precision/decodeの文字列は説明用であり、変更するだけでは実行方式は変わらない。seed、thread数、device、出力上限、deadlineは設定から使用する。CPU予備実験のみ検証済み。

推論APIにはpromptだけを渡し、正解や生成用パラメータを渡さない。採点は空白除去後に整数のみを許し、説明から都合のよい数値を抜き出さない。コード問題は出力予測であり、モデルのコードを実行しない。

## 結果と再現性

各runにmanifest、warmup、個別JSONL、集計JSONを保存する。失敗時もmanifestを残す。既存の出力ディレクトリやデータファイルは上書きしない。モデル重みはGit対象外とし、hash・公開revisionを記録する。

[検証スクリプト](../scripts/verify_pilot.py)は保存されたrun-02とrun-03を比較し、標準generateとの一致を検証したもの。既存verification.jsonは上書きしないため、そのまま再実行する場合も新しい保存先を指定するようスクリプトを複製・変更する。一般的な比較CLIへの拡張は未実装。

この端末の既存librosa／numbaはsandbox内でcacheエラーになる場合があり、今回の推論は許可された制限外実行で行った。依存を分離した環境での再現は今後確認する。

## English / 简体中文

**English:** Run the commands above from the repository root. Data generation and tests use the standard library; inference requires the optional inference dependencies. Keep NumPy below 2. Model inference is local and offline after download. Use a new output directory for every run. Only the CPU float32 greedy pilot has been validated.

**简体中文：** 在仓库根目录运行上述命令。数据生成与测试只依赖标准库，推理需要可选inference依赖，NumPy保持低于2。下载模型后可离线推理。每次运行使用新的输出目录，目前仅验证了CPU float32贪心试验。
