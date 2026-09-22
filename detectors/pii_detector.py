import re

PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    "phone": r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?\d{5}[\s.-]?\d{5}(?!\d)",

    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}


def detect_pii(text: str) -> dict:
    findings = {}

    for pii_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)

        if matches:
            findings[pii_type] = {
                "count": len(matches),
                "matches": matches,
            }

    total_count = sum(
        item["count"]
        for item in findings.values()
    )

    return {
        "has_pii": total_count > 0,
        "total_count": total_count,
        "types": findings,
    }


if __name__ == "__main__":
    test_text = """
    Contact John at john.doe@example.com
    or call +91 98765 43210.
    The server IP is 192.168.1.10.
    """

    result = detect_pii(test_text)

    print("PII Detection Result:")
    print(result)