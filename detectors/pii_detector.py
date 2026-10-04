import re


EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

PHONE_PATTERN = (
    r"(?<!\d)"
    r"(?:\+\d{1,3}[\s.-]?)?"
    r"\d{5}[\s.-]?\d{5}"
    r"(?!\d)"
)

IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"


def find_valid_ips(text: str) -> list[str]:
    """
    Find IPv4 addresses and keep only valid addresses
    where every octet is between 0 and 255.
    """

    candidates = re.findall(IP_PATTERN, text)

    valid_ips = []

    for ip in candidates:
        octets = ip.split(".")

        if all(0 <= int(octet) <= 255 for octet in octets):
            valid_ips.append(ip)

    return valid_ips


def detect_pii(text: str) -> dict:

    findings = {}

    emails = re.findall(
        EMAIL_PATTERN,
        text,
        flags=re.IGNORECASE
    )

    if emails:
        findings["email"] = {
            "count": len(emails),
            "matches": emails,
        }

    phones = re.findall(
        PHONE_PATTERN,
        text
    )

    if phones:
        findings["phone"] = {
            "count": len(phones),
            "matches": phones,
        }

    valid_ips = find_valid_ips(text)

    if valid_ips:
        findings["ip_address"] = {
            "count": len(valid_ips),
            "matches": valid_ips,
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

    test_cases = [
        "Contact me at student@example.com",
        "My phone number is 9876543210",
        "Server IP is 192.168.1.10",
        "Invalid IP is 123.555.44.2",
        "Email me at test@example.com from 10.0.0.5",
    ]

    print("PII Detector Tests")
    print("=" * 60)

    for text in test_cases:

        result = detect_pii(text)

        print(f"\nInput: {text}")
        print(f"PII detected: {result['has_pii']}")
        print(f"Total count: {result['total_count']}")
        print(f"Types: {list(result['types'].keys())}")