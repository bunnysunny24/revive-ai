import argparse
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "datasets" / "payments.csv"

FAILURE_TYPES = [
    "bank_timeout",
    "technical_error",
    "issuer_decline",
    "insufficient_funds",
    "expired_method",
    "mandate_failure",
    "checkout_abandonment",
]


DEMO_ROWS = [
    {
        "payment_id": "DEMO_SUCCESS",
        "customer_id": "CUST9001",
        "amount": 8499,
        "status": "failed",
        "failure_type": "bank_timeout",
        "previous_successes": 9,
        "previous_failures": 0,
        "attempts": 1,
        "customer_tier": "vip",
        "subscription_active": "true",
        "checkout_abandoned": "false",
        "customer_opted_out": "false",
        "last_attempt_minutes": 45,
        "expected_recoverable": "true",
    },
    {
        "payment_id": "DEMO_BLOCKED",
        "customer_id": "CUST9002",
        "amount": 24999,
        "status": "failed",
        "failure_type": "checkout_abandonment",
        "previous_successes": 12,
        "previous_failures": 0,
        "attempts": 0,
        "customer_tier": "vip",
        "subscription_active": "true",
        "checkout_abandoned": "true",
        "customer_opted_out": "false",
        "last_attempt_minutes": 60,
        "expected_recoverable": "true",
    },
    {
        "payment_id": "DEMO_FAIL7",
        "customer_id": "CUST9003",
        "amount": 1999,
        "status": "failed",
        "failure_type": "technical_error",
        "previous_successes": 8,
        "previous_failures": 0,
        "attempts": 0,
        "customer_tier": "regular",
        "subscription_active": "true",
        "checkout_abandoned": "false",
        "customer_opted_out": "false",
        "last_attempt_minutes": 60,
        "expected_recoverable": "true",
    },
]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_row(index: int) -> dict:
    failure_type = random.choices(
        FAILURE_TYPES,
        weights=[18, 14, 16, 15, 12, 10, 15],
        k=1,
    )[0]
    previous_successes = random.randint(0, 12)
    previous_failures = random.randint(0, 5)
    amount = random.choice([499, 799, 1200, 1999, 2499, 4500, 8499, 12999, 24999])
    attempts = random.choices([0, 1, 2, 3], weights=[30, 45, 20, 5], k=1)[0]
    subscription_active = random.random() < 0.36
    checkout_abandoned = failure_type == "checkout_abandonment"
    customer_opted_out = random.random() < 0.035
    last_attempt_minutes = random.choice([10, 20, 30, 45, 60, 120, 360, 1440])
    customer_tier = random.choices(["new", "regular", "vip"], weights=[35, 50, 15], k=1)[0]

    recoverability = 0.18
    recoverability += 0.24 if failure_type in {"bank_timeout", "technical_error"} else 0
    recoverability += 0.14 if failure_type in {"checkout_abandonment", "mandate_failure"} else 0
    recoverability += min(previous_successes, 10) * 0.035
    recoverability -= previous_failures * 0.04
    recoverability -= 0.18 if customer_opted_out else 0
    recoverability -= 0.12 if amount > 10000 else 0
    recoverability -= 0.08 if attempts >= 2 else 0

    return {
        "payment_id": f"RPX{index:05d}",
        "customer_id": f"CUST{random.randint(1, 2200):04d}",
        "amount": amount,
        "status": "failed",
        "failure_type": failure_type,
        "previous_successes": previous_successes,
        "previous_failures": previous_failures,
        "attempts": attempts,
        "customer_tier": customer_tier,
        "subscription_active": bool_text(subscription_active),
        "checkout_abandoned": bool_text(checkout_abandoned),
        "customer_opted_out": bool_text(customer_opted_out),
        "last_attempt_minutes": last_attempt_minutes,
        "expected_recoverable": bool_text(random.random() < max(0.05, min(recoverability, 0.92))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generated_count = max(0, args.records - len(DEMO_ROWS))
    rows = DEMO_ROWS + [build_row(index) for index in range(1, generated_count + 1)]

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic payments to {OUTPUT}")


if __name__ == "__main__":
    main()
