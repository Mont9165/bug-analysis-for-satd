# LLM4SZZ結果の分析・集約

LLM4SZZ実行後の結果を集約・分析するためのガイド

## 📊 進捗確認

### 実行中の進捗チェック

```bash
# 全プロジェクトの進捗確認
./scripts/check_progress.sh

# 特定プロジェクトのみ
./scripts/check_progress.sh jfreechart
```

**出力例：**
```
📊 jfreechart
   Expected: 74 commits
   Processed: 40 commits (54.1%)
   JSON files: 116
   🔄 IN PROGRESS
```

### リアルタイムログ監視

```bash
# ログファイルをリアルタイム表示
tail -f logs/llm4szz_*.out

# 特定プロジェクト
tail -f logs/llm4szz_jfreechart_*.out

# エラーログ
tail -f logs/llm4szz_*.err
```

### ジョブ状態確認

```bash
# 自分のジョブ確認
squeue -u $USER

# 詳細情報
sacct -j <JOB_ID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS
```

## 📦 結果の集約

### 単一プロジェクトの集約

```bash
# JSON出力
python scripts/aggregate_llm4szz_results.py \
  --project jfreechart \
  --output results/jfreechart_results.json

# JSON + CSV出力
python scripts/aggregate_llm4szz_results.py \
  --project jfreechart \
  --output results/jfreechart_results.json \
  --export-csv
```

### 全プロジェクトの集約

```bash
# 全8プロジェクトを一括集約
mkdir -p results

python scripts/aggregate_llm4szz_results.py \
  --all \
  --output results/all_projects_results.json \
  --export-csv
```

## 📄 出力ファイル形式

### JSON形式

```json
{
  "jfreechart": {
    "commits": {
      "a27780c821ef9a3a07eff3c997c55e853ac6b6df": {
        "repo_name": "jfree/jfreechart",
        "bug_fixing_commit": "a27780c821ef...",
        "changed_files": [
          "src/main/java/org/jfree/chart/renderer/xy/XYLineAndShapeRenderer.java"
        ],
        "bug_inducing_commits": [
          "def456...",
          "ghi789..."
        ],
        "buggy_statements": [
          {
            "file": "XYLineAndShapeRenderer.java",
            "statement": "public int hashCode() {"
          }
        ],
        "can_determine": true,
        "total_token_cost": 0,
        "total_llm_calls": 9,
        "total_elapsed_time": 92.11
      }
    },
    "summary": {
      "project": "jfreechart",
      "total_bug_fixing_commits": 74,
      "determined_commits": 65,
      "determination_rate": "87.8%",
      "total_bug_inducing_commits": 130,
      "avg_bug_inducing_per_fix": "2.00",
      "total_buggy_statements": 245
    }
  }
}
```

### CSV形式

| Project | Repo | Bug-Fixing Commit | Changed Files | Can Determine | Bug-Inducing Commits | Num Bug-Inducing | Num Buggy Statements |
|---------|------|-------------------|---------------|---------------|---------------------|------------------|---------------------|
| jfreechart | jfree/jfreechart | a27780c8... | XYLine...java | TRUE | def456;ghi789 | 2 | 1 |

## 📈 統計情報

集約スクリプトは以下の統計を自動生成します：

### プロジェクト別統計

- **Total bug-fixing commits**: 分析対象のbug-fixing commit数
- **Determined commits**: bug-inducing commitを特定できた数
- **Determination rate**: 特定成功率（%）
- **Total bug-inducing commits**: 特定されたbug-inducing commitの総数
- **Avg bug-inducing per fix**: 1つのbug-fixに対する平均bug-inducing commit数
- **Total buggy statements**: 特定されたバグのあるステートメント数

### 全体統計（複数プロジェクト集約時）

- 全プロジェクトの合計
- 平均特定成功率
- プロジェクト間の比較

## 🔍 結果の分析例

### Python での後処理

```python
import json
import pandas as pd

# JSON読み込み
with open('results/all_projects_results.json', 'r') as f:
    results = json.load(f)

# プロジェクト別サマリー抽出
summaries = []
for project, data in results.items():
    summary = data['summary']
    summaries.append({
        'project': project,
        'total': summary['total_bug_fixing_commits'],
        'determined': summary['determined_commits'],
        'rate': float(summary['determination_rate'].rstrip('%'))
    })

df = pd.DataFrame(summaries)
print(df.sort_values('rate', ascending=False))
```

### CSV での分析

```bash
# CSVをExcel/Googleスプレッドシートで開く
# または
# pandasで分析
python -c "
import pandas as pd
df = pd.read_csv('results/all_projects_results.csv')
print(df.describe())
print(df.groupby('Project')['Num Bug-Inducing'].mean())
"
```

## 🎯 次のステップ

結果集約後：

1. **データ検証**: 結果の妥当性確認
   ```bash
   # 期待値と実際の処理数を比較
   ./scripts/check_progress.sh
   ```

2. **統計分析**: プロジェクト間の比較、傾向分析

3. **SATD分析への引き渡し**:
   - bug-fixing commits
   - bug-inducing commits
   - buggy statements

   の3つの情報を含むデータセットを作成

4. **論文用データ作成**: LaTeX表、グラフ用のデータエクスポート

## 📝 トラブルシューティング

### 一部のコミットが処理されていない

```bash
# 未処理のコミットを特定
python scripts/find_missing_commits.py --project jfreechart

# 未処理分のみ再実行
sbatch --export=PROJECT=jfreechart,START=40,END=74 scripts/cluster/run_llm4szz.sh
```

### 結果ファイルが見つからない

```bash
# save_logsディレクトリの存在確認
ls -la llm4szz_datasets/*/save_logs/

# 権限確認
ls -ld llm4szz_datasets/jfreechart/
```

### メモリ不足・処理失敗

- ログファイルでエラー確認
- 必要に応じて並列度を下げる（PARALLEL=3など）
- 大きいプロジェクトを分割処理
