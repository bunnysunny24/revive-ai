# Evaluation

ReviveAI is evaluated on a synthetic batch of failed payment events.

## Dataset

The generator creates 10,000 events by default:

```bash
python scripts/generate_dataset.py --records 10000
```

Each record includes:

- amount
- failure type
- previous successes
- previous failures
- retry attempts
- customer tier
- subscription state
- checkout abandonment
- opt-out state
- expected recoverability label

## Metrics

The evaluation reports three groups of metrics.

### ML Metrics

- Precision
- Recall
- F1
- False-positive cost

The script also trains a lightweight logistic regression model in pure Python and saves the learned weights to:

```text
models/risk_model.json
```

This keeps the project dependency-light while still showing a real train/validation/test ML workflow.

Latest seeded model result:

- validation-selected threshold: 0.30
- test precision: 0.459
- test recall: 0.810
- test F1: 0.586

### Business Metrics

- payments analyzed
- predicted at-risk payments
- interventions attempted
- recovered count
- recovered revenue
- recovery rate
- human escalation count

### Safety Metrics

- unauthorized action rate
- policy violation rate
- retry-limit violations

## Run

```bash
python scripts/evaluate.py
```

The generated report is written to:

```text
evaluation/report.md
```
