class RiskEngine:
    """
    Calculates a normalized privacy/security risk score.

    The ML classifier provides the predicted sensitivity.
    Deterministic detectors provide concrete security signals.
    """

    SENSITIVITY_SCORES = {
        "Public": 0,
        "Internal": 20,
        "Confidential": 40,
        "Secret": 60,
    }

    def calculate_risk(
        self,
        sensitivity_label: str,
        confidence: float,
        has_pii: bool = False,
        pii_count: int = 0,
        has_secret: bool = False,
        secret_count: int = 0,
        has_code: bool = False,
        code_match_count: int = 0,
    ) -> dict:

        score = self.SENSITIVITY_SCORES.get(
            sensitivity_label,
            50,
        )

        reasons = []

        # Sensitivity contribution
        if sensitivity_label in self.SENSITIVITY_SCORES:
            if sensitivity_label != "Public":
                reasons.append(
                    f"{sensitivity_label} sensitivity classification"
                )

        # PII contribution
        if has_pii:
            score += min(pii_count * 10, 20)
            reasons.append(
                f"PII detected ({pii_count} occurrence(s))"
            )

        # Secret contribution
        if has_secret:
            score += 40
            reasons.append(
                f"Secret/credential detected ({secret_count} occurrence(s))"
            )

        # Code contribution
        if has_code:
            score += min(code_match_count * 2, 10)
            reasons.append(
                f"Code detected ({code_match_count} match(es))"
            )

        # Low ML confidence increases uncertainty
        if confidence < 0.60:
            score += 10
            reasons.append(
                "Low ML classification confidence"
            )

        # Normalize to 0-100
        score = min(score, 100)

        # Risk category
        if score >= 70:
            risk_level = "HIGH"
        elif score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
        }


if __name__ == "__main__":

    engine = RiskEngine()

    test_cases = [
        {
            "name": "Public question",
            "sensitivity_label": "Public",
            "confidence": 0.90,
            "has_pii": False,
            "pii_count": 0,
            "has_secret": False,
            "secret_count": 0,
            "has_code": False,
            "code_match_count": 0,
        },
        {
            "name": "Internal information",
            "sensitivity_label": "Internal",
            "confidence": 0.90,
            "has_pii": False,
            "pii_count": 0,
            "has_secret": False,
            "secret_count": 0,
            "has_code": False,
            "code_match_count": 0,
        },
        {
            "name": "Employee information",
            "sensitivity_label": "Confidential",
            "confidence": 0.85,
            "has_pii": True,
            "pii_count": 2,
            "has_secret": False,
            "secret_count": 0,
            "has_code": False,
            "code_match_count": 0,
        },
        {
            "name": "API credential",
            "sensitivity_label": "Secret",
            "confidence": 0.30,
            "has_pii": False,
            "pii_count": 0,
            "has_secret": True,
            "secret_count": 1,
            "has_code": False,
            "code_match_count": 0,
        },
    ]

    print("Risk Engine Tests")
    print("=" * 60)

    for case in test_cases:
        result = engine.calculate_risk(
            sensitivity_label=case["sensitivity_label"],
            confidence=case["confidence"],
            has_pii=case["has_pii"],
            pii_count=case["pii_count"],
            has_secret=case["has_secret"],
            secret_count=case["secret_count"],
            has_code=case["has_code"],
            code_match_count=case["code_match_count"],
        )

        print(f"\nTest: {case['name']}")
        print(f"Risk Score: {result['risk_score']}/100")
        print(f"Risk Level: {result['risk_level']}")
        print("Reasons:")

        for reason in result["reasons"]:
            print(f"  - {reason}")