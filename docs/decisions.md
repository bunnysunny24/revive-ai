# Engineering Decisions

## Track Choice

I chose Track 03, AI Revenue Recovery, because it creates a measurable business loop: detect lost revenue, choose an intervention, execute safely, and report recovered money.

## No Direct LLM Money Execution

LLMs are useful for diagnosis and explanation, but financial execution needs deterministic gates. ReviveAI makes the policy engine mandatory before any recovery action.

## Synthetic Data

Real payment data is sensitive and unavailable for a student buildathon. The project uses synthetic data with interpretable labels and stable seeds so evaluation is reproducible.

## Local Razorpay Simulator

The first version uses a local Razorpay-compatible test adapter to keep the demo runnable for every reviewer. The adapter is isolated so real test-mode calls can be added without changing the risk, policy, audit, or UI layers.

## Dependency-Light Stack

The current build uses Python standard library and static frontend assets. This reduces setup friction and makes the reviewer path:

```bash
python scripts/generate_dataset.py
python scripts/evaluate.py
python backend/server.py
```
