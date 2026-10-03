from detectors.pii_detector import detect_pii
from detectors.secret_detector import detect_secrets
from detectors.code_detector import detect_code
from preprocessing.metadata_extractor import extract_metadata


def generate_features(
    text: str,
    file_path: str | None = None,
    input_type: str = "text",
) -> dict:
    """
    Generate a unified feature representation for
    sensitivity classification and policy decisions.
    """

    # Security detectors
    pii_result = detect_pii(text)
    secret_result = detect_secrets(text)
    code_result = detect_code(text)

    # Metadata
    metadata = extract_metadata(
        text=text,
        file_path=file_path,
        input_type=input_type,
    )

    # Unified feature representation
    features = {
        "text": text,

        # PII features
        "has_pii": pii_result["has_pii"],
        "pii_count": pii_result["total_count"],
        "pii_types": list(pii_result["types"].keys()),

        # Secret features
        "has_secret": secret_result["has_secret"],
        "secret_count": secret_result["total_count"],
        "secret_types": list(secret_result["types"].keys()),

        # Code features
        "has_code": code_result["has_code"],
        "code_match_count": code_result["code_match_count"],
        "code_languages": code_result["languages"],

        # Metadata
        "input_type": metadata["input_type"],
        "character_count": metadata["character_count"],
        "file_name": metadata["file_name"],
        "file_type": metadata["file_type"],
    }

    return features


if __name__ == "__main__":

    test_text = """
    def get_employee_data():
        return "employee information"

    Contact: john.doe@example.com

    API_KEY=FAKE_API_KEY_123456789
    """

    features = generate_features(
        text=test_text,
        file_path="employee_record.pdf",
        input_type="document",
    )

    print("Unified Feature Representation")
    print("=" * 50)

    for key, value in features.items():
        print(f"{key}: {value}")