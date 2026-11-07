from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    status: str
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetailResponse(KnowledgeDocumentResponse):
    extracted_text: str | None = None