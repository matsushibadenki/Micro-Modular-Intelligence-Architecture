# MMIA-R001：最小Core評価基盤の予備実験

登録：2026-09-11。モデル実行前に作成。仮説は「固定したモデル・入力・seed・CPU設定で個別出力を再現し、品質と資源ログを欠損なく保存できる」。専門化、階層形成、コスト削減はまだ検証しない。

## 固定条件

- [Qwen/Qwen2.5-0.5B-Instruct公式モデルカード](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)に基づき選定。最新／最良モデルであるという主張はしない。
- revision `7ae557604adf67be50417f59c2c2f167def9a775`、Apache-2.0。モデルをローカルへ取得し、実行時はnetwork不要。重みとtokenizerのファイルhashを保存する。
- Python 3.10、PyTorch 2.10.0、Transformers 4.57.6、NumPy 1.25.2。CPU、float32、4 threads、batch size 1。MPSはこのsandbox内で利用不可と判定されたため採用しない。実機GPUの能力に関する結論ではない。
- テンプレート問題4分野、各10意味group、各groupの英語・日本語・简体中文を同じsplitへ配置。train 72行、validation 24行、test 24行。今回実行するのはvalidationのみ。
- 算術、F=ma、Pythonコードの出力予測、全順序の推論。コード生成・任意コード実行は未実装。
- integer-only出力、greedy argmax、最大32生成token、1問30秒の協調的deadline。各forward自体の強制中断は行わない。
- processごとにモデルloadと1問のwarmupを実行後、全validationを測定する。同一設定で2 processを順番に実行する。

## 採否基準

両runが全24問を記録し、error／timeout／truncatedが0件、問題IDごとのtoken列と採点が一致するなら初期再現性を合格とする。正答率は記述統計であり合否の条件ではない。

基盤不具合の修正は履歴を残して再実行する。正答率を見てpromptを調整して同じ結果を本試験と呼ばない。3 seed・検出力分析・新規テンプレートによる本試験は後続作業。

## 計測範囲

TTFTはtokenize開始から最初の生成token（特殊tokenも含む）決定まで。完了時間はtokenizeから出力文字列decodeまで。モデルloadとwarmupを別保存。生成token数にはEOSを含む。最大長到達は、文字列が整数でも不正解扱い。

`ru_maxrss`はprocess生涯の最大RSS（macOSはbytes）。load中のpeakも含み、GPUメモリ・KV cache単独の指標ではない。OS cacheを消しておらず真のcold計測ではない。error／timeoutは正答率の分母に含め、成功時の遅延分布から除外して件数を明示する。

FLOPs・エネルギーは未計測としてnull。学習費用は今回は対象外。型・出力形式の失敗も隠さず保存する。

## 限界

簡単な同一テンプレート問題によるsmoke testであり、一般能力、未見の構造への汎化、多段推論を測るbenchmarkではない。翻訳groupの漏洩は防ぐが、テンプレート自体はsplit間で共通。人手による翻訳評価は未実施。短い24問からp95を安定した運用値と推定しない。

この実験はMMIA-R002の学習、R101の知識記憶、R201の昇格機構に必要な基盤の最初の工程である。
