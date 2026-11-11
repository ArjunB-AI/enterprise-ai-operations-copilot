
import re

from transformers import AutoTokenizer
from sqlalchemy.orm import Session

from backend.app.models.document_chunk import DocumentChunk


MODEL_NAME = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 450
CHUNK_OVERLAP = 75

tokenizer = None


def get_tokenizer():
    global tokenizer

    if tokenizer is None:
        print(f"Loading tokenizer: {MODEL_NAME}")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        print("Tokenizer loaded successfully.")

    return tokenizer


def is_section_heading(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    # Ignore document identifiers such as ATAI-IT-POL-001.
    if re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", line):
        return False

    # Markdown headings.
    if line.startswith("#"):
        return len(line) <= 150

    # Numbered headings such as 1. Purpose or 2.1 Scope.
    if re.match(r"^\d+\.\s+\S", line) or re.match(
        r"^\d+(?:\.\d+)+\s+\S", line
    ):
        return len(line) <= 150

    # Genuine uppercase headings, excluding codes and priority labels.
    if (
        len(line) <= 100
        and len(line.split()) >= 2
        and line.isupper()
        and all(word.isalpha() for word in line.split())
    ):
        return True

    return False


def split_into_sections(text: str) -> list[dict]:
    sections = []
    current_title = None
    current_lines = []

    for line in text.splitlines():
        stripped_line = line.strip()

        if is_section_heading(stripped_line):
            if current_lines:
                sections.append({
                    "section_title": current_title,
                    "content": "\n".join(current_lines).strip(),
                })

            current_title = stripped_line.lstrip("#").strip()
            current_lines = [stripped_line]

        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "section_title": current_title,
            "content": "\n".join(current_lines).strip(),
        })

    return [
        section for section in sections
        if section["content"]
    ]



def merge_short_sections(sections, tokenizer, chunk_size=CHUNK_SIZE):
    merged_sections = []

    for section in sections:
        current_content = section["content"]

        current_token_count = len(
            tokenizer.encode(
                current_content,
                add_special_tokens=False,
            )
        )

        if not merged_sections:
            merged_sections.append(section)
            continue

        previous_section = merged_sections[-1]

        combined_content = (
            previous_section["content"] + "\n\n" + current_content
        )

        combined_token_count = len(
            tokenizer.encode(
                combined_content,
                add_special_tokens=False,
            )
        )

        if (
            current_token_count < chunk_size
            and combined_token_count <= chunk_size
        ):
            previous_section["content"] = combined_content
        else:
            merged_sections.append(section)

    return merged_sections

def chunk_section(
    content,
    tokenizer,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
):
    tokens = tokenizer.encode(
        content,
        add_special_tokens=False,
    )

    chunks = []
    start = 0
    chunk_index = 0

    step = chunk_size - chunk_overlap

    while start < len(tokens):
        end = start + chunk_size

        chunk_tokens = tokens[start:end]

        chunk_text = tokenizer.decode(
            chunk_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

        actual_token_count = len(
            tokenizer.encode(
                chunk_text,
                add_special_tokens=False,
            )
        )

        if chunk_text.strip():
            chunks.append({
                "content": chunk_text,
                "token_count": actual_token_count,
                "chunk_index": chunk_index,
            })

            chunk_index += 1

        start += step

    return chunks




def create_document_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
):
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative and smaller than chunk size."
        )

    tokenizer = get_tokenizer()

    sections = split_into_sections(text)

    sections = merge_short_sections(
        sections,
        tokenizer,
        chunk_size,
    )

    all_chunks = []
    global_chunk_index = 0

    for section in sections:
        section_chunks = chunk_section(
            content=section["content"],
            tokenizer=tokenizer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk in section_chunks:
            all_chunks.append({
                "chunk_index": global_chunk_index,
                "content": chunk["content"],
                "token_count": chunk["token_count"],
                "section_title": section["section_title"],
            })

            global_chunk_index += 1

    return all_chunks


def store_document_chunks(
    db: Session,
    document_id: int,
    text: str,
) -> int:

    chunks = create_document_chunks(text)

    # Remove previously generated chunks if the document is reprocessed.
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete(synchronize_session=False)

    document_chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=chunk["chunk_index"],
            content=chunk["content"],
            token_count=chunk["token_count"],
            section_title=chunk["section_title"],
        )
        for chunk in chunks
    ]

    db.add_all(document_chunks)

    return len(document_chunks)
