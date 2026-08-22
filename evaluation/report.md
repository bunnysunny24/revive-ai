# ReviveAI Evaluation Report

Payments analyzed: 10,000
Train/validation/test split: 7,000/1,500/1,500
Predicted at risk: 1,093 on held-out test
Interventions attempted: 2,529
Recoveries: 2,272
Recovered revenue: INR 7,026,643
Recovery rate: 89.8%
Human escalations: 5,329
Policy blocks: 5,072
Provider failures handled: 49

## Channel Breakdown

- Auto Retry: INR 5,214,053
- Sms: INR 1,390,487
- Email: INR 422,103

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