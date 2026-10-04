from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from docx import Document
from openpyxl import load_workbook


# ---------------------------------------------------------
# Tesseract configuration
# ---------------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ---------------------------------------------------------
# TXT
# ---------------------------------------------------------

def extract_from_txt(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------
# IMAGE OCR
# ---------------------------------------------------------

def extract_from_image(file_path: str) -> str:
    """
    Extract text from PNG/JPG/JPEG using Tesseract OCR.
    """

    image = Image.open(file_path)

    try:
        text = pytesseract.image_to_string(
            image,
            lang="eng",
        )
    finally:
        image.close()

    return text.strip()


# ---------------------------------------------------------
# PDF OCR helper
# ---------------------------------------------------------

def ocr_pdf_page(page) -> str:
    """
    Convert a PDF page into an image and run OCR.
    """

    matrix = pymupdf.Matrix(2, 2)

    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False,
    )

    image = Image.frombytes(
        "RGB",
        [pixmap.width, pixmap.height],
        pixmap.samples,
    )

    try:
        text = pytesseract.image_to_string(
            image,
            lang="eng",
        )
    finally:
        image.close()

    return text.strip()


# ---------------------------------------------------------
# PDF
# ---------------------------------------------------------

def extract_from_pdf(file_path: str) -> tuple[str, bool, list[int]]:
    """
    Extract text from PDF.

    If a page contains little/no selectable text,
    automatically use OCR.
    """

    document = pymupdf.open(file_path)

    pages = []
    ocr_pages = []

    try:
        for page_number, page in enumerate(
            document,
            start=1,
        ):

            # Try normal PDF text extraction first
            text = page.get_text("text").strip()

            # Fall back to OCR when there is
            # little or no selectable text
            if len(text) < 30:

                print(
                    f"  OCR processing page {page_number}..."
                )

                text = ocr_pdf_page(page)

                if text:
                    ocr_pages.append(page_number)

            if text:
                pages.append(text)

    finally:
        document.close()

    return (
        "\n\n".join(pages).strip(),
        len(ocr_pages) > 0,
        ocr_pages,
    )


# ---------------------------------------------------------
# DOCX
# ---------------------------------------------------------

def extract_from_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs).strip()


# ---------------------------------------------------------
# XLSX
# ---------------------------------------------------------

def extract_from_xlsx(file_path: str) -> str:
    workbook = load_workbook(
        filename=file_path,
        read_only=True,
        data_only=True,
    )

    sheets = []

    try:

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
                        values.append(
                            str(cell)
                        )

                if values:
                    sheets.append(
                        "\t".join(values)
                    )

    finally:
        workbook.close()

    return "\n".join(sheets).strip()


# ---------------------------------------------------------
# UNIFIED DOCUMENT EXTRACTION
# ---------------------------------------------------------

def extract_text(file_path: str) -> dict:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    ocr_used = False
    ocr_pages = []

    # -----------------------------------------------------
    # TXT
    # -----------------------------------------------------

    if extension == ".txt":

        text = extract_from_txt(
            file_path
        )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    elif extension == ".pdf":

        (
            text,
            ocr_used,
            ocr_pages,
        ) = extract_from_pdf(
            file_path
        )

    # -----------------------------------------------------
    # DOCX
    # -----------------------------------------------------

    elif extension == ".docx":

        text = extract_from_docx(
            file_path
        )

    # -----------------------------------------------------
    # XLSX
    # -----------------------------------------------------

    elif extension == ".xlsx":

        text = extract_from_xlsx(
            file_path
        )

    # -----------------------------------------------------
    # PNG / JPG / JPEG
    # -----------------------------------------------------

    elif extension in {
        ".png",
        ".jpg",
        ".jpeg",
    }:

        print("  OCR processing image...")

        text = extract_from_image(
            file_path
        )

        ocr_used = True

    # -----------------------------------------------------
    # Unsupported
    # -----------------------------------------------------

    else:

        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported types: "
            ".txt, .pdf, .docx, .xlsx, "
            ".png, .jpg, .jpeg"
        )

    return {
        "file_name": path.name,
        "file_type": extension,
        "text": text,
        "character_count": len(text),
        "ocr_used": ocr_used,
        "ocr_pages": ocr_pages,
    }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print("Usage:")
        print(
            "python -m preprocessing.document_processor "
            "<file_path>"
        )

        sys.exit(1)

    file_path = sys.argv[1]

    result = extract_text(
        file_path
    )

    print(
        "\nDocument Processing Result"
    )
    print("=" * 60)

    print(
        f"File       : {result['file_name']}"
    )

    print(
        f"Type       : {result['file_type']}"
    )

    print(
        f"Characters : {result['character_count']}"
    )

    print(
        f"OCR Used   : {result['ocr_used']}"
    )

    print(
        f"OCR Pages  : {result['ocr_pages']}"
    )

    print("\nExtracted Text")
    print("-" * 60)

    print(result["text"])

    print("-" * 60)