from pathlib import Path

import pymupdf
from docx import Document


def extract_from_txt(file_path: str) -> str:
    """Extract text from a plain text file."""
    path = Path(file_path)

    return path.read_text(encoding="utf-8")


def extract_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    document = pymupdf.open(file_path)

    pages = []

    for page in document:
        text = page.get_text()
        pages.append(text)

    document.close()

    return "\n".join(pages).strip()


def extract_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()


def extract_text(file_path: str) -> dict:
    """
    Extract text from TXT, PDF, or DOCX.

    Returns a common structure that can be passed
    to the security analysis pipeline.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".txt":
        text = extract_from_txt(file_path)

    elif extension == ".pdf":
        text = extract_from_pdf(file_path)

    elif extension == ".docx":
        text = extract_from_docx(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported types: .txt, .pdf, .docx"
        )

    return {
        "file_name": path.name,
        "file_type": extension,
        "text": text,
        "character_count": len(text),
    }


if __name__ == "__main__":
    print("Document processor loaded successfully.")
    print("Supported formats: TXT, PDF, DOCX")