from typing import Optional


class PolicyEngine:
    """
    Converts sensitivity classification and security signals
    into a routing decision.

    Principle:
    ML predicts; policy decides.
    """

    def __init__(self, confidence_threshold: float = 0.60):
        self.confidence_threshold = confidence_threshold

    def decide(
        self,
        sensitivity_label: str,
        confidence: float,
        has_pii: bool = False,
        has_secret: bool = False,
        has_code: bool = False,
    ) -> dict:

        # ---------------------------------------------------------
        # Rule 1: Secrets always take priority.
        # ---------------------------------------------------------
        if has_secret:
            return {
                "decision": "BLOCK",
                "reason": "Sensitive secret or credential detected.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Rule 2: Low ML confidence -> fail safe to local.
        # ---------------------------------------------------------
        if confidence < self.confidence_threshold:
            return {
                "decision": "LOCAL",
                "reason": "ML classifier confidence is below threshold.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Rule 3: Confidential information stays local.
        # ---------------------------------------------------------
        if sensitivity_label == "Confidential":
            return {
                "decision": "LOCAL",
                "reason": "Confidential information detected.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Rule 4: Internal information stays local.
        # ---------------------------------------------------------
        if sensitivity_label == "Internal":
            return {
                "decision": "LOCAL",
                "reason": "Internal information detected.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Rule 5: PII -> local processing.
        # ---------------------------------------------------------
        if has_pii:
            return {
                "decision": "LOCAL",
                "reason": "Personally identifiable information detected.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Rule 6: Public information can use cloud.
        # ---------------------------------------------------------
        if sensitivity_label == "Public":
            return {
                "decision": "CLOUD",
                "reason": "Input classified as public and no blocking signals detected.",
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # ---------------------------------------------------------
        # Default: fail safe to local.
        # ---------------------------------------------------------
        return {
            "decision": "LOCAL",
            "reason": "No explicit cloud-safe policy matched; fail-safe to local.",
            "sensitivity": sensitivity_label,
            "confidence": confidence,
        }


if __name__ == "__main__":

    policy = PolicyEngine()

    test_cases = [
        {
            "name": "Public question",
            "sensitivity_label": "Public",
            "confidence": 0.90,
            "has_pii": False,
            "has_secret": False,
            "has_code": False,
        },
        {
            "name": "Internal document",
            "sensitivity_label": "Internal",
            "confidence": 0.90,
            "has_pii": False,
            "has_secret": False,
            "has_code": False,
        },
        {
            "name": "Confidential document",
            "sensitivity_label": "Confidential",
            "confidence": 0.90,
            "has_pii": False,
            "has_secret": False,
            "has_code": False,
        },
        {
            "name": "Secret credential",
            "sensitivity_label": "Secret",
            "confidence": 0.30,
            "has_pii": False,
            "has_secret": True,
            "has_code": False,
        },
        {
            "name": "Low-confidence prediction",
            "sensitivity_label": "Public",
            "confidence": 0.40,
            "has_pii": False,
            "has_secret": False,
            "has_code": False,
        },
    ]

    print("Policy Engine Tests")
    print("=" * 60)

    for case in test_cases:
        result = policy.decide(
            sensitivity_label=case["sensitivity_label"],
            confidence=case["confidence"],
            has_pii=case["has_pii"],
            has_secret=case["has_secret"],
            has_code=case["has_code"],
        )

        print(f"\nTest: {case['name']}")
        print(f"Sensitivity: {result['sensitivity']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")