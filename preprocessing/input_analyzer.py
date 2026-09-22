from detectors.pii_detector import detect_pii
from detectors.secret_detector import detect_secrets


def analyze_input(text: str) -> dict:
    pii_result = detect_pii(text)
    secret_result = detect_secrets(text)

    return {
        "text": text,

        "has_pii": pii_result["has_pii"],
        "pii_count": pii_result["total_count"],
        "pii_types": list(pii_result["types"].keys()),

        "has_secret": secret_result["has_secret"],
        "secret_count": secret_result["total_count"],
        "secret_types": list(secret_result["types"].keys()),
    }


if __name__ == "__main__":
    test_text = """
    Please review this employee record.
    Contact the employee at john.doe@example.com.
    The temporary API key is API_KEY=FAKE_API_KEY_123456789.
    """

    result = analyze_input(test_text)

    print("Input Analysis Result:")
    print(result)