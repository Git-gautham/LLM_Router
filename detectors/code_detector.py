import re


CODE_PATTERNS = {
    "python": [
        r"\bdef\s+\w+\s*\(",
        r"\bimport\s+\w+",
        r"\bfrom\s+\w+\s+import\s+",
        r"\bprint\s*\(",
    ],

    "javascript": [
        r"\b(?:const|let|var)\s+\w+\s*=",
        r"\bfunction\s+\w+\s*\(",
        r"=>",
        r"\bconsole\.log\s*\(",
    ],

    "sql": [
        r"\bSELECT\b.+\bFROM\b",
        r"\bINSERT\s+INTO\b",
        r"\bUPDATE\b.+\bSET\b",
        r"\bDELETE\s+FROM\b",
    ],

    "shell": [
        r"^\s*#!/bin/(?:bash|sh)",
        r"\b(?:sudo|chmod|apt|pip|npm)\s+",
    ],
}


def detect_code(text: str) -> dict:
    """
    Detect whether the input contains common programming
    or command-line code patterns.
    """

    detected_languages = {}

    for language, patterns in CODE_PATTERNS.items():
        matches = []

        for pattern in patterns:
            found = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )

            matches.extend(found)

        if matches:
            detected_languages[language] = {
                "match_count": len(matches),
            }

    total_matches = sum(
        item["match_count"]
        for item in detected_languages.values()
    )

    return {
        "has_code": total_matches > 0,
        "code_match_count": total_matches,
        "languages": list(detected_languages.keys()),
        "details": detected_languages,
    }


if __name__ == "__main__":
    test_text = """
    def calculate_salary(employee):
        return employee.salary * 1.10

    API_KEY=FAKE_API_KEY_123456789
    """

    result = detect_code(test_text)

    print("Code Detection Result:")
    print(result)