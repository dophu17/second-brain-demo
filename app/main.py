from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import webhook, demo
from app.services.graph_engine import graph_engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API Server cho dự án Second Brain AI (人を天才にするAIプロダクト)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(demo.router)

@app.on_event("startup")
def on_startup():
    # Khởi tạo Graph khi server boot lên
    graph_engine.build_graph()

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Phục vụ Giao diện Web Chatbox LINE-style tại trang chủ http://localhost:8008/."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Second Brain AI Web Chatbox</h1><p>Index template not found.</p>")

@app.get("/api/info")
def read_info():
    """Trả về JSON tổng quan hệ thống & thống kê Đồ thị Tri thức Knowledge Graph."""
    graph_info = graph_engine.get_graph_summary()
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "vault_path": str(settings.VAULT_PATH),
        "knowledge_graph": graph_info,
        "endpoints": {
            "web_chat": "/",
            "webhook": "/api/webhook",
            "demo_chat": "POST /api/demo/chat",
            "demo_notes": "GET /api/demo/notes",
            "demo_graph": "GET /api/demo/graph",
            "docs": "/docs"
        }
    }
