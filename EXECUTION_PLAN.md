# LLM4SZZ Execution Plan - Phase 2

## 目標
1週間以内に全8プロジェクト（8,331 bug-fixing commits）のbug-inducing commit特定を完了

## モデル
**Qwen2.5-Coder-3B-Instruct** (軽量モデル)
- 理由: 高速処理、GPU メモリ効率的
- 推定速度: 5-10秒/commit

## データセット準備状況

✅ **完了** - 全8プロジェクトのデータセット作成済み

| プロジェクト | Bug-Fixing Commits | データセット | リポジトリ |
|-------------|-------------------|------------|-----------|
| commons-lang | 424 | ✅ | ✅ |
| commons-io | 232 | ✅ | ✅ |
| hibernate-orm | 3,199 | ✅ | ✅ |
| dubbo | 1,503 | ✅ | ✅ |
| spoon | 1,152 | ✅ | ✅ |
| maven | 1,030 | ✅ | ✅ |
| storm | 717 | ✅ | ✅ |
| jfreechart | 74 | ✅ | ✅ |
| **合計** | **8,331** | | |

データセット場所: `~/bug-analysis-for-satd/llm4szz_datasets/`

## 実行方法

### オプション1: 全プロジェクト一括投入（推奨）

```bash
cd ~/bug-analysis-for-satd
./scripts/cluster/submit_llm4szz_batch.sh
```

**結果**: 8個のSLURMジョブが投入され、並列実行されます

### オプション2: 特定プロジェクトのみ

```bash
# 小さいプロジェクトでテスト
./scripts/cluster/submit_llm4szz_batch.sh jfreechart commons-io

# 大きいプロジェクトのみ
./scripts/cluster/submit_llm4szz_batch.sh hibernate-orm dubbo
```

### オプション3: 手動投入（デバッグ用）

```bash
# jfreechartでテスト (74 commits)
sbatch --export=PROJECT=jfreechart,START=0,END=74,MODEL=Qwen/Qwen2.5-Coder-3B-Instruct,PARALLEL=5 \
  scripts/cluster/run_llm4szz.sh
```

## 処理時間見積もり

### 単一GPU、並列度5の場合

| プロジェクト | Commits | 最小時間 | 最大時間 |
|-------------|---------|---------|---------|
| jfreechart | 74 | 1分 | 2分 |
| commons-io | 232 | 4分 | 8分 |
| commons-lang | 424 | 7分 | 14分 |
| storm | 717 | 12分 | 24分 |
| maven | 1,030 | 17分 | 34分 |
| spoon | 1,152 | 19分 | 38分 |
| dubbo | 1,503 | 25分 | 50分 |
| hibernate-orm | 3,199 | 53分 | 107分 |
| **合計** | **8,331** | **~2.8時間** | **~5.6時間** |

### 8 GPU並列実行の場合

- **最小**: 約20-30分
- **最大**: 約40-60分

## ジョブ監視

### ジョブ状態確認
```bash
squeue -u $USER
```

### ログ確認
```bash
# リアルタイム監視
tail -f logs/llm4szz_*.out

# 特定プロジェクト
tail -f logs/llm4szz_commons-lang_*.out

# エラー確認
tail -f logs/llm4szz_*.err
```

### 進捗確認
```bash
# 各プロジェクトの出力ファイル数を確認
for project in commons-lang commons-io hibernate-orm dubbo spoon maven storm jfreechart; do
  count=$(find llm4szz_datasets/$project/output -name "*.json" 2>/dev/null | wc -l)
  expected=${EXPECTED_COUNTS[$project]}
  echo "$project: $count files"
done
```

## 出力結果

### 出力ディレクトリ構造
```
llm4szz_datasets/
├── commons-lang/
│   ├── dataset/issue_list.json (input)
│   ├── repos/commons-lang/ (repository)
│   └── output/ (LLM4SZZ results)
│       ├── <commit_hash>.json
│       ├── <commit_hash>.json
│       └── ...
├── commons-io/
│   └── ...
└── ...
```

### 結果ファイル形式
各コミットに対して1つのJSONファイルが生成されます：

```json
{
  "repo_name": "apache/commons-lang",
  "bug_fixing_commit": "abc123...",
  "bug_inducing_commits": ["def456...", "ghi789..."],
  "buggy_stmts": [
    {
      "file": "src/.../StringUtils.java",
      "line": 123,
      "code": "if (str == null) return null;"
    }
  ],
  "strategy_used": "s2",
  "can_determine": true
}
```

## トラブルシューティング

### GPU Out of Memory
```bash
# 並列度を下げる
sbatch --export=PROJECT=hibernate-orm,PARALLEL=3 scripts/cluster/run_llm4szz.sh
```

### ジョブがキューで待機
```bash
# パーティション確認
sinfo

# 自分のジョブ優先度確認
sprio -u $USER
```

### 途中から再開
```bash
# 500-1000番目のコミットを処理
sbatch --export=PROJECT=hibernate-orm,START=500,END=1000 scripts/cluster/run_llm4szz.sh
```

## 結果の集約（Phase 2完了後）

全ジョブ完了後、結果を集約します：

```bash
# 結果集約スクリプト（後で作成）
python scripts/aggregate_llm4szz_results.py \
  --input llm4szz_datasets \
  --output final_results
```

## チェックリスト

- [x] Phase 1完了 (bug-fixing commits抽出)
- [x] データセット変換 (LLM4SZZ形式)
- [x] 実行スクリプト作成
- [ ] テスト実行 (jfreechart)
- [ ] 全プロジェクト投入
- [ ] ジョブ監視
- [ ] 結果確認
- [ ] 結果集約
- [ ] SATD分析チームへ引き渡し

## 次のステップ

1. **今すぐテスト**: 小さいプロジェクトで動作確認
   ```bash
   ./scripts/cluster/submit_llm4szz_batch.sh jfreechart
   ```

2. **本番実行**: テスト成功後、全プロジェクト投入
   ```bash
   ./scripts/cluster/submit_llm4szz_batch.sh
   ```

3. **監視**: ログを確認しながら進捗監視

4. **結果集約**: 完了後、統合データセット作成
