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

- **Payments Analyzed**: 10,000
- **Predicted At-Risk**: 1,093 (on held-out test split)
- **Interventions Attempted**: 2,529
- **Recovered Count**: 2,272
- **Recovered Revenue**: INR 7,026,643
- **Batch Recovery Rate**: 89.8%
- **Human Escalation Count**: 5,329
- **Policy Blocks**: 5,072
- **Handled Provider Failures**: 49

### Channel Breakdown

- **Auto Retry**: INR 5,214,053
- **SMS Recovery Link**: INR 1,390,487
- **Email Recovery Link**: INR 422,103

### Safety Metrics

- **Unauthorized Action Rate**: 0.0%
- **Policy Violation Rate**: 0.0%
- **Retry-Limit Violations**: 0


## Run

```bash
python scripts/evaluate.py
```

The generated report is written to:

```text
evaluation/report.md
```
