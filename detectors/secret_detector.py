import re


PATTERNS = {

    # Generic API key assignment.
    # Requires at least 8 characters after the key name.
    "api_key": (
        r"\b(?:api[_-]?key|apikey)"
        r"\s*[:=]\s*"
        r"['\"]?"
        r"[A-Za-z0-9_\-]{8,}"
        r"['\"]?"
    ),

    # Access tokens.
    "access_token": (
        r"\b(?:access[_-]?token)"
        r"\s*[:=]\s*"
        r"['\"]?"
        r"[A-Za-z0-9_\-]{8,}"
        r"['\"]?"
    ),

    # Password assignments.
    "password": (
        r"\b(?:password|passwd|pwd)"
        r"\s*[:=]\s*"
        r"\S+"
    ),

    # Private keys.
    "private_key": (
        r"-----BEGIN "
        r"(?:RSA |EC |OPENSSH )?"
        r"PRIVATE KEY-----"
    ),

    # Database credentials.
    "database_credential": (
        r"\b(?:mysql|postgresql|postgres|mongodb)://"
        r"[^:\s]+:"
        r"[^@\s]+@"
    ),
}


def detect_secrets(text: str) -> dict:

    findings = {}

    for secret_type, pattern in PATTERNS.items():

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if matches:

            findings[secret_type] = {
                "count": len(matches),
                "matches": matches,
            }

    total_count = sum(
        item["count"]
        for item in findings.values()
    )

    return {
        "has_secret": total_count > 0,
        "total_count": total_count,
        "types": findings,
    }


if __name__ == "__main__":

    test_cases = [
        "API_KEY:19hfknsbkd",
        "api_key=FAKE_API_KEY_123456789",
        "access_token: abcdefgh123456",
        "password: MyRealPassword123",
        "-----BEGIN PRIVATE KEY-----",
        "postgres://admin:secret123@localhost:5432/database",
        "What is a good password?",
    ]

    print("Secret Detector Tests")
    print("=" * 60)

    for text in test_cases:

        result = detect_secrets(text)

        print(f"\nInput: {text}")
        print(f"Secret detected: {result['has_secret']}")
        print(f"Total count: {result['total_count']}")
        print(f"Types: {list(result['types'].keys())}")