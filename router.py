from ml.predict import SensitivityClassifier
from preprocessing.feature_generator import generate_features
from preprocessing.document_processor import extract_text
from policy.policy_engine import PolicyEngine
from risk.risk_engine import RiskEngine
from app.local_llm import ask_local_llm


class AdaptiveRouter:

    def __init__(self):
        self.classifier = SensitivityClassifier()
        self.risk_engine = RiskEngine()
        self.policy = PolicyEngine()

    def route(
        self,
        text: str,
        file_path: str | None = None,
    ) -> dict:

        # --------------------------------------------------
        # 1. PROCESS INPUT
        # --------------------------------------------------

        if file_path:

            document = extract_text(file_path)

            document_text = document["text"]

            # Analyze both the user's question and
            # the extracted document content.
            analysis_text = (
                f"User query:\n{text}\n\n"
                f"Document content:\n{document_text}"
            )

            features = generate_features(
                text=document_text,
                file_path=file_path,
                input_type="document",
            )

        else:

            analysis_text = text

            features = generate_features(
                text=text,
                input_type="text",
            )

        # --------------------------------------------------
        # 2. ML SENSITIVITY CLASSIFICATION
        # --------------------------------------------------

        prediction = self.classifier.predict(
            analysis_text
        )

        # --------------------------------------------------
        # 3. RISK CALCULATION
        # --------------------------------------------------

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

        # --------------------------------------------------
        # 4. POLICY DECISION
        # --------------------------------------------------

        decision = self.policy.decide(
            sensitivity_label=prediction["label"],
            confidence=prediction["confidence"],
            has_pii=features["has_pii"],
            has_secret=features["has_secret"],
            has_code=features["has_code"],
        )

        # --------------------------------------------------
        # 5. BUILD RESULT
        # --------------------------------------------------

        result = {
            "input": text,
            "file": file_path,
            "sensitivity": prediction["label"],
            "confidence": prediction["confidence"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "risk_reasons": risk["reasons"],
            "decision": decision["decision"],
            "reason": decision["reason"],
        }

        # --------------------------------------------------
        # 6. EXECUTE ROUTING DECISION
        # --------------------------------------------------

        if decision["decision"] == "LOCAL":

            # Local LLM receives the complete analysis context.
            local_prompt = analysis_text

            result["response"] = ask_local_llm(
                local_prompt
            )

        elif decision["decision"] == "CLOUD":

            # Cloud integration will be added later.
            result["response"] = (
                "[CLOUD LLM SIMULATION] "
                "This request would be sent to the "
                "configured cloud LLM."
            )

        elif decision["decision"] == "BLOCK":

            result["response"] = (
                "Request blocked because sensitive "
                "information was detected."
            )

        return result


def print_result(result: dict):

    print("\n" + "-" * 60)
    print("ROUTING ANALYSIS")
    print("-" * 60)

    print(f"Sensitivity : {result['sensitivity']}")
    print(f"Confidence  : {result['confidence']}")
    print(f"Risk Score  : {result['risk_score']}/100")
    print(f"Risk Level  : {result['risk_level']}")
    print(f"Decision    : {result['decision']}")
    print(f"Reason      : {result['reason']}")

    if result["file"]:
        print(f"File        : {result['file']}")

    if result["risk_reasons"]:

        print("\nRisk Factors:")

        for reason in result["risk_reasons"]:
            print(f"  - {reason}")

    print("\n" + "-" * 60)
    print("RESPONSE")
    print("-" * 60)

    print(result["response"])

    print("-" * 60)


def main():
    print("\nAdaptive Hybrid LLM Router")
    print("=" * 60)
    print("Enter your question and optionally provide a document.")
    print("Press Enter at the document prompt if there is no document.")
    print("Type 'exit' to quit.")
    print("=" * 60)

    router = AdaptiveRouter()

    while True:
        print("\n")

        user_input = input("Question: ").strip()

        if user_input.lower() == "exit":
            break

        if not user_input:
            print("Please enter a question.")
            continue

        file_path = input(
            "Document path (press Enter if no document): "
        ).strip()

        if file_path.lower() == "exit":
            break

        # --------------------------------------------------
        # Determine whether a valid document was provided
        # --------------------------------------------------
        if file_path:
            from pathlib import Path

            if Path(file_path).exists():
                print("\nDocument detected -> File + Question mode")
                try:
                    result = router.route(
                        text=user_input,
                        file_path=file_path,
                    )
                    print_result(result)
                except Exception as error:
                    print(f"\nError processing document: {error}")
            else:
                print("\nDocument not found -> Treating input as text")

                result = router.route(
                    text=user_input,
                    file_path=None,
                )
                print_result(result)

        else:
            print("\nNo document provided -> Text mode")

            result = router.route(
                text=user_input,
                file_path=None,
            )
            print_result(result)


if __name__ == "__main__":
    main()
