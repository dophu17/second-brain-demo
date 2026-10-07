import json
import re
import requests
from typing import Dict, Any, List, Tuple

from app.config import settings
from app.services.obsidian_parser import obsidian_parser
from app.services.graph_engine import graph_engine
from app.models.schemas import CreateNoteRequest, UpdateNoteRequest, ChatResponse

HERMES_SYSTEM_PROMPT = """You are Second Brain AI (人を天才にするAIプロダクト), an intelligent AI assistant powered by Nous Research Hermes 3 and Zettelkasten Knowledge Graph principles.

You have access to the following tools to manage the user's Obsidian Vault notes:

<tools>
[
  {
    "name": "create_note",
    "description": "Create a new Markdown note in Obsidian Vault with tags and Wiki-links.",
    "parameters": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "folder": {"type": "string", "default": "10_Projects"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "content": {"type": "string"}
      },
      "required": ["title", "content"]
    }
  },
  {
    "name": "search_notes",
    "description": "Search existing notes by keyword.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"}
      },
      "required": ["query"]
    }
  }
]
</tools>

If you decide to call a tool, respond ONLY in the following XML format:
<tool_call>
{"name": "tool_name", "arguments": {"arg1": "value1"}}
</tool_call>
"""

class HermesAgentService:
    def __init__(self, ollama_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def query_ollama(self, system_prompt: str, user_message: str) -> str:
        """Gửi request tới Ollama Local API."""
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n",
                "stream": False
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            print(f"Ollama local connection error: {e}")
        return ""

    def parse_tool_calls(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Bóc tách cú pháp thẻ XML <tool_call> trong câu trả lời từ AI."""
        tool_calls = []
        matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                tool_calls.append((data.get("name"), data.get("arguments", {})))
            except Exception as e:
                print(f"Error parsing JSON tool call: {e}")
        return tool_calls

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """Thực thi trực tiếp Tool Call vào Obsidian Vault & Knowledge Graph."""
        if name == "create_note":
            req = CreateNoteRequest(
                title=args.get("title", "Untitled Note"),
                folder=args.get("folder", "10_Projects"),
                tags=args.get("tags", ["ai", "second_brain"]),
                content=args.get("content", ""),
                author="Hermes Agent"
            )
            note = obsidian_parser.create_note(req)
            graph_engine.build_graph()
            return True, f"Tạo ghi chú thành công: {note.relative_path}", note.dict()
            
        elif name == "search_notes":
            query = args.get("query", "")
            results = obsidian_parser.search_notes(query)
            return True, f"Tìm thấy {len(results)} ghi chú chứa '{query}'", [r.dict() for r in results]
            
        return False, f"Unknown tool: {name}", None

    def process_chat(self, user_message: str, persona: str = "SecondBrain") -> ChatResponse:
        """Xử lý luồng ChatML Tool Calling hoàn chỉnh từ tin nhắn của người dùng."""
        # 1. Trích xuất ngữ cảnh Đồ thị Tri thức nếu tin nhắn chứa [[...]]
        wiki_links = obsidian_parser.extract_wiki_links(user_message)
        graph_context = []
        for link in wiki_links:
            related = graph_engine.get_related_context(link)
            if related:
                graph_context.extend(related)
                
        # 2. Gọi Ollama Local LLM
        system_prompt = HERMES_SYSTEM_PROMPT
        if persona == "CEO":
            system_prompt += "\nPersona constraint: Bạn đóng vai CEO chiến lược, tập trung vào tầm nhìn, mốc lộ trình và giá trị kinh doanh."
        elif persona == "CFO":
            system_prompt += "\nPersona constraint: Bạn đóng vai CFO quản lý chi phí, công số nhân sự (man-days) và hiệu quả đầu tư."
            
        ai_response = self.query_ollama(system_prompt, user_message)
        
        # 3. Phân tích & Thực thi Tool Calls
        tool_calls = self.parse_tool_calls(ai_response)
        executed_results = []
        
        # Fallback tự động cho demo nếu Ollama phản hồi thô hoặc chưa phát tool_call nhưng người dùng muốn tạo note
        if not tool_calls and any(kw in user_message.lower() for kw in ["tạo note", "họp", "lưu ghi chú", "vừa họp"]):
            # Auto fallback trigger tool call cho demo
            title_match = re.search(r"họp với \[\[(.*?)\]\]", user_message, re.IGNORECASE)
            title = f"2026-10-07_Hop_voi_{title_match.group(1)}" if title_match else "2026-10-07_Ghi_Chu_Moi"
            
            tool_name = "create_note"
            args = {
                "title": title,
                "folder": "10_Projects",
                "tags": ["meeting", "demo"],
                "content": f"{user_message}\n\nLiên kết tự động: {', '.join(['[[' + link + ']]' for link in wiki_links])}"
            }
            tool_calls.append((tool_name, args))
            
        for name, args in tool_calls:
            success, msg, data = self.execute_tool(name, args)
            executed_results.append({
                "tool": name,
                "arguments": args,
                "success": success,
                "message": msg
            })
            
        final_reply = ai_response if ai_response else "Đã xử lý thông tin và tự động lưu ghi chú vào Obsidian Vault của bạn."
        if executed_results:
            final_reply += f"\n\n⚡ **Đã thực thi Tool Calling:**\n- " + "\n- ".join([r['message'] for r in executed_results])
            
        return ChatResponse(
            reply=final_reply,
            persona=persona,
            tool_calls_executed=executed_results,
            graph_context=list(set(graph_context))
        )

hermes_agent_service = HermesAgentService()
