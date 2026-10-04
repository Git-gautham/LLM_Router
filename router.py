from ml.predict import SensitivityClassifier
from preprocessing.feature_generator import generate_features
from policy.policy_engine import PolicyEngine
from risk.risk_engine import RiskEngine
from app.local_llm import ask_local_llm


class AdaptiveRouter:
    def __init__(self):
        self.classifier = SensitivityClassifier()
        self.risk_engine = RiskEngine()
        self.policy = PolicyEngine()

    def route(self, text: str) -> dict:

        # 1. Extract security features
        features = generate_features(
            text=text,
            input_type="text",
        )

        # 2. ML sensitivity classification
        prediction = self.classifier.predict(text)

        # 3. Calculate risk
        risk = self.risk_engine.calculate_risk(
            sensitivity_label=prediction["label"],
            confidence=prediction["confidence"],
            has_pii=features["has_pii"],
            pii_count=features["pii_count"],
            has_secret=features["has_secret"],
            secret_count=features["secret_count"],
            has_code=features["has_code"],
            code_match_count=features["code_match_count"],
        )

        # 4. Policy decision
        decision = self.policy.decide(
            sensitivity_label=prediction["label"],
            confidence=prediction["confidence"],
            has_pii=features["has_pii"],
            has_secret=features["has_secret"],
            has_code=features["has_code"],
        )

        result = {
            "input": text,
            "sensitivity": prediction["label"],
            "confidence": prediction["confidence"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "risk_reasons": risk["reasons"],
            "decision": decision["decision"],
            "reason": decision["reason"],
        }

        # 5. Execute routing decision
        if decision["decision"] == "LOCAL":

            result["response"] = ask_local_llm(text)

        elif decision["decision"] == "CLOUD":

            # Cloud integration will be added later.
            result["response"] = (
                "[CLOUD LLM SIMULATION] "
                "This request would be sent to the configured cloud LLM."
            )

        elif decision["decision"] == "BLOCK":

            result["response"] = (
                "Request blocked because sensitive information "
                "was detected."
            )

        return result


def main():

    print("\nAdaptive Hybrid LLM Router")
    print("=" * 60)
    print("Type your request below.")
    print("Type 'exit' to quit.")
    print("=" * 60)

    router = AdaptiveRouter()

    while True:

        print("\n")
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("\nExiting router...")
            break

        if not user_input:
            print("Please enter a request.")
            continue

        result = router.route(user_input)

        print("\n" + "-" * 60)
        print("ROUTING ANALYSIS")
        print("-" * 60)

        print(f"Sensitivity : {result['sensitivity']}")
        print(f"Confidence  : {result['confidence']}")
        print(f"Risk Score  : {result['risk_score']}/100")
        print(f"Risk Level  : {result['risk_level']}")
        print(f"Decision    : {result['decision']}")
        print(f"Reason      : {result['reason']}")

        if result["risk_reasons"]:
            print("\nRisk Factors:")
            for reason in result["risk_reasons"]:
                print(f"  - {reason}")

        print("\n" + "-" * 60)
        print("RESPONSE")
        print("-" * 60)
        print(result["response"])
        print("-" * 60)


if __name__ == "__main__":
    main()