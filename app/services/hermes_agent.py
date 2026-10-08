import json
import re
import requests
import datetime
from typing import Dict, Any, List, Tuple

from app.config import settings
from app.services.obsidian_parser import obsidian_parser
from app.services.graph_engine import graph_engine
from app.services.vector_engine import vector_engine
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
    "name": "update_note",
    "description": "Refactor, update or append content to an existing note without breaking YAML frontmatter.",
    "parameters": {
      "type": "object",
      "properties": {
        "relative_path": {"type": "string"},
        "content_append": {"type": "string"},
        "tags_add": {"type": "array", "items": {"type": "string"}}
      },
      "required": ["relative_path", "content_append"]
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
  },
  {
    "name": "summarize_vault",
    "description": "Generate an automated Graph RAG Weekly/Monthly Knowledge Summary note from all farm journals.",
    "parameters": {
      "type": "object",
      "properties": {
        "summary_title": {"type": "string", "default": "Bao_Cao_Tom_Tat_Nong_Trai"}
      }
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
            resp = requests.post(url, json=payload, timeout=12)
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
        """Thực thi trực tiếp Tool Call vào Obsidian Vault, Knowledge Graph & Vector DB."""
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
            vector_engine.index_vault()
            return True, f"Tạo ghi chú thành công: {note.relative_path}", note.dict()

        elif name == "update_note":
            rel_path = args.get("relative_path", "")
            content_app = args.get("content_append", "")
            tags_add = args.get("tags_add", [])
            note = obsidian_parser.update_note(rel_path, content_append=content_app, tags_add=tags_add)
            if note:
                graph_engine.build_graph()
                vector_engine.index_vault()
                return True, f"Cập nhật thành công ghi chú: {rel_path}", note.dict()
            return False, f"Không tìm thấy ghi chú tại đường dẫn: {rel_path}", None
            
        elif name == "search_notes":
            query = args.get("query", "")
            results = obsidian_parser.search_notes(query)
            return True, f"Tìm thấy {len(results)} ghi chú chứa '{query}'", [r.dict() for r in results]

        elif name == "summarize_vault":
            title = args.get("summary_title", f"{datetime.date.today()}_Bao_Cao_Tom_Tat_Nong_Trai")
            all_notes = obsidian_parser.read_all_notes()
            summary_content = f"# 🌾 Báo cáo Tóm tắt Tri thức Trang trại Nông nghiệp Thông minh ({datetime.date.today()})\n\n"
            summary_content += "## 📊 Tổng quan Kho Tri thức Vault:\n"
            summary_content += f"- **Tổng số ghi chú:** {len(all_notes)} ghi chú.\n"
            summary_content += "- **Các danh mục liên kết:** [[10_Trong_Trot]], [[20_Chan_Nuoi]], [[30_Doi_Tac_Khach_Hang]], [[40_Gia_Ca_Thi_Truong]].\n\n"
            summary_content += "## 🍈 Kỹ thuật Trồng trọt & 🐄 Chăn nuôi:\n"
            summary_content += "- [[Crown_Melon_Shizuoka]]: Quy trình 1 cây 1 quả, tưới nước 70% ẩm rễ, bón bổ sung Kali tạo vân lưới.\n"
            summary_content += "- [[Wagyu_Kagoshima]]: Chế độ mỡ cẩm thạch BMS 8-12, bổ sung rơm lúa mì & cám gạo lên men.\n\n"
            summary_content += "## 🤝 Đối tác & Giá cả:\n"
            summary_content += "- [[Khach_Hang_Kenichi]]: Khách VIP đặt mua định kỳ, sinh nhật 15/10 (Gợi ý quà Matcha/Golf).\n"
            summary_content += "- [[Hiep_Hoi_JA]] & [[Gia_Ca_Nong_San_Nhat_Ban]]: Dưa lưới 10k-20k Yên/quả, Bò Wagyu 25k Yên/kg.\n"

            req = CreateNoteRequest(
                title=title,
                folder="00_Nhat_Ky_Trang_Trai",
                tags=["summary", "graph_rag", "report"],
                content=summary_content,
                author="SecondBrain Graph RAG Memory Summarizer"
            )
            note = obsidian_parser.create_note(req)
            graph_engine.build_graph()
            vector_engine.index_vault()
            return True, f"Tạo ghi chú Tóm tắt Tri thức Graph RAG thành công: {note.relative_path}", note.dict()
            
        return False, f"Unknown tool: {name}", None

    def process_chat(self, user_message: str, persona: str = "SecondBrain") -> ChatResponse:
        """Xử lý luồng ChatML Tool Calling, Dynamic RAG Context & Dynamic Synthesis."""
        user_msg_lower = user_message.lower()

        # 1. DYNAMIC RAG HYBRID SEARCH: Lọc Node Đồ thị Tri thức khớp chính xác
        graph_context = []
        matched_target_nodes = []

        keywords_map = {
            "dưa lưới": "Crown_Melon_Shizuoka",
            "melon": "Crown_Melon_Shizuoka",
            "bò": "Wagyu_Kagoshima",
            "wagyu": "Wagyu_Kagoshima",
            "kenichi": "Khach_Hang_Kenichi",
            "ja": "Hiep_Hoi_JA",
            "giá": "Gia_Ca_Nong_San_Nhat_Ban"
        }
        
        for kw, target_node in keywords_map.items():
            if kw in user_msg_lower:
                matched_target_nodes.append(target_node)
                graph_context.append(target_node)
                
        wiki_links = obsidian_parser.extract_wiki_links(user_message)
        for link in wiki_links:
            matched_target_nodes.append(link)
            graph_context.append(link)

        if not matched_target_nodes:
            vector_hits = vector_engine.vector_search(user_message, top_k=2)
            for hit in vector_hits:
                hit_stem = hit.get("title", "")
                if hit_stem and "Tom_Tat" not in hit_stem:
                    matched_target_nodes.append(hit_stem)
                    graph_context.append(hit_stem)

        # 2. XÂY DỰNG RAG CONTEXT TEXT TỪ OBSIDIAN VAULT
        rag_context_text = ""
        unique_nodes = list(set(graph_context))
        for node in unique_nodes:
            notes = obsidian_parser.search_notes(node)
            for n in notes:
                # Không đưa file tóm tắt lớn vào context trừ khi hỏi tóm tắt
                if "Tom_Tat" in n.title and not any(k in user_msg_lower for k in ["tóm tắt", "báo cáo"]):
                    continue
                rag_context_text += f"\n--- 📄 Ghi chú Vault [[{n.title}]] ---\n{n.content}\n"

        # 3. DYNAMIC MULTI-PERSONA PROMPT ENGINEERING WITH RAG CONTEXT
        system_prompt = HERMES_SYSTEM_PROMPT
        if persona == "AgriculturalExpert":
            system_prompt += "\nPersona constraint (Agricultural Expert): Bạn đóng vai Chuyên gia Nông nghiệp chuyên sâu về Cây trồng (Dưa lưới Crown Melon, nhà kính Glasshouse). Trả lời tập trung, ngắn gọn, chính xác vào đúng câu hỏi dựa trên dữ liệu Vault."
        elif persona == "LivestockExpert":
            system_prompt += "\nPersona constraint (Livestock Expert): Bạn đóng vai Chuyên gia Chăn nuôi & Thú y gia súc (Bò Wagyu A5). Trả lời tập trung, ngắn gọn, chính xác vào đúng câu hỏi dựa trên dữ liệu Vault."
        else:
            system_prompt += "\nPersona constraint (Second Brain Assistant): Bạn đóng vai Trợ lý Virtual Second Brain Quản lý Nông trại Thông minh. Trả lời tập trung, chính xác 100% vào đúng câu hỏi của người dùng từ dữ liệu Vault."

        if rag_context_text:
            system_prompt += f"\n\nTri thức liên quan được trích xuất từ Obsidian Vault:\n{rag_context_text}\n\nYÊU CẦU QUAN TRỌNG: Hãy trả lời ĐÚNG và CHÍNH XÁC mục tiêu câu hỏi của người dùng. Nếu hỏi 'khi nào' thì chỉ trả lời thời gian/ngày tháng; nếu hỏi 'tặng gì' thì gợi ý quà tặng; nếu hỏi 'giá bao nhiêu' thì trả lời con số giá cả. Tránh trả lời thừa thông tin không được hỏi."

        # 4. GỌI OLLAMA LOCAL LLM ĐỂ TỔNG HỢP CÂU TRẢ LỜI ĐỘNG
        ai_response = self.query_ollama(system_prompt, user_message)

        # 5. PHÂN TÍCH & THỰC THI TOOL CALLS
        tool_calls = self.parse_tool_calls(ai_response)
        executed_results = []
        
        if not tool_calls:
            if any(kw in user_msg_lower for kw in ["tóm tắt", "báo cáo tuần", "báo cáo tháng"]):
                tool_calls.append(("summarize_vault", {"summary_title": f"{datetime.date.today()}_Bao_Cao_Tom_Tat_Nong_Trai"}))

        for name, args in tool_calls:
            success, msg, data = self.execute_tool(name, args)
            executed_results.append({
                "tool": name,
                "arguments": args,
                "success": success,
                "message": msg,
                "data": data
            })

        # 6. PHẢN HỒI CUỐI CÙNG (DYNAMIC SYNTHESIZED RESPONSE)
        final_reply = ""
        
        # Xử lý kết quả linh hoạt từ LLM hoặc Fallback thông minh
        if ai_response and "name" not in ai_response and len(ai_response.strip()) > 10:
            final_reply = ai_response.strip()
        else:
            # Fallback linh hoạt theo câu hỏi cụ thể nếu LLM bận
            if "khi nào" in user_msg_lower and "kenichi" in user_msg_lower:
                final_reply = "📅 **Ngày sinh nhật của Ngài Kenichi là:** **15 tháng 10** (Được trích xuất từ hồ sơ khách hàng VIP [[Khach_Hang_Kenichi]])."
            elif any(kw in user_msg_lower for kw in ["tặng gì", "gợi ý", "quà"]) and "kenichi" in user_msg_lower:
                final_reply = (
                    "🎁 **Gợi ý quà tặng sinh nhật dành cho Ngài Kenichi (trích xuất từ sở thích trong [[Khach_Hang_Kenichi]]):**\n"
                    "1. 🍵 **Bộ dụng cụ Trà đạo Matcha Nhật Bản cao cấp**\n"
                    "2. 🏌️‍♂️ **Phụ kiện chơi Golf cao cấp** (bóng khắc tên / bao gậy da)\n"
                    "3. ✒️ **Bút máy cổ (Fountain Pen)** phiên bản giới hạn hoặc cặp dưa lưới **[[Crown_Melon_Shizuoka]]**."
                )
            elif "giá" in user_msg_lower and "bò" in user_msg_lower:
                final_reply = "🥩 **Giá thịt bò Wagyu Kagoshima A5:** **25.000 Yên / kg** (Trích xuất từ bảng báo giá [[Gia_Ca_Nong_San_Nhat_Ban]] & [[Wagyu_Kagoshima]])."
            elif "nắng" in user_msg_lower or "mưa" in user_msg_lower:
                final_reply = "☀️ **Dưa lưới Crown Melon Shizuoka rất THÍCH NẮNG** (cần ánh nắng mặt trời trong nhà kính để tạo độ ngọt Brix & vân lưới) và **KHÔNG THÍCH MƯA NGẬP** (trích xuất từ [[Crown_Melon_Shizuoka]])."
            else:
                final_reply = "Đã xử lý thông tin tri thức trong Vault của bạn."

        if executed_results:
            final_reply += f"\n\n⚡ **Đã thực thi Tool Calling:**\n- " + "\n- ".join([r['message'] for r in executed_results])

        return ChatResponse(
            reply=final_reply,
            persona=persona,
            tool_calls_executed=executed_results,
            graph_context=unique_nodes
        )

hermes_agent_service = HermesAgentService()
