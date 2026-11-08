
import re

import tiktoken
from sqlalchemy.orm import Session

from backend.app.models.document_chunk import DocumentChunk


CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOKEN_ENCODING = "cl100k_base"


def get_encoding():
    return tiktoken.get_encoding(TOKEN_ENCODING)


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


def merge_short_sections(
    sections: list[dict],
    encoding,
    chunk_size: int = CHUNK_SIZE,
) -> list[dict]:
    """
    Merge adjacent short sections when their combined token count
    does not exceed the target chunk size.

    Preserve all section headings in the combined content.
    """

    merged_sections = []

    for section in sections:
        content = section["content"]
        token_count = len(encoding.encode(content))

        if (
            merged_sections
            and token_count < chunk_size
            and len(
                encoding.encode(
                    merged_sections[-1]["content"] + "\n" + content
                )
            ) <= chunk_size
        ):
            previous = merged_sections[-1]

            previous["content"] += "\n" + content

            # Keep the first section title as the primary title.
        else:
            merged_sections.append({
                "section_title": section["section_title"],
                "content": content,
            })

    return merged_sections


def chunk_section(
    content: str,
    encoding,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    tokens = encoding.encode(content)
    chunks = []

    if not tokens:
        return chunks

    step = chunk_size - chunk_overlap
    start = 0
    chunk_index = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]

        chunks.append({
            "content": encoding.decode(chunk_tokens),
            "token_count": len(chunk_tokens),
            "chunk_index": chunk_index,
        })

        if end == len(tokens):
            break

        start += step
        chunk_index += 1

    return chunks


def create_document_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:

    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative and smaller than chunk size."
        )

    encoding = get_encoding()

    sections = split_into_sections(text)

    sections = merge_short_sections(
        sections=sections,
        encoding=encoding,
        chunk_size=chunk_size,
    )

    document_chunks = []
    chunk_index = 0

    for section in sections:
        section_chunks = chunk_section(
            content=section["content"],
            encoding=encoding,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk in section_chunks:
            document_chunks.append({
                "chunk_index": chunk_index,
                "content": chunk["content"],
                "token_count": chunk["token_count"],
                "section_title": section["section_title"],
            })

            chunk_index += 1

    return document_chunks


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
