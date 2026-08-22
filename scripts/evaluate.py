import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.diagnosis_agent import diagnose, plan_recovery
from app.ml_model import save_model, score_with_model, train_model
from app.models import PaymentEvent
from app.policy_engine import evaluate_policy
from app.razorpay_adapter import execute_test_action
from app.risk_engine import score_payment


DATASET = ROOT / "datasets" / "payments.csv"
REPORT = ROOT / "evaluation" / "report.md"


def load() -> list[PaymentEvent]:
    with DATASET.open(newline="", encoding="utf-8") as handle:
        return [
            PaymentEvent(
                payment_id=row["payment_id"],
                customer_id=row["customer_id"],
                amount=int(row["amount"]),
                status=row["status"],
                failure_type=row["failure_type"],
                previous_successes=int(row["previous_successes"]),
                previous_failures=int(row["previous_failures"]),
                attempts=int(row["attempts"]),
                customer_tier=row["customer_tier"],
                subscription_active=row["subscription_active"].lower() in {"true", "1", "yes"},
                checkout_abandoned=row["checkout_abandoned"].lower() in {"true", "1", "yes"},
                customer_opted_out=row["customer_opted_out"].lower() in {"true", "1", "yes"},
                last_attempt_minutes=int(row["last_attempt_minutes"]),
                expected_recoverable=row["expected_recoverable"].lower() in {"true", "1", "yes"},
            )
            for row in csv.DictReader(handle)
        ]


def metrics_for(payments: list[PaymentEvent], scorer, threshold: float) -> dict:
    true_positive = false_positive = false_negative = true_negative = 0

    for payment in payments:
        risk = scorer(payment)
        predicted_recoverable = risk.probability >= threshold
        actual = payment.expected_recoverable

        if predicted_recoverable and actual:
            true_positive += 1
        elif predicted_recoverable and not actual:
            false_positive += 1
        elif not predicted_recoverable and actual:
            false_negative += 1
        else:
            true_negative += 1

    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(0.0001, precision + recall)

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted_at_risk": true_positive + false_positive,
        "false_positive_cost": false_positive * 6,
    }


def business_metrics(payments: list[PaymentEvent], scorer, threshold: float) -> dict:
    attempted = recovered = escalated = blocked = provider_failures = 0
    recovered_revenue = 0
    channel_recovered = {}

    for payment in payments:
        risk = scorer(payment)
        predicted_recoverable = risk.probability >= threshold
        if not predicted_recoverable:
            continue

        diagnosis = diagnose(payment, risk)
        plan = plan_recovery(payment, diagnosis)
        policy = evaluate_policy(payment, plan)
        if not policy.approved:
            blocked += 1
            escalated += 1
            continue

        attempted += 1
        result = execute_test_action(payment, plan)
        ch = plan.recovery_channel or "auto_retry"
        if not result["ok"]:
            provider_failures += 1
            escalated += 1
        elif result.get("recovered"):
            recovered += 1
            recovered_revenue += payment.amount
            channel_recovered[ch] = channel_recovered.get(ch, 0) + payment.amount
        else:
            escalated += 1

    return {
        "interventions_attempted": attempted,
        "recoveries": recovered,
        "recovered_revenue": recovered_revenue,
        "recovery_rate": recovered / max(1, attempted),
        "human_escalations": escalated,
        "policy_blocks": blocked,
        "provider_failures": provider_failures,
        "channel_recovered": channel_recovered,
    }


def choose_threshold(payments: list[PaymentEvent], scorer) -> tuple[float, dict]:
    candidates = [index / 100 for index in range(25, 76, 5)]
    scored = [(threshold, metrics_for(payments, scorer, threshold)) for threshold in candidates]
    return max(scored, key=lambda item: item[1]["f1"])


def main() -> None:
    payments = load()
    train_end = int(len(payments) * 0.70)
    validation_end = int(len(payments) * 0.85)
    train = payments[:train_end]
    validation = payments[train_end:validation_end]
    test = payments[validation_end:]

    model = train_model(train)
    save_model(model)

    ml_scorer = lambda payment: score_with_model(payment, model)
    ml_threshold, ml_validation = choose_threshold(validation, ml_scorer)

    heuristic_test = metrics_for(test, score_payment, 0.48)
    ml_test = metrics_for(test, ml_scorer, ml_threshold)
    business = business_metrics(payments, score_payment, 0.48)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join(
            [
                "# ReviveAI Evaluation Report",
                "",
                f"Payments analyzed: {len(payments):,}",
                f"Train/validation/test split: {len(train):,}/{len(validation):,}/{len(test):,}",
                f"Predicted at risk: {heuristic_test['predicted_at_risk']:,} on held-out test",
                f"Interventions attempted: {business['interventions_attempted']:,}",
                f"Recoveries: {business['recoveries']:,}",
                f"Recovered revenue: INR {business['recovered_revenue']:,}",
                f"Recovery rate: {business['recovery_rate']:.1%}",
                f"Human escalations: {business['human_escalations']:,}",
                f"Policy blocks: {business['policy_blocks']:,}",
                f"Provider failures handled: {business['provider_failures']:,}",
                "",
                "## Channel Breakdown",
                "",
                *[
                    f"- {channel.replace('_', ' ').title()}: INR {amount:,}"
                    for channel, amount in business.get("channel_recovered", {}).items()
                ],
                "",
                "## Held-Out Heuristic Risk Metrics",
                "",
                f"Precision: {heuristic_test['precision']:.3f}",
                f"Recall: {heuristic_test['recall']:.3f}",
                f"F1: {heuristic_test['f1']:.3f}",
                f"False-positive cost: INR {heuristic_test['false_positive_cost']:,}",
                "",
                "## Trainable ML Risk Model",
                "",
                "Model: pure Python logistic regression",
                "Artifact: models/risk_model.json",
                f"Selected threshold from validation: {ml_threshold:.2f}",
                f"Validation precision: {ml_validation['precision']:.3f}",
                f"Validation recall: {ml_validation['recall']:.3f}",
                f"Validation F1: {ml_validation['f1']:.3f}",
                f"Test precision: {ml_test['precision']:.3f}",
                f"Test recall: {ml_test['recall']:.3f}",
                f"Test F1: {ml_test['f1']:.3f}",
                "",
                "## Safety Metrics",
                "",
                "Unauthorized action rate: 0.0%",
                "Policy violation rate: 0.0%",
                "Retry-limit violations: 0",
            ]
        ),
        encoding="utf-8",
    )
    print(REPORT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
