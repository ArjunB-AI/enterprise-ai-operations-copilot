from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader


# Store uploaded documents in the project root.
UPLOAD_DIR = (
    Path(__file__).resolve().parents[3]
    / "uploads"
    / "knowledge_documents"
)

# Maximum allowed document size: 10 MB.
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_text(file_bytes: bytes, extension: str) -> str:
    """Extract readable text from a supported document."""

    if extension == ".pdf":
        pdf = PdfReader(BytesIO(file_bytes))

        text = "\n".join(
            page.extract_text() or ""
            for page in pdf.pages
        )

    elif extension == ".docx":
        document = Document(BytesIO(file_bytes))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
        ]

        table_text = [
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        ]

        text = "\n".join(paragraphs + table_text)

    elif extension == ".txt":
        text = file_bytes.decode("utf-8-sig")

    else:
        raise ValueError("Unsupported document format.")

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found in the document. "
            "Scanned PDFs are not supported yet."
        )

    return text


def process_document(filename: str, file_bytes: bytes) -> dict:
    """Validate, extract text, and save an uploaded document."""

    if not filename:
        raise ValueError("A filename is required.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file format. Upload PDF, DOCX, or TXT files."
        )

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 10 MB limit.")

    # Extract text before saving the file.
    extracted_text = extract_text(file_bytes, extension)

    # Generate a safe, unique filename.
    stored_filename = f"{uuid4().hex}{extension}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / stored_filename
    file_path.write_bytes(file_bytes)

    return {
        "file_name": Path(filename).name,
        "file_type": extension.lstrip("."),
        "file_path": str(file_path),
        "file_size": len(file_bytes),
        "extracted_text": extracted_text,
    }


def delete_stored_file(file_path: str) -> None:
    """Delete a stored document if it belongs to our upload directory."""

    upload_directory = UPLOAD_DIR.resolve()
    target_path = Path(file_path).resolve()

    if target_path.is_relative_to(upload_directory):
        target_path.unlink(missing_ok=True)