from pydantic import BaseModel


class ChatQueryRequest(BaseModel):
    """Payload for submitting a chat prompt (Placeholder interface without AI logic)."""

    query: str


class ChatQueryResponse(BaseModel):
    """Response payload for chat queries (Placeholder interface without AI logic)."""

    query: str
    response: str
    message: str = "Placeholder response - AI functionality to be implemented."
