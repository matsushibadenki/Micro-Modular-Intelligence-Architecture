# MMIA-R002：単一LoRAと専門LoRA群の比較プロトコル

登録日：2026-09-13。学習・評価前のdraft。依存環境と短い学習pilotを確認した後、数値予算を確定して`registered`へ変更する。現時点では結果を含まない。

## 問い

同じFrozen Coreに対して、4分野の専門LoRAを分けること自体が、混合データで学習した単一LoRAより品質とコストの関係を改善するか。

この実験ではroutingを評価しない。専門LoRAには正しいdomain labelを与えるoracle選択を使い、分割の上限効果を測る。ここで利益がなければ、routingや階層形成によってその差を回復できるとは仮定しない。

## pilot-v2

- 4分野：数学、物理、Pythonコード出力予測、形式論理。
- 各分野についてtrain／validation／test × easy／medium／hard × 12意味問題。各意味問題に英語・日本語・简体中文があり、合計432意味問題・1,296行。
- domain・split・difficultyの各セルを均等化。論理は各セルで真6／偽6。
- `template_id`をsplitごとに分離し、翻訳された同一問題は同じsplitへ置く。
- 正解は構造化parameterから再計算して監査する。モデルが生成したコードは実行しない。

これは制御された小規模データであり、一般的な数学・物理・コード・論理能力を代表しない。同じtask familyの異なる表現への転移を測る。より大きな未知分布への一般化は別実験とする。

## 比較群

| 群 | 学習データ | 選択 | 目的 |
| --- | --- | --- | --- |
| C0 Core only | なし | なし | 未学習baselineと床効果の確認 |
| C1 Mixed LoRA-active | 全分野混合 | 単一 | 各専門LoRAと同じrankのactive容量対照 |
| C2 Four specialists | 分野別 | oracle domain | 分割の効果。1問では1個だけactive |
| C3 Mixed LoRA-total | 全分野混合 | 単一 | 4専門家の総trainable容量に近づける対照 |

C1とC2は、各分野・言語・難易度ごとの学習example数と、全群での総optimizer update相当量を可能な限り一致させる。C2の各expertをC1と同じstep数だけ学習すると総学習量が4倍になるため採用しない。gradient accumulationとsampling規則を事前に固定し、実際に処理したtoken数を保存する。

C3はLoRA rankを単純に4倍したとき、対象層によって実trainable parameter数が4倍になることを実装で確認する。rankの増加で実行kernelや最適化が変わるため、parameter数と時間の両方を報告する。

## 固定する学習条件

- Core revision、tokenizer、chat template、対象層、LoRA rank／alpha／dropout、optimizer、learning rate、scheduler、最大長、batch、gradient accumulation、precision。
- seedは少なくとも3つ。初回短縮pilotは機能確認だけに使い、本比較の結果へ混ぜない。
- 学習回答は整数とEOSだけをloss対象とし、prompt tokenはmaskする。padding tokenもmaskする。
- trainだけで重みを更新し、validationだけでcheckpointとhyperparameterを選ぶ。testは条件確定後に一度評価する。
- 3言語を同じ比率でsamplingし、同一意味groupの翻訳が同じbatchへ常に固まらないようshuffleする。
- C0〜C3で同じdecode、最大出力長、採点契約を使う。

依存関係は隔離した環境へlockする。現在の共有環境にはPEFTとAccelerateがないため、学習はまだ開始していない。CPU学習の所要時間とメモリを短いpilotで確認し、ローカルで現実的でない場合はデータ規模・対象層・backendを別IDで変更する。

## 主要評価

最初の主要評価は意味group単位のmacro exact-matchとし、三つの翻訳を独立問題として過大計数しない。言語別・分野別・難易度別のexact-match、format遵守、失敗率を併記する。

費用はtrainable parameter数、処理学習token、学習wall time、process peak memory、推論TTFT・完了時間、入力／出力tokenを測る。推定FLOPsは推定法が実装された場合だけ報告し、時間やparameter数で代用しない。

## 仮の採否基準

本学習pilot後に検出可能差と費用から確定する。初期案は、C2がC1に対して意味group macro accuracyで改善し、そのpaired bootstrap 95%区間下限が0を上回ること。さらにC2のoracle選択費用を含む1問あたり推論時間がC1の1.25倍以内であること。

C2とC3は用途が異なるため、C2がC3より常に高品質であることを必須にしない。C3より低品質でもactive容量・推論費用との関係を報告する。C2がC1へ勝てない場合は、追加のrouting研究を正当化する根拠が弱いという否定結果として保存する。

## データ監査から残る制約

template文字列はsplit間で異なるが、生成規則とtask familyは共有される。このため「未見template」への転移であり、「未見技能」への転移ではない。物理は教科書的な整数演算、コードは安全な静的出力予測、論理は全順序に限定される。

12意味問題／セルは本試験として小さい。学習pilotの分散を見て、testを開封する前に別seedの世界を追加するか決める。追加する場合も現在のpilot-v2を変更せず、新しいdataset IDとhashを作る。

## English / 简体中文

**English:** MMIA-R002 compares a mixed-task LoRA with four domain LoRAs under oracle domain selection. It separates equal-active-rank and approximately equal-total-trainable-parameter controls. Data, update counts, target-only loss, model revision, and decoding must be fixed before test evaluation. This is a draft protocol; training has not started.

**简体中文：** MMIA-R002在已知领域标签的oracle选择条件下，比较混合任务LoRA与四个领域LoRA，并分别设置相同激活rank和近似相同总可训练参数的对照。测试前需固定数据、更新量、仅答案loss、模型版本与解码条件。本文件仍为草案，尚未开始训练。
