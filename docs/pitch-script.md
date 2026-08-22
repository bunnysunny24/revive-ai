# Five-Minute Pitch Video Script (Track 03)

## 0:00 – 0:45: The Problem & The Core Insight
"Hi everyone, I'm presenting **ReviveAI** for **Track 03 — AI Revenue Recovery**.

Every day, online merchants lose significant revenue to payment failures, checkout drop-offs, and subscription declines. Most gateways merely notify merchants that a payment failed, leaving money on the table. But revenue loss rarely happens in a single step, and recovering it requires more than blindly spamming retries.

The central thesis of ReviveAI is: **The AI recommends, but the policy engine controls.** We close the loop from detection to diagnosis, bounded intervention, gateway execution, and measured revenue recovery — while enforcing strict financial guardrails."

---

## 0:45 – 2:00: Live Demo — The Autonomous Recovery Loop
*(Screen recording shows the ReviveAI dashboard at `http://localhost:8000`)*

"Here is the ReviveAI live dashboard. When I click **Run Recovery Batch**, the engine processes our 10,000-payment dataset in real time. Notice our metrics:
- Over **INR 7 Million recovered** across 2,272 transactions.
- An **89.8% recovery rate** on actionable interventions.
- Multi-channel attribution across Automated Retries, SMS Links, and Email Links.
- And critically: **0 policy violations and 0 unauthorized actions**.

Let's look at the **Recovery Console**:
1. **DEMO_SUCCESS**: For a VIP customer with 9 prior successes experiencing a transient bank timeout, ReviveAI diagnoses the root cause as temporary provider rails degradation. It checks all 6 policy gates — amount cap, customer consent, cooldown window, and retry budget — and autonomously executes recovery.
2. **DEMO_BLOCKED**: Here is a high-value checkout drop-off for INR 24,999. Our policy engine immediately stops automated execution because it exceeds the INR 10,000 limit, routing it to human high-touch sales instead of risking an unmonitored action."

---

## 2:00 – 3:15: Failure Recovery & Bounded Execution
"The buildathon specifically asks: *What broke, and how did you get out?*

Let me show you **DEMO_FAIL7**:
When we execute this transaction, we simulate a realistic **Razorpay 504 Gateway Timeout**. In an unconstrained AI system, this might trigger a runaway retry loop or double-charge the buyer. 

In ReviveAI, the failure is caught by our Razorpay adapter. It preserves the merchant retry budget, immediately records a `provider_failure_escalated` event in our immutable audit trail, and safely escalates the case to human review without looping."

---

## 3:15 – 4:15: Architecture & Machine Learning Efficacy
*(Navigate to the 'Evaluation & ML' tab)*

"Under the hood, ReviveAI uses a pure-Python, zero-dependency Logistic Regression model trained across a 70/15/15 train-validation-test split.
- Our trainable ML model achieves an **F1 score of 0.586** on strictly held-out test data, outperforming our interpretable baseline of 0.561.
- We tune the decision threshold systematically on validation data to minimize false-positive outreach costs.
- The entire application runs natively on the Python 3.10+ standard library with zero external pip dependencies."

---

## 4:15 – 5:00: Closing
"ReviveAI doesn't just identify revenue at risk — it wins it back with measured monetary impact, compliant escalation, deterministic stopping rules, and an immutable audit trail.

Thank you, and I look forward to your questions!"
