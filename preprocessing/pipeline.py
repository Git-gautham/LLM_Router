from preprocessing.document_processor import extract_text
from detectors.pii_detector import detect_pii
from detectors.secret_detector import detect_secrets


def analyze_document(file_path: str) -> dict:
    """
    Extract text from a document and analyze it
    for PII and secrets.
    """

    document = extract_text(file_path)

    text = document["text"]

    pii_result = detect_pii(text)
    secret_result = detect_secrets(text)

    return {
        "file_name": document["file_name"],
        "file_type": document["file_type"],
        "character_count": document["character_count"],

        "text": text,

        "has_pii": pii_result["has_pii"],
        "pii_count": pii_result["total_count"],
        "pii_types": list(pii_result["types"].keys()),

        "has_secret": secret_result["has_secret"],
        "secret_count": secret_result["total_count"],
        "secret_types": list(secret_result["types"].keys()),
    }


if __name__ == "__main__":
    result = analyze_document("test.pdf")

    print("\nDocument Security Analysis")
    print("=" * 50)

    print(f"File: {result['file_name']}")
    print(f"Type: {result['file_type']}")
    print(f"Characters: {result['character_count']}")

    print(f"\nPII detected: {result['has_pii']}")
    print(f"PII count: {result['pii_count']}")
    print(f"PII types: {result['pii_types']}")

    print(f"\nSecret detected: {result['has_secret']}")
    print(f"Secret count: {result['secret_count']}")
    print(f"Secret types: {result['secret_types']}")