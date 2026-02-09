# bug-analysis-for-satd

Bug analysis pipeline for Self-Admitted Technical Debt (SATD) research.

## HPC Cluster Usage (SLURM)

### Prerequisites
- Singularity/Apptainer installed
- LLM4SZZ Singularity image at `~/singularity_images/llm4szz.sif`
- LLM4SZZ repository cloned at `~/LLM4SZZ`

### Submit Full Pipeline Job
```bash
./scripts/cluster/submit_job.sh \
  --repo-url https://github.com/owner/repo \
  --branch main \
  --model Qwen/Qwen3-8B \
  --parallel 5
```

### Submit LLM4SZZ-Only Job
```bash
./scripts/cluster/submit_job.sh \
  --llm4szz-only \
  --input output/bug_fixing_commits.json \
  --start 0 \
  --end 1000
```

### Direct SLURM Submission
```bash
# Set environment variables and submit
export REPO_URL="https://github.com/owner/repo"
export BRANCH="main"
sbatch scripts/cluster/run_pipeline_gpu.sh
```

### Monitor Jobs
```bash
squeue -u $USER
tail -f logs/bug_analysis_*.out
```

## Directory Structure

```
bug-analysis-for-satd/
├── scripts/
│   ├── extract_bug_fixing_commits.py
│   ├── run_llm4szz_analysis.py
│   ├── full_pipeline.py
│   └── cluster/
│       ├── run_pipeline_gpu.sh      # Full pipeline SLURM script
│       ├── run_llm4szz_only.sh      # LLM4SZZ-only SLURM script
│       └── submit_job.sh            # Job submission helper
├── logs/                             # SLURM log files (gitignored)
└── ...
```

## Features

### HPC Cluster Scripts
- **Auto-resubmit**: Jobs automatically resubmit if they exceed the minimum runtime threshold
- **GPU Support**: SLURM scripts configured for GPU-enabled nodes (isgpu2h200_long partition)
- **Singularity/Apptainer**: Containerized execution for reproducibility
- **Flexible Configuration**: Environment variables for easy customization
- **Job Management**: Helper scripts for easy job submission and monitoring

### Based On
- [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ) - Bug-introducing commit identification using LLMs
- Original reference: https://github.com/Mont9165/LLM4SZZ/blob/main/run_isgpu.sh