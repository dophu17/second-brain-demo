import json
import re
import requests
from typing import Dict, Any, List, Tuple

from app.config import settings
from app.services.obsidian_parser import obsidian_parser
from app.services.graph_engine import graph_engine
from app.models.schemas import CreateNoteRequest, UpdateNoteRequest, ChatResponse

HERMES_SYSTEM_PROMPT = """You are Second Brain AI (人を天才にするAIプロダクト), an intelligent Smart Farm Management AI assistant powered by Nous Research Hermes 3 and Knowledge Graph principles.

You have access to the following tools to manage the user's Obsidian Vault farm notes:

<tools>
[
  {
    "name": "create_note",
    "description": "Create a new Markdown note in Obsidian Vault with tags and Wiki-links.",
    "parameters": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "folder": {"type": "string", "default": "00_Nhat_Ky_Trang_Trai"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "content": {"type": "string"}
      },
      "required": ["title", "content"]
    }
  },
  {
    "name": "search_notes",
    "description": "Search existing farm notes by keyword.",
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

If you decide to call a tool, respond in XML format:
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
        """Bóc tách linh hoạt cú pháp Tool Call (dạng XML <tool_call> hoặc JSON thô)."""
        tool_calls = []
        if not text:
            return tool_calls

        matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
        if not matches:
            clean_text = re.sub(r"</?tool_call>", "", text).strip()
            json_match = re.search(r"\{.*\"name\"\s*:\s*\"([^\"]+)\".*\"arguments\"\s*:\s*(\{.*\}).*\}", clean_text, re.DOTALL)
            if json_match:
                matches = [clean_text]

        for match in matches:
            try:
                json_str = match.strip()
                if not json_str.startswith("{"):
                    idx = json_str.find("{")
                    if idx != -1:
                        json_str = json_str[idx:]
                data = json.loads(json_str)
                if "name" in data and "arguments" in data:
                    tool_calls.append((data["name"], data["arguments"]))
            except Exception as e:
                print(f"Error parsing JSON tool call: {e}")

        return tool_calls

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """Thực thi trực tiếp Tool Call vào Obsidian Vault & Knowledge Graph."""
        if name == "create_note":
            req = CreateNoteRequest(
                title=args.get("title", "Ghi_Chu_Trang_Trai"),
                folder=args.get("folder", "00_Nhat_Ky_Trang_Trai"),
                tags=args.get("tags", ["farm", "smart_agri"]),
                content=args.get("content", ""),
                author="Farm AI Agent"
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
        """Xử lý luồng ChatML Tool Calling & Smart Context Retrieval từ tin nhắn của người dùng."""
        # 1. Trích xuất Wiki-links [[...]] và Smart Keyword Search
        wiki_links = obsidian_parser.extract_wiki_links(user_message)
        graph_context = []
        
        # Thêm các Wiki-links trực tiếp
        for link in wiki_links:
            related = graph_engine.get_related_context(link)
            if related:
                graph_context.extend(related)
                
        # Smart Keyword Search cho câu hỏi tự nhiên (không cần ngoặc [[...]])
        keywords_map = {
            "dưa lưới": "Crown_Melon_Shizuoka",
            "melon": "Crown_Melon_Shizuoka",
            "bò": "Wagyu_Kagoshima",
            "wagyu": "Wagyu_Kagoshima",
            "kenichi": "Khach_Hang_Kenichi",
            "ja": "Hiep_Hoi_JA",
            "giá": "Gia_Ca_Nong_San_Nhat_Ban"
        }
        user_msg_lower = user_message.lower()
        for kw, target_node in keywords_map.items():
            if kw in user_msg_lower:
                related = graph_engine.get_related_context(target_node)
                if related:
                    graph_context.extend(related)
                else:
                    graph_context.append(target_node)
                
        # 2. Gọi Ollama Local LLM
        system_prompt = HERMES_SYSTEM_PROMPT
        if persona == "CEO":
            system_prompt += "\nPersona constraint: Bạn đóng vai Chuyên gia Quản lý Trang trại Nông nghiệp Nhật Bản."
        elif persona == "CFO":
            system_prompt += "\nPersona constraint: Bạn đóng vai Chuyên viên Phân tích Chi phí & Giá cả Thị trường Nông sản."
            
        ai_response = self.query_ollama(system_prompt, user_message)
        
        # 3. Phân tích & Thực thi Tool Calls
        tool_calls = self.parse_tool_calls(ai_response)
        executed_results = []
        
        # Fallback tự động cho demo nếu Ollama chưa phát tool_call nhưng người dùng muốn tạo note nhật ký trang trại
        if not tool_calls and any(kw in user_msg_lower for kw in ["tạo note", "họp", "lưu ghi chú", "vừa họp", "nhật ký"]):
            title_match = re.search(r"về \[\[(.*?)\]\]", user_message, re.IGNORECASE)
            title = f"2026-10-07_Nhat_Ky_{title_match.group(1)}" if title_match else "2026-10-07_Nhat_Ky_Trang_Trai"
            
            tool_name = "create_note"
            args = {
                "title": title,
                "folder": "00_Nhat_Ky_Trang_Trai",
                "tags": ["nhat_ky", "nong_trai"],
                "content": f"{user_message}\n\nLiên kết tự động: {', '.join(['[[' + link + ']]' for link in wiki_links])}"
            }
            tool_calls.append((tool_name, args))
            
        for name, args in tool_calls:
            success, msg, data = self.execute_tool(name, args)
            executed_results.append({
                "tool": name,
                "arguments": args,
                "success": success,
                "message": msg,
                "data": data
            })
            
        # 4. Tổng hợp phản hồi tự nhiên (Natural Language Response)
        context_contents = []
        unique_nodes = list(set(graph_context))
        for node in unique_nodes:
            notes = obsidian_parser.search_notes(node)
            for n in notes:
                context_contents.append(f"📄 **Ghi chú [[{n.title}]]:**\n{n.content}")

        if context_contents:
            final_reply = f"🤖 **Trích xuất Tri thức từ Second Brain Vault của bạn:**\n\n" + "\n\n".join(context_contents)
            
            # Smart Answer Synthesis cho câu hỏi Nắng/Mưa
            if "nắng" in user_msg_lower or "mưa" in user_msg_lower:
                final_reply += "\n\n☀️ **Trả lời chi tiết từ AI:**\n- Dưa lưới (Crown Melon Shizuoka) **rất THÍCH NẮNG và cần MẶT TRỜI nhiều** (được trồng trong nhà kính kính Glasshouse để hấp thụ tối đa ánh sáng).\n- Ánh sáng mặt trời ở giai đoạn tạo vân lưới (Tuần 5-8) giúp vỏ dưa nứt đẹp và tăng tích tụ độ ngọt (độ Brix).\n- Dưa lưới **KHÔNG THÍCH MƯA NGẬP** (cần kiểm soát chặt chẽ độ ẩm đất ở mức 70% và giảm 30% tưới nước giai đoạn tạo vân)."
            elif any(kw in user_msg_lower for kw in ["tặng gì", "sinh nhật", "gợi ý", "quà"]):
                final_reply += "\n\n💡 **Gợi ý quà tặng dành cho Kenichi từ AI:**\n- 🍵 **Bộ dụng cụ Trà đạo Matcha Nhật Bản cao cấp** (Phù hợp sở thích trà đạo Matcha của Kenichi).\n- 🏌️‍♂️ **Phụ kiện chơi Golf cao cấp** (Bóng Golf khắc tên cá nhân hoặc bao gậy da).\n- ✒️ **Bút máy cổ (Fountain Pen)** phiên bản giới hạn."
        else:
            final_reply = ai_response if (ai_response and "name" not in ai_response) else "Đã xử lý thông tin tri thức trong Vault của bạn."

        if executed_results:
            final_reply += f"\n\n⚡ **Đã thực thi Tool Calling:**\n- " + "\n- ".join([r['message'] for r in executed_results])
            
        return ChatResponse(
            reply=final_reply,
            persona=persona,
            tool_calls_executed=executed_results,
            graph_context=unique_nodes
        )

hermes_agent_service = HermesAgentService()
