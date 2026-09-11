# MMIA-R001：Core評価基盤の予備実験結果

実施日：2026-09-11。[事前プロトコル](MMIA-R001-protocol.md)に基づく実装確認。**再実行で24/24問のtoken列と採点が一致し、同じgreedy条件のTransformers標準generateとも24/24問で一致した。** 初期再現性の採否基準を満たした。

この結果はMicroModelのコスト削減・専門化・階層形成を実証するものではない。

## 実施内容

- 4分野×10意味group×3言語、計120行の人工問題を生成。翻訳は同じsplitへまとめた。
- validationの8意味group／24行だけを実行。trainとtestの推論評価は未実施。
- Qwen2.5-0.5B-Instruct、494,032,768 parameters、固定revision。CPU／float32／4 threads／greedy／最大32token。
- 回答と採点、token数、TTFT、完了時間、process最大RSS、ファイルhash、環境情報を保存。
- 6件の単体テストで分割漏洩、採点契約、失敗時の分母、再現性、失敗ログ、上書き防止を確認。

## 実測値

| 指標 | run-02 | run-03 |
| --- | ---: | ---: |
| 完了問数 | 24 | 24 |
| 整数のみの契約で正解 | 5/24（20.8%） | 5/24（20.8%） |
| 出力形式違反 | 2 | 2 |
| error／timeout／truncated | 0／0／0 | 0／0／0 |
| TTFT中央値 | 0.111秒 | 0.106秒 |
| 回答完了時間中央値 | 0.191秒 | 0.178秒 |
| 回答完了時間p95 | 0.718秒 | 0.630秒 |
| モデルload時間 | 4.676秒 | 3.577秒 |
| process最大RSS（10進GB） | 3.613 | 3.538 |

時刻測定は実行中の端末負荷・OS cache・起動時の状態に影響される。2回の時間差をアーキテクチャ改善と解釈しない。メモリはloadやPython依存を含むprocess生涯のhigh-water markであり、重み単独・GPU単独ではない。FLOPsとJは未計測。

両runの分野別正解数は、数学0/6、物理1/6、コード出力予測0/6、論理4/6。言語別は英語3/8、日本語0/8、简体中文2/8だった。24問は8意味groupの翻訳なので、24個の独立した問題として統計的な確証を主張できない。

## 解釈と次の仮説

低い正答率に対し、推論ループの実装差を疑って標準generateとの照合を追加した。全tokenが一致したため、少なくともこの固定入力・固定decode条件での独自ループの不一致は観測されなかった。これはprompt設計やモデル選定が最適であることを意味しない。

整数のみという契約では、計算過程と正しい最終値を出した回答も不正解になる。実際に日本語数学の1問でこの形式違反があった。採点基準を後から緩めず、元の出力を保存した。

さらに、今回のvalidationでは論理の2意味groupが両方とも真だった。常に1を出す対照がこの部分で満点になるため、論理能力の評価には使えない。データ生成は翻訳の漏洩を防いでいるが、回答ラベルの層化はまだない。

このため、次の工程では次を完了してからMMIA-R002の学習へ進む。

1. **pilot-v2を別データとして作成**：真偽ラベルの層化、未見テンプレート、難易度区分、複合問題、十分な学習件数を追加する。v1は保存する。
2. **対照を追加**：定数回答とルールによる診断対照、意味上の正解と形式遵守の分離を新プロトコルで登録する。
3. **Coreの床効果を確認**：容易な問題でも誤答が多い条件で、専門化の失敗を構造全体の失敗と解釈しない。学習用データ、prompt、Coreサイズの変更は別IDで試す。
4. **本比較を事前登録**：単一LoRA対4専門LoRAの総token、active容量と総容量の対照、3 seed、費用上限、品質基準を固定する。

H4の昇格研究に必要な連携履歴は、専門モジュールが動作してから収集する。今回のCore単独結果から昇格の有効性は判断できない。

## 失敗と環境上の注意

run-01はモデルload時、既存のlibrosa／numbaのcache書き込み制限によりfailedとなった。予測は生成されていない。この失敗を保存したまま、許可された制限外実行でrun-02／run-03を完了した。検証スクリプトも同じ制限で一度停止し、その後同じ権限で完了した。

音声依存の非推奨警告とoptional C++ extensionのversion警告も出たが、CPU eagerの評価は完了した。既存の共有Python環境は変更していない。音声等の不要な依存がない隔離環境の再現確認は今後の作業。現在のoptional dependenciesはコアライブラリの指定であり、全依存のlockfileではない。

## 保存成果物

- [run-01失敗記録](../../results/MMIA-R001/run-01/manifest.json)
- [run-02個別結果](../../results/MMIA-R001/run-02/predictions.jsonl)／[集計](../../results/MMIA-R001/run-02/summary.json)／[実行条件](../../results/MMIA-R001/run-02/manifest.json)
- [run-03個別結果](../../results/MMIA-R001/run-03/predictions.jsonl)／[集計](../../results/MMIA-R001/run-03/summary.json)／[実行条件](../../results/MMIA-R001/run-03/manifest.json)
- [一致検証結果](../../results/MMIA-R001/verification.json)
- [固定設定](../../configs/pilot-core.json)／[人工データ](../../datasets/pilot-v1.jsonl)

## English / 简体中文

**English:** The Core-only pilot completed 24 validation examples twice, with identical tokens and grades. All outputs also matched Transformers.generate under the same greedy settings. Strict integer-only accuracy was 5/24 (20.8%). These are eight semantic groups in three languages, not 24 independent problems. The logic subset contains only true cases. The harness pilot passed, but data improvements are required before specialist training. No cost-reduction claim is supported yet.

**简体中文：** Core单模型试验两次完成24条验证样本，token与评分完全一致，同一贪心设置下也与Transformers.generate一致。严格整数格式下正确率为5/24（20.8%）。这些样本是8组语义问题的三语版本，不是24个独立问题；逻辑子集只有真命题。评估框架的初步验证通过，但需先改进数据，再开展专家训练。目前没有证明成本降低。
