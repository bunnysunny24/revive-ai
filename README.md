# ReviveAI

> **AI Revenue Recovery Engine** — Built for the **Razorpay AI Buildathon (Track 03)**.
> Detect revenue at risk, diagnose root causes, select bounded recovery workflows, enforce deterministic policy guardrails, and execute through Razorpay test adapters with immutable audit trails.

![Track 03 Badge](https://img.shields.io/badge/Track%2003-AI%20Revenue%20Recovery-0b5fff?style=for-the-badge)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Python%20Stdlib)-107e4a?style=for-the-badge)
![Test Status](https://img.shields.io/badge/Unit%20Tests-15%2F15%20Passing-107e4a?style=for-the-badge)
![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-0b5fff?style=for-the-badge)

🌐 **Live Deployed Application**: [https://revive-ai-hlmx.onrender.com](https://revive-ai-hlmx.onrender.com)


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

## 🔍 Reviewer Evaluation Guide: Step-by-Step Verification

Judges and reviewers can evaluate all Track 03 capabilities in **under 5 minutes** either via the live web application at **[https://revive-ai-hlmx.onrender.com](https://revive-ai-hlmx.onrender.com)** or locally.

| Step | Action to Perform | Expected System Behavior & What to Check | Track 03 Requirement Verified |
| :--- | :--- | :--- | :--- |
| **1. Autonomous Batch Recovery** | Click the blue **"Run Recovery Batch"** button in the header. | The system processes hundreds of at-risk transactions. Real-time KPI metrics update immediately: **INR 7,026,643+ recovered**, **89.8% recovery rate**, multi-channel breakdown (Auto-retry, SMS, Email), and **0 policy violations**. | *Measured Money Recovered across Batch* |
| **2. Transient Failure Recovery** | Click the **`DEMO_SUCCESS`** chip in the demo strip. Click **"Execute Recovery Workflow"**. | For a VIP customer with 9 prior successes and a bank timeout, AI diagnoses a temporary rail glitch. All 6 policy checks turn green. Recovery succeeds, status transitions to `CAPTURED`, and a `revenue_recovered` audit event is emitted. | *Detection & Intervention Determination* |
| **3. High-Value Policy Gating** | Click the **`DEMO_BLOCKED`** chip in the demo strip. | High-ticket checkout abandonment for INR 24,999. Policy engine immediately halts automated outreach because it exceeds the INR 10,000 automatic limit. "Action Stopped" button is disabled and routed to human sales. | *Deterministic Stopping Rules & Policy Gating* |
| **4. Provider Failure Escalation** | Click the **`DEMO_FAIL7`** chip and click **"Execute Recovery Workflow"**. | Simulates a realistic **Razorpay 504 Gateway Timeout**. System catches the provider error, **preserves the merchant retry budget**, writes a `provider_failure_escalated` audit event, and safely routes to human review without looping. | *Compliant Escalation & Failure Recovery* |
| **5. Immutable Audit Trail** | Navigate to the **"Audit Logs"** tab in the sidebar. Filter by *Recovered*, *Gateway Action*, or *Blocked*. | Inspect chronological, UTC-timestamped audit records with full JSON metadata payloads for every transaction ingestion, policy evaluation, gateway attempt, and recovery. | *Immutable Audit Trail* |
| **6. ML Model & Safety Benchmarks** | Navigate to the **"Evaluation & ML"** tab in the sidebar. | View side-by-side benchmark tables comparing the pure-Python Logistic Regression model (`F1: 0.586`) with the heuristic baseline (`F1: 0.561`), safety verification checklist (0 violations), and raw report. | *Meaningful AI & ML Efficacy* |

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
