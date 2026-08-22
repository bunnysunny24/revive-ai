# Five-Minute Pitch Script

## 0:00-0:30 - Problem

Failed payments are not just payment events. They are leaked revenue. A merchant may know that a payment failed, but the harder question is what to do next, whether it is safe to do it automatically, and whether the action recovered money.

## 0:30-1:30 - Demo

This is ReviveAI. It analyzed a synthetic batch of failed payments, identified the highest recovery opportunities, and ranked them by recovery probability. For this payment, the system shows the amount, failure type, root cause, recommended intervention, policy decision, and audit trail.

Now I execute recovery. The action goes through the Razorpay test adapter only after the policy engine approves it. The result is recorded immediately in the audit trail.

## 1:30-2:30 - Architecture

The architecture is data to ML to agent to policy to Razorpay to outcome measurement. The important decision is that the AI recommends, but deterministic policy controls all financial actions.

The risk engine estimates recovery likelihood. The diagnosis agent explains the likely root cause. The planner proposes retry, payment link, or escalation. The policy engine checks retry limits, amount limit, customer opt-out, cooldown, and current payment state.

## 2:30-3:30 - Evaluation

I evaluate ReviveAI on 10,000 synthetic payment records. The report includes precision, recall, F1, false-positive cost, recovered revenue, recovery rate, human escalation rate, policy blocks, and policy violations.

The main business metric is recovered revenue across the batch, not just model accuracy.

## 3:30-4:15 - Failure Handling

I intentionally simulate a Razorpay test API timeout. ReviveAI records the provider failure, avoids retry loops, preserves retry budget, and escalates the case to a human operator. The audit trail shows exactly what happened.

## 4:15-5:00 - Closing

The main idea is controlled autonomy. ReviveAI closes the loop from detection to recovery, but it keeps every money action explainable, bounded, gated, and auditable. That is the difference between an AI demo and a financial workflow I would be willing to trust.
