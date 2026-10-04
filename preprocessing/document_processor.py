from pathlib import Path

import pymupdf
from docx import Document
from openpyxl import load_workbook


def extract_from_txt(file_path: str) -> str:
    path = Path(file_path)

    return path.read_text(
        encoding="utf-8"
    )


def extract_from_pdf(file_path: str) -> str:
    document = pymupdf.open(file_path)

    pages = []

    for page in document:
        pages.append(page.get_text())

    document.close()

    return "\n".join(pages).strip()


def extract_from_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()


def extract_from_xlsx(file_path: str) -> str:
    """
    Extract readable text from an Excel workbook.

    Each worksheet is processed row by row.
    Cell values are converted to text and separated by tabs.
    """

    workbook = load_workbook(
        filename=file_path,
        read_only=True,
        data_only=True,
    )

    sheets = []

    for worksheet in workbook.worksheets:

        sheets.append(
            f"[Worksheet: {worksheet.title}]"
        )

        for row in worksheet.iter_rows(
            values_only=True
        ):

            values = []

            for cell in row:

                if cell is not None:
                    values.append(str(cell))

            if values:
                sheets.append(
                    "\t".join(values)
                )

    workbook.close()

    return "\n".join(sheets).strip()


def extract_text(file_path: str) -> dict:
    """
    Extract text from supported document types.

    Supported:
        .txt
        .pdf
        .docx
        .xlsx
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    if extension == ".txt":

        text = extract_from_txt(file_path)

    elif extension == ".pdf":

        text = extract_from_pdf(file_path)

    elif extension == ".docx":

        text = extract_from_docx(file_path)

    elif extension == ".xlsx":

        text = extract_from_xlsx(file_path)

    else:

        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported types: .txt, .pdf, .docx, .xlsx"
        )

    return {
        "file_name": path.name,
        "file_type": extension,
        "text": text,
        "character_count": len(text),
    }


if __name__ == "__main__":

    print("Document Processor")
    print("=" * 60)

    print(
        "Supported file types:"
    )

    print("  - TXT")
    print("  - PDF")
    print("  - DOCX")
    print("  - XLSX")