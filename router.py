from ml.predict import SensitivityClassifier
from preprocessing.feature_generator import generate_features
from policy.policy_engine import PolicyEngine
from app.local_llm import ask_local_llm


class AdaptiveRouter:
    def __init__(self):
        self.classifier = SensitivityClassifier()
        self.policy = PolicyEngine()

    def route(self, text: str) -> dict:
        # Step 1: Extract security features
        features = generate_features(
            text=text,
            input_type="text",
        )

        # Step 2: ML sensitivity classification
        prediction = self.classifier.predict(text)

        # Step 3: Policy decision
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
            "decision": decision["decision"],
            "reason": decision["reason"],
            "features": features,
        }

        # Step 4: Execute routing decision
        if decision["decision"] == "LOCAL":
            result["response"] = ask_local_llm(text)

        elif decision["decision"] == "CLOUD":
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


if __name__ == "__main__":
    router = AdaptiveRouter()

    test_inputs = [
        "What is machine learning?",
        "Summarize our internal software development process.",
        "Review this employee salary document.",
        "API_KEY=FAKE_API_KEY_123456789",
    ]

    print("\nAdaptive Hybrid LLM Router")
    print("=" * 60)

    for text in test_inputs:
        result = router.route(text)

        print("\nInput:")
        print(result["input"])

        print(f"\nSensitivity: {result['sensitivity']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")

        print("\nResponse:")
        print(result["response"])

        print("-" * 60)