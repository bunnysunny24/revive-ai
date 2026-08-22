import json
import math
from pathlib import Path

from .models import PaymentEvent, RiskScore


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "risk_model.json"

FAILURE_TYPES = [
    "bank_timeout",
    "technical_error",
    "issuer_decline",
    "insufficient_funds",
    "expired_method",
    "mandate_failure",
    "checkout_abandonment",
]


def features(payment: PaymentEvent) -> list[float]:
    amount_scaled = min(payment.amount / 25000, 1.0)
    base = [
        1.0,
        amount_scaled,
        min(payment.previous_successes / 12, 1.0),
        min(payment.previous_failures / 5, 1.0),
        min(payment.attempts / 3, 1.0),
        1.0 if payment.subscription_active else 0.0,
        1.0 if payment.checkout_abandoned else 0.0,
        1.0 if payment.customer_opted_out else 0.0,
        1.0 if payment.last_attempt_minutes <= 60 else 0.0,
    ]
    return base + [1.0 if payment.failure_type == failure_type else 0.0 for failure_type in FAILURE_TYPES]


def sigmoid(value: float) -> float:
    if value < -35:
        return 0.0
    if value > 35:
        return 1.0
    return 1 / (1 + math.exp(-value))


def predict_probability(payment: PaymentEvent, weights: list[float]) -> float:
    return sigmoid(sum(weight * feature for weight, feature in zip(weights, features(payment))))


def train_model(payments: list[PaymentEvent], epochs: int = 220, learning_rate: float = 0.18) -> dict:
    if not payments:
        raise ValueError("Cannot train on an empty payment list.")

    weights = [0.0 for _ in features(payments[0])]
    for _ in range(epochs):
        gradients = [0.0 for _ in weights]
        for payment in payments:
            expected = 1.0 if payment.expected_recoverable else 0.0
            predicted = predict_probability(payment, weights)
            error = predicted - expected
            for index, feature in enumerate(features(payment)):
                gradients[index] += error * feature

        for index, gradient in enumerate(gradients):
            weights[index] -= learning_rate * gradient / len(payments)

    return {
        "model_type": "pure_python_logistic_regression",
        "feature_order": [
            "bias",
            "amount_scaled",
            "previous_successes_scaled",
            "previous_failures_scaled",
            "attempts_scaled",
            "subscription_active",
            "checkout_abandoned",
            "customer_opted_out",
            "recent_attempt",
            *[f"failure_type={failure_type}" for failure_type in FAILURE_TYPES],
        ],
        "weights": [round(weight, 6) for weight in weights],
    }


def save_model(model: dict) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2), encoding="utf-8")


def load_model() -> dict | None:
    if not MODEL_PATH.exists():
        return None
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def score_with_model(payment: PaymentEvent, model: dict | None = None) -> RiskScore:
    loaded_model = model or load_model()
    if loaded_model is None:
        raise FileNotFoundError("Train the risk model with scripts/evaluate.py first.")

    feature_vector = features(payment)
    probability = round(predict_probability(payment, loaded_model["weights"]), 3)

    if probability >= 0.75:
        priority = "HIGH"
    elif probability >= 0.48:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return RiskScore(
        probability=probability,
        priority=priority,
        features={
            "model_type": loaded_model["model_type"],
            "amount_scaled": round(feature_vector[1], 3),
            "success_history": round(feature_vector[2], 3),
            "failure_history": round(feature_vector[3], 3),
        },
    )
