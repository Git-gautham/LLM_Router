from preprocessing.document_processor import extract_text


TEST_FILES = [
    "test.txt",
    "test.pdf",
    "test.docx",
]


def test_file(file_path: str):
    print("\n" + "=" * 50)
    print(f"Testing: {file_path}")
    print("=" * 50)

    try:
        result = extract_text(file_path)

        print(f"File name: {result['file_name']}")
        print(f"File type: {result['file_type']}")
        print(f"Characters: {result['character_count']}")
        print("\nExtracted text:")
        print(result["text"])

    except Exception as error:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    for file_path in TEST_FILES:
        test_file(file_path)