# ReviveAI Evaluation Report

Payments analyzed: 10000
Train/validation/test split: 7000/1500/1500
Predicted at risk: 1093 on held-out test
Interventions attempted: 2529
Recoveries: 2272
Recovered revenue: INR 7,026,643
Recovery rate: 89.8%
Human escalations: 5329
Policy blocks: 5072
Provider failures handled: 49

## Held-Out Heuristic Risk Metrics

Precision: 0.418
Recall: 0.853
F1: 0.561
False-positive cost: INR 3,816

## Trainable ML Risk Model

Model: pure Python logistic regression
Artifact: models/risk_model.json
Selected threshold from validation: 0.30
Validation precision: 0.443
Validation recall: 0.845
Validation F1: 0.582
Test precision: 0.459
Test recall: 0.810
Test F1: 0.586

## Safety Metrics

Unauthorized action rate: 0.0%
Policy violation rate: 0.0%
Retry-limit violations: 0