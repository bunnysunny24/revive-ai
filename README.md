# ReviveAI

> **AI Revenue Recovery Engine** — Built for the **Razorpay AI Buildathon (Track 03)**.
> Detect revenue at risk, diagnose root causes, select bounded recovery workflows, enforce deterministic policy guardrails, and execute through Razorpay test adapters with immutable audit trails.

![Track 03 Badge](https://img.shields.io/badge/Track%2003-AI%20Revenue%20Recovery-0b5fff?style=for-the-badge)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Python%20Stdlib)-107e4a?style=for-the-badge)
![Test Status](https://img.shields.io/badge/Unit%20Tests-15%2F15%20Passing-107e4a?style=for-the-badge)
![Safety Compliance](https://img.shields.io/badge/Policy%20Violations-0.0%25-107e4a?style=for-the-badge)

---

## 🎯 Track 03: The Core Closed Loop

```
Detect -> Diagnose -> Decide -> Gate (Policy) -> Act (Razorpay) -> Measure -> Audit
```

| Requirement | ReviveAI Implementation |
| :--- | :--- |
| **Detect revenue at risk** | Dual risk scoring: Trainable Logistic Regression (`F1: 0.586`) + Heuristic Baseline (`F1: 0.561`) ranking failed payments, checkout drop-offs, and subscription failures. |
| **Determine intervention** | Contextual Diagnosis Agent recommends delayed retry, payment recovery link (SMS/Email), or human escalation with customer-aware reasoning. |
| **Execute bounded workflow** | 6-Gate Deterministic Policy Engine validates amount caps, retry budgets, cooldown windows, customer consent, and double-charge prevention before execution. |
| **Measured money recovered** | Evaluated on a 10,000-payment batch: **INR 7,026,643** recovered across 2,272 payments (**89.8% recovery rate**). |
| **Compliant escalation** | High-ticket items (>INR 10,000), opt-outs, exhausted retry budgets, and provider 504 timeouts safely escalate to human review. |
| **Stopping rules** | Strict amount thresholds, max retry limits (2), 30-minute cooldown windows, customer opt-out blocking, and idempotent state checks. |
| **Audit trail** | Chronological, immutable audit events recorded for every ingestion, policy gate, gateway execution, provider failure, and recovery. |

---

## 📊 Evaluation & Benchmark Metrics (10,000 Batch)

Run `python scripts/evaluate.py` to train the model artifact and reproduce the benchmark:

```text
======================================================================
Payments Analyzed:              10,000
Train / Validation / Test:      7,000 / 1,500 / 1,500
Interventions Attempted:        2,529
Successful Recoveries:          2,272
Total Recovered Revenue:        INR 7,026,643
Batch Recovery Rate:            89.8%
Human Escalations:              5,329
Policy Gating Blocks:           5,072
Handled Provider 504 Failures:  49
======================================================================
Channel Breakdown:
  • Auto Retry:                 INR 5,214,053
  • SMS Recovery Link:          INR 1,390,487
  • Email Recovery Link:        INR 422,103
======================================================================
Machine Learning (Held-Out Test Set):
  • Trainable Logistic Model:   Precision: 0.459 | Recall: 0.810 | F1: 0.586
  • Heuristic Baseline:         Precision: 0.418 | Recall: 0.853 | F1: 0.561
  • Threshold Selected:         0.30 (tuned on validation split)
======================================================================
Safety & Control Metrics:
  • Unauthorized Actions:       0.0%
  • Policy Violations:          0
  • Retry Limit Violations:     0
======================================================================
```

---

## 🛡️ Architecture & Security: "AI Recommends. Policy Controls."

ReviveAI strictly decouples **intelligence** from **monetary authority**:

```
Synthetic Payment Events
  └──> Risk Scoring Engine (Trainable Logistic ML + Heuristic Scorer)
         └──> Contextual Diagnosis Agent (Root-cause classification + dynamic reasoning)
                └──> Recovery Planner (Action, channel, retry budget & cooldown sequencer)
                       └──> 6-Gate Deterministic Policy Engine (Amount, Consent, Budget, Cooldown, Idempotency)
                              ├── [Approved] ──> Razorpay Test Adapter ──> Outcome Tracker
                              └── [Blocked]  ──> Safe Escalation / Stop
                                     └──> Immutable Audit Log ──> Evaluation KPI Engine
```

### Security & Hardening Highlights
1. **Zero Path Traversal Vulnerability**: Server strictly enforces path boundaries with `Path.resolve()` and `is_relative_to()`.
2. **Thread Safety**: Central repository and audit trails are protected by re-entrant thread locks (`threading.RLock`).
3. **Pure Python Standard Library**: Zero external pip dependencies ensures maximum portability, reproducible execution, and zero supply-chain risk.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (No `pip install` required!)

### 2. Generate Data & Train ML Model
```bash
python scripts/generate_dataset.py --records 10000
python scripts/evaluate.py
```

### 3. Run Unit Tests (15 Tests)
```bash
python -m unittest discover -s tests -v
```

### 4. Start the Application Server
```bash
python backend/server.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 🎥 Reviewer Demo Path & Presets

1. **Dashboard & Metrics**: Click **Run Recovery Batch** to witness autonomous revenue recovery across hundreds of cases with real-time KPI updates.
2. **Preset 1: `DEMO_SUCCESS`** — Transient bank timeout with VIP customer history. Diagnosis prescribes automated retry after cooldown. Passes all 6 policy gates and successfully captures revenue.
3. **Preset 2: `DEMO_BLOCKED`** — High-value checkout drop-off (INR 24,999). Policy engine blocks automatic execution because amount exceeds the INR 10,000 limit, routing to human high-touch sales.
4. **Preset 3: `DEMO_FAIL7`** — Simulated Razorpay 504 gateway timeout. System preserves the merchant retry budget, records the provider error in the audit log, and safely escalates to human review without looping.
5. **Audit Logs & Evaluation Views**: Explore immutable audit logs and side-by-side ML vs Heuristic tables directly in the top navigation tabs.

---

## 📂 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── diagnosis_agent.py   # Root cause diagnosis & dynamic reasoning
│   │   ├── http.py              # Secured HTTP server, CORS & static handler
│   │   ├── ml_model.py          # Pure Python Logistic Regression model
│   │   ├── models.py            # Strongly-typed dataclasses & AuditEvent
│   │   ├── policy_engine.py     # 6-gate deterministic policy guardrails
│   │   ├── razorpay_adapter.py  # Razorpay test mode simulator & link generator
│   │   ├── risk_engine.py       # Interpretable heuristic risk scorer
│   │   └── store.py             # Thread-safe in-memory state & audit index
│   └── server.py                # Server entry point
├── datasets/
│   └── payments.csv             # Synthetic 10,000 payment dataset (seed 42)
├── docs/
│   ├── application-answers.md   # Ready-to-paste Buildathon form answers
│   ├── architecture.md          # In-depth architectural design & diagrams
│   ├── decisions.md             # Key engineering trade-offs & rationales
│   ├── demo-checklist.md        # Video pitch recording flow & key talking points
│   ├── evaluation.md            # ML evaluation methodology & metric definitions
│   ├── failure-modes.md         # Detailed breakdown of provider failure recovery
│   └── pitch-script.md          # 5-minute timed video script
├── evaluation/
│   └── report.md                # Generated benchmark evaluation report
├── frontend/
│   ├── app.js                   # Interactive UI application logic & views
│   ├── index.html               # Main dashboard & workbench interface
│   └── styles.css               # Modern fintech styling & responsive design
├── models/
│   └── risk_model.json          # Serialized ML model weights & feature specs
├── scripts/
│   ├── evaluate.py              # ML training, threshold tuning & evaluation runner
│   └── generate_dataset.py      # Reproducible synthetic dataset generator
├── tests/
│   └── test_workflow.py         # 15 unit & integration tests
├── requirements.txt             # Zero-dependency specification
└── README.md
```
