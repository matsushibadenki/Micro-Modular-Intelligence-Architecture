# MMIA-R002：単一LoRAと専門LoRA群の比較プロトコル

初回登録日：2026-09-13。固定条件登録日：2026-09-15。状態：`registered`。MMIA-R002-P0/P1で実行可能性と予算を確認した後、本比較の数値条件を固定した。以下の条件はvalidation結果を見る前に確定しており、testは未開封である。

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

## 固定した学習条件

- Coreは`Qwen/Qwen2.5-0.5B-Instruct` revision `7ae557604adf67be50417f59c2c2f167def9a775`。ローカルsnapshotをofflineで読み、tokenizerとchat templateも同revisionに固定する。
- C1/C2はLoRA rank 8、alpha 16、dropout 0、biasなし、対象層`q_proj`/`v_proj`。C3はrank 32、alpha 64とする。
- AdamW、learning rate 2e-4、weight decay 0、schedulerなし、batch 1、gradient accumulation 1、最大系列長256、gradient norm 1.0、CPU float32、4 thread。
- seedは`20260915`、`20260916`、`20260917`の3つ。P0/P1は機能・予算確認だけに使い、本比較へ混ぜない。
- C1はtrain全432行を1 epoch学習する。C2は各domainの全108行を対応expertが1 epoch学習し、4 expert合計432 updateとする。したがって、C1/C2は同じ学習行集合をそれぞれ1回処理し、総target tokenも一致する。
- 学習回答は整数とEOSだけをloss対象とし、prompt tokenはmaskする。padding tokenもmaskする。
- trainだけで重みを更新し、validationだけでcheckpointとhyperparameterを選ぶ。testは条件確定後に一度評価する。
- 3言語を同じ比率で含む全train集合をseedごとにshuffleする。
- C0〜C3で同じdecode、最大出力長、採点契約を使う。

PEFT 0.17.1とAccelerate 1.10.1をrepository内の隔離依存領域から読み込む。P1の72 updateは18.975秒、peak RSS 4.013 GBで完了したため、登録条件はローカルCPUで実行可能と判断した。

## 主要評価

最初の主要評価は意味group単位のmacro exact-matchとし、三つの翻訳を独立問題として過大計数しない。言語別・分野別・難易度別のexact-match、format遵守、失敗率を併記する。

費用はtrainable parameter数、処理学習token、学習wall time、process peak memory、推論TTFT・完了時間、入力／出力tokenを測る。推定FLOPsは推定法が実装された場合だけ報告し、時間やparameter数で代用しない。

## 採否基準

C2がC1に対してvalidationの意味group macro accuracyで改善し、seedを併合したpaired cluster bootstrap 95%区間下限が0を上回ることを品質面の採択条件とする。推論は正解domain labelからadapterを選ぶoracle上限であり、router計算は含まない。各行の推論時間がC1の1.25倍以内であることを運用面の条件とする。adapterの別process load時間は別に報告し、1問あたり推論時間へ混ぜない。

C2とC3は用途が異なるため、C2がC3より常に高品質であることを必須にしない。C3より低品質でもactive容量・推論費用との関係を報告する。C2がC1へ勝てない場合は、追加のrouting研究を正当化する根拠が弱いという否定結果として保存する。

## データ監査から残る制約

template文字列はsplit間で異なるが、生成規則とtask familyは共有される。このため「未見template」への転移であり、「未見技能」への転移ではない。物理は教科書的な整数演算、コードは安全な静的出力予測、論理は全順序に限定される。

12意味問題／セルは本試験として小さい。学習pilotの分散を見て、testを開封する前に別seedの世界を追加するか決める。追加する場合も現在のpilot-v2を変更せず、新しいdataset IDとhashを作る。

## English / 简体中文

**English:** MMIA-R002 compares a mixed-task LoRA with four domain LoRAs under oracle domain selection. Its registered main comparison uses three fixed seeds and exactly one pass over the same 432 training rows: one rank-8 mixed adapter versus four rank-8 specialists processing 108 domain rows each. Validation is used for the comparison; test remains unopened.

**简体中文：** MMIA-R002在已知领域标签的oracle选择条件下比较混合任务LoRA与四个领域LoRA。已注册的主要比较固定三个seed，并对相同的432条训练数据各处理一次：一个rank-8混合adapter，对比四个各处理108条领域数据的rank-8专家。比较只使用validation，test仍未打开。
