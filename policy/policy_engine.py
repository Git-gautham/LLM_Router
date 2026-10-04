class PolicyEngine:
    """
    Converts ML sensitivity predictions and deterministic
    security signals into a routing decision.

    Principle:
        ML predicts; policy decides.

    Routing policy:
        Secret detected       -> BLOCK
        PII detected          -> LOCAL
        Confidential          -> LOCAL
        Internal              -> LOCAL
        Public                -> CLOUD
        Unknown classification -> LOCAL

    Important:
        Low ML confidence alone does NOT force LOCAL.
        Deterministic security signals have higher priority.
    """

    def decide(
        self,
        sensitivity_label: str,
        confidence: float,
        has_pii: bool = False,
        has_secret: bool = False,
        has_code: bool = False,
    ) -> dict:

        # --------------------------------------------------
        # 1. HARD SECURITY RULE
        # --------------------------------------------------
        # Actual credentials/secrets should never be sent
        # to either a cloud or local LLM.
        if has_secret:
            return {
                "decision": "BLOCK",
                "reason": (
                    "Secret or credential detected; "
                    "request blocked."
                ),
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # --------------------------------------------------
        # 2. PII
        # --------------------------------------------------
        # Personally identifiable information remains local.
        if has_pii:
            return {
                "decision": "LOCAL",
                "reason": (
                    "Personally identifiable information "
                    "detected; keeping request local."
                ),
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # --------------------------------------------------
        # 3. CONFIDENTIAL
        # --------------------------------------------------
        if sensitivity_label == "Confidential":
            return {
                "decision": "LOCAL",
                "reason": (
                    "Confidential information must remain "
                    "on the local system."
                ),
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # --------------------------------------------------
        # 4. INTERNAL
        # --------------------------------------------------
        if sensitivity_label == "Internal":
            return {
                "decision": "LOCAL",
                "reason": (
                    "Internal information must remain "
                    "on the local system."
                ),
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # --------------------------------------------------
        # 5. PUBLIC
        # --------------------------------------------------
        # Public information can use the cloud when no
        # deterministic sensitive signal was detected.
        if sensitivity_label == "Public":
            return {
                "decision": "CLOUD",
                "reason": (
                    "Input is public and no sensitive "
                    "security signals were detected."
                ),
                "sensitivity": sensitivity_label,
                "confidence": confidence,
            }

        # --------------------------------------------------
        # 6. UNKNOWN / UNRECOGNIZED
        # --------------------------------------------------
        # Fail-safe behavior.
        return {
            "decision": "LOCAL",
            "reason": (
                "Sensitivity classification is unknown; "
                "using local processing as a fail-safe."
            ),
            "sensitivity": sensitivity_label,
            "confidence": confidence,
        }


if __name__ == "__main__":

    policy = PolicyEngine()

    test_cases = [
        {
            "name": "Public question",
            "label": "Public",
            "confidence": 0.31,
            "pii": False,
            "secret": False,
            "code": False,
        },
        {
            "name": "Internal information",
            "label": "Internal",
            "confidence": 0.40,
            "pii": False,
            "secret": False,
            "code": False,
        },
        {
            "name": "Confidential information",
            "label": "Confidential",
            "confidence": 0.38,
            "pii": False,
            "secret": False,
            "code": False,
        },
        {
            "name": "PII information",
            "label": "Public",
            "confidence": 0.90,
            "pii": True,
            "secret": False,
            "code": False,
        },
        {
            "name": "Secret credential",
            "label": "Secret",
            "confidence": 0.30,
            "pii": False,
            "secret": True,
            "code": False,
        },
        {
            "name": "Public code",
            "label": "Public",
            "confidence": 0.35,
            "pii": False,
            "secret": False,
            "code": True,
        },
        {
            "name": "Unknown classification",
            "label": "Unknown",
            "confidence": 0.20,
            "pii": False,
            "secret": False,
            "code": False,
        },
    ]

    print("Policy Engine Tests")
    print("=" * 60)

    for case in test_cases:

        result = policy.decide(
            sensitivity_label=case["label"],
            confidence=case["confidence"],
            has_pii=case["pii"],
            has_secret=case["secret"],
            has_code=case["code"],
        )

        print(f"\nTest: {case['name']}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")