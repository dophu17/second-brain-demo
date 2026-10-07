from fastapi import APIRouter
from typing import List, Dict, Any
from app.models.schemas import ChatRequest, ChatResponse, NoteItem
from app.services.obsidian_parser import obsidian_parser
from app.services.graph_engine import graph_engine
from app.services.hermes_agent import hermes_agent_service

router = APIRouter(prefix="/api/demo", tags=["Demo REST API"])

@router.post("/chat", response_model=ChatResponse)
def demo_chat(req: ChatRequest):
    """Gửi câu hỏi / tin nhắn trực tiếp để test Hermes Agent & Tool Calling."""
    return hermes_agent_service.process_chat(req.message, req.persona)

@router.get("/notes", response_model=List[NoteItem])
def demo_list_notes():
    """Xem danh sách toàn bộ các ghi chú hiện có trong Obsidian Vault."""
    return obsidian_parser.read_all_notes()

@router.get("/graph")
def demo_graph_info() -> Dict[str, Any]:
    """Lấy thông số Đồ thị Tri thức (Nodes, Edges, Backlinks)."""
    return graph_engine.get_graph_summary()
