from pathlib import Path


def extract_metadata(
    text: str,
    file_path: str | None = None,
    input_type: str = "text",
) -> dict:
    """
    Extract basic metadata from the input.

    input_type:
        - text
        - document
        - code
    """

    metadata = {
        "input_type": input_type,
        "character_count": len(text),
    }

    if file_path:
        path = Path(file_path)

        metadata["file_name"] = path.name
        metadata["file_type"] = path.suffix.lower()

    else:
        metadata["file_name"] = None
        metadata["file_type"] = None

    return metadata


if __name__ == "__main__":
    test_text = """
    Employee review document.
    Contact: john.doe@example.com
    """

    metadata = extract_metadata(
        text=test_text,
        file_path="employee_record.pdf",
        input_type="document",
    )

    print("Metadata")
    print("=" * 50)

    for key, value in metadata.items():
        print(f"{key}: {value}")