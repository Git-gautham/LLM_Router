from docx import Document
from reportlab.pdfgen import canvas


TEST_TEXT = """Employee review document.
Contact: john.doe@example.com
API_KEY=FAKE_API_KEY_123456789
"""


def create_txt():
    with open("test.txt", "w", encoding="utf-8") as file:
        file.write(TEST_TEXT)


def create_pdf():
    pdf = canvas.Canvas("test.pdf")

    y_position = 800

    for line in TEST_TEXT.splitlines():
        pdf.drawString(50, y_position, line)
        y_position -= 20

    pdf.save()


def create_docx():
    document = Document()

    for line in TEST_TEXT.splitlines():
        document.add_paragraph(line)

    document.save("test.docx")


if __name__ == "__main__":
    create_txt()
    create_pdf()
    create_docx()

    print("Test documents created successfully: test.txt, test.pdf, test.docx")