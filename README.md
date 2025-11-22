# Prompt Quality Experiment

## Project Structure

```
3036654455/
├── experiments/prompt_quality/    # Prompt quality experiment modules
│   ├── corrupted_demonstrations.py
│   ├── quality_method.py
│   ├── run_quality_experiments.py
│   └── quality_analyzer.py
├── data/                          # Data and configuration
│   ├── config.py                 # API keys and model configuration
│   ├── test.jsonl                # Test dataset
│   └── train.jsonl               # Training dataset
├── output/                        # Experiment results
│   ├── results/                  # Detailed results (JSONL files)
│   ├── summary/                  # Summary statistics
│   └── quality_experiment_report.md
├── core/                         # Core modules
│   ├── llm_client.py            # LLM API client
│   ├── evaluation.py            # Evaluation functions
│   └── baseline.py              # Baseline methods
├── methods/                      # Method implementations
│   ├── base_method.py
│   ├── zero_shot_method.py
│   ├── few_shot_method.py
│   └── ...
├── analysis/                     # Analysis tools
│   ├── accuracy_analyzer.py
│   ├── cost_analyzer.py
│   └── method_comparator.py
├── processing/                   # Processing utilities
│   └── concurrent_processor.py
├── main.py                       # Main entry point
└── requirements.txt             # Dependencies
```

## Running Full Experiments

### Run All Experiments

```bash
# Run all 10 experimental groups on full dataset
python experiments/prompt_quality/run_quality_experiments.py   --experiment all   --verbose
```

### Run Individual Experiment

```bash
# Run a specific experiment
python experiments/prompt_quality/run_quality_experiments.py   --experiment  baseline   --max-questions 10
```

### Generate Analysis Report

```bash
# Generate comparison report after experiments
python experiments/prompt_quality/quality_analyzer.py
```

## Experimental Groups

| Group | Dimension | Description |
|-------|-----------|-------------|
| baseline | Baseline | Correct demonstrations |
| wrong_answer | Correctness | Incorrect answer |
| wrong_reasoning | Correctness | Incorrect reasoning |
| completely_wrong | Correctness | Both incorrect |
| irrelevant | Relevance | Unrelated demonstrations |
| partially_relevant | Relevance | Partially related |
| mixed_50_50 | Relevance | 50% relevant + 50% irrelevant |
| format_inconsistent | Format | Inconsistent format |
| format_missing | Format | Missing format markers |
| format_chaotic | Format | Chaotic format |

## Output Files

- Results: `output/results/quality_*.jsonl`
- Report: `output/quality_experiment_report.md`

## Configuration

Edit `data/config.py` to configure:
- API keys
- Model parameters (temperature, top-p)
- Dataset paths
