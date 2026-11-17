
from typing import TypedDict

from sqlalchemy.orm import Session


class AgentState(TypedDict):
    user_message: str
    intent: str
    response: str
    sources: list[dict]


class AgentContext(TypedDict):
    db: Session
    vector_db: Session
