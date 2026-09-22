import re


PATTERNS = {
    "api_key": r"\b(?:api[_-]?key|apikey)\s*[:=]\s*[A-Za-z0-9_\-]{12,}\b",

    "access_token": r"\b(?:access[_-]?token|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}\b",

    "password": r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+\b",

    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",

    "database_credential": (
        r"\b(?:mysql|postgresql|postgres|mongodb)://"
        r"[^:\s]+:[^@\s]+@"
    ),
}


def detect_secrets(text: str) -> dict:
    findings = {}

    for secret_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

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
    test_text = """
    API_KEY=FAKE_API_KEY_123456789
    password=FakePassword123
    access_token=FAKE_TOKEN_987654321
    """

    result = detect_secrets(test_text)

    print("Secret Detection Result:")
    print(result)