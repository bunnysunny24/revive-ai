# Demo Checklist

Run locally:
```bash
python scripts/generate_dataset.py --records 10000
python scripts/evaluate.py
python -m unittest discover -s tests -v
python backend/server.py
```

Then open locally `http://localhost:8000` or use the live deployment:
```text
https://revive-ai-hlmx.onrender.com
```


## Recording Flow

1. Show the dashboard and explain the problem in one sentence.
2. Click `Run Batch` and point to recovered revenue, recovery rate, escalations, and zero policy violations.
3. Execute one approved high-priority payment recovery.
4. Show `DEMO_BLOCKED` and explain the INR 10,000 automatic-action limit.
5. Show `DEMO_FAIL7`, execute recovery, and point to provider failure escalation in the audit trail.
6. Close with the architecture line: AI recommends, policy controls.

## Reviewer Signals To Say Out Loud

- This is Track 03, AI Revenue Recovery.
- The main metric is recovered money across a batch.
- Every money action is explainable, bounded, gated, and audited.
- Provider failure does not trigger runaway retries.
