
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_role
from backend.app.db.dependencies import get_db
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.models.user import User
from backend.app.schemas.knowledge_document import (
    KnowledgeDocumentResponse,
    KnowledgeDocumentDetailResponse,
)
from backend.app.services.document_service import (
    process_document,
    delete_stored_file,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("it_support")),
    db: Session = Depends(get_db),
):
    file_path = None

    try:
        file_bytes = await file.read(10 * 1024 * 1024 + 1)

        document_data = process_document(
            filename=file.filename or "",
            file_bytes=file_bytes,
        )

        file_path = document_data["file_path"]

        document = KnowledgeDocument(
            file_name=document_data["file_name"],
            file_type=document_data["file_type"],
            file_path=document_data["file_path"],
            file_size=document_data["file_size"],
            extracted_text=document_data["extracted_text"],
            status="processed",
            uploaded_by=current_user.id,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception:
        db.rollback()

        if file_path:
            delete_stored_file(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and process document.",
        )


@router.get(
    "/documents",
    response_model=list[KnowledgeDocumentResponse],
)
def get_knowledge_documents(
    current_user: User = Depends(require_role("it_support")),
    db: Session = Depends(get_db),
):
    documents = (
        db.query(KnowledgeDocument)
        .order_by(KnowledgeDocument.created_at.desc())
        .all()
    )

    return documents


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
)
def get_knowledge_document(
    document_id: int,
    current_user: User = Depends(require_role("it_support")),
    db: Session = Depends(get_db),
):
    document = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found.",
        )

    return document
