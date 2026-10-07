from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NoteMetadata(BaseModel):
    title: str
    tags: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = "General"

class NoteItem(BaseModel):
    filename: str
    relative_path: str
    title: str
    content: str
    metadata: NoteMetadata
    wiki_links: List[str] = Field(default_factory=list)

class CreateNoteRequest(BaseModel):
    title: str
    folder: Optional[str] = "00_Nhat_Ky_Trang_Trai"
    tags: List[str] = Field(default_factory=list)
    content: str
    author: Optional[str] = "Farm Manager"

class UpdateNoteRequest(BaseModel):
    relative_path: str
    content_append: Optional[str] = None
    tags_add: Optional[List[str]] = None

class ChatRequest(BaseModel):
    message: str
    persona: Optional[str] = "SecondBrain"  # Options: SecondBrain, CEO, CFO, CMO

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ChatResponse(BaseModel):
    reply: str
    persona: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)
    graph_context: List[str] = Field(default_factory=list)
