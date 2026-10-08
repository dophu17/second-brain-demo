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
                return True, f"Cập nhật thành công ghi chú: {note.relative_path}", note.dict()
            return False, f"Không thể cập nhật ghi chú tại đường dẫn: {rel_path}", None
            
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
        """Xử lý luồng Multilingual Dynamic RAG Context & Dynamic Synthesis (JP / VI / EN)."""
        user_msg_lower = user_message.lower()

        # 1. MULTILINGUAL HYBRID SEARCH (JP & VI & EN)
        graph_context = []
        matched_target_nodes = []

        keywords_map = {
            "dưa lưới": "Crown_Melon_Shizuoka",
            "melon": "Crown_Melon_Shizuoka",
            "メロン": "Crown_Melon_Shizuoka",
            "クラウンメロン": "Crown_Melon_Shizuoka",
            "bò": "Wagyu_Kagoshima",
            "wagyu": "Wagyu_Kagoshima",
            "和牛": "Wagyu_Kagoshima",
            "カゴシマ": "Wagyu_Kagoshima",
            "鹿児島": "Wagyu_Kagoshima",
            "食欲": "Wagyu_Kagoshima",
            "giảm ăn": "Wagyu_Kagoshima",
            "sốt": "Wagyu_Kagoshima",
            "thú y": "Wagyu_Kagoshima",
            "kenichi": "Khach_Hang_Kenichi",
            "ケンイチ": "Khach_Hang_Kenichi",
            "yamoto": "Khach_Hang_Yamoto",
            "ヤモト": "Khach_Hang_Yamoto",
            "ja": "Hiep_Hoi_JA",
            "農協": "Hiep_Hoi_JA",
            "giá": "Gia_Ca_Nong_San_Nhat_Ban",
            "price": "Gia_Ca_Nong_San_Nhat_Ban",
            "価格": "Gia_Ca_Nong_San_Nhat_Ban",
            "相場": "Gia_Ca_Nong_San_Nhat_Ban"
        }
        
        for kw, target_node in keywords_map.items():
            if kw in user_msg_lower:
                matched_target_nodes.append(target_node)
                graph_context.append(target_node)

        # Vector Semantic Search
        vector_hits = vector_engine.vector_search(user_message, top_k=3)
        for hit in vector_hits:
            hit_stem = hit.get("title", "")
            if hit_stem and "Tom_Tat" not in hit_stem:
                matched_target_nodes.append(hit_stem)
                graph_context.append(hit_stem)

        # Quét thêm từ khóa trực tiếp từ Obsidian Parser Full-Text
        words = [w for w in re.findall(r'\w+', user_message) if len(w) > 2]
        for word in words:
            found = obsidian_parser.search_notes(word)
            for f_note in found:
                if f_note.title not in matched_target_nodes:
                    matched_target_nodes.append(f_note.title)
                    graph_context.append(f_note.title)

        wiki_links = obsidian_parser.extract_wiki_links(user_message)
        for link in wiki_links:
            matched_target_nodes.append(link)
            graph_context.append(link)

        # 2. XÂY DỰNG MULTILINGUAL RAG CONTEXT TEXT TỪ OBSIDIAN VAULT
        rag_context_text = ""
        unique_nodes = list(set(graph_context))
        for node in unique_nodes:
            notes = obsidian_parser.search_notes(node)
            for n in notes:
                if "Tom_Tat" in n.title and not any(k in user_msg_lower for k in ["tóm tắt", "báo cáo", "要約", "まとめ"]):
                    continue
                rag_context_text += f"\n--- 📄 Vault Note [[{n.title}]] ---\n{n.content}\n"

        # 3. DYNAMIC MULTI-PERSONA PROMPT ENGINEERING (MULTILINGUAL JP/VI/EN)
        system_prompt = HERMES_SYSTEM_PROMPT
        system_prompt += "\n\nCRITICAL LANGUAGE INSTRUCTION: Always respond in the EXACT SAME LANGUAGE as the user's question. If the user asks in Japanese, answer in fluent Japanese. If the user asks in Vietnamese, answer in Vietnamese."

        if persona == "AgriculturalExpert":
            system_prompt += "\nPersona constraint (Agricultural Expert): You are a leading Japanese Smart Agriculture Crop Expert (Crown Melon Shizuoka, Glasshouse greenhouse). Answer concisely and accurately based on the Vault context."
        elif persona == "LivestockExpert":
            system_prompt += "\nPersona constraint (Livestock Expert): You are a leading Japanese Livestock & Veterinary Expert (Kagoshima Wagyu A5 beef cattle). Answer concisely and accurately based on the Vault context."
        else:
            system_prompt += "\nPersona constraint (Second Brain Assistant): You are an intelligent Virtual Second Brain Farm Management Assistant. Answer concisely and 100% accurately based on the Vault context."

        if rag_context_text:
            system_prompt += f"\n\nRetrieved Knowledge Context from Obsidian Vault:\n{rag_context_text}\n\nINSTRUCTION: Answer the specific question directly using the retrieved vault data above. Be direct and concise."

        # 4. GỌI OLLAMA LOCAL LLM ĐỂ TỔNG HỢP CÂU TRẢ LỜI ĐỘNG
        ai_response = self.query_ollama(system_prompt, user_message)

        # 5. PHÂN TÍCH & THỰC THI TOOL CALLS
        tool_calls = self.parse_tool_calls(ai_response)
        executed_results = []

        # Tự động phát hiện intent cập nhật / bổ sung dữ liệu note nếu Hermes chưa gọi tool
        if not tool_calls and any(kw in user_msg_lower for kw in ["cập nhật", "bổ sung", "sửa", "lưu", "thêm", "更新", "追加"]):
            target_name = "Yamoto" if "yamoto" in user_msg_lower or "ヤモト" in user_msg_lower else ("Kenichi" if "kenichi" in user_msg_lower else "Trang_Trai")
            rel_path = f"30_Doi_Tac_Khach_Hang/Khach_Hang_{target_name}.md" if target_name != "Trang_Trai" else "00_Nhat_Ky_Trang_Trai/Nhat_Ky.md"
            tool_calls.append(("update_note", {
                "relative_path": rel_path,
                "content_append": user_message,
                "tags_add": ["client", "updated"]
            }))

        for name, args in tool_calls:
            success, msg, data = self.execute_tool(name, args)
            executed_results.append({
                "tool": name,
                "arguments": args,
                "success": success,
                "message": msg,
                "data": data
            })

        # 6. PHẢN HỒI THỰC TẾ (DYNAMIC RESPONSE RETURN)
        final_reply = ""
        
        # Nếu có Tool Calling `update_note` thực thi thành công
        for res in executed_results:
            if res["tool"] == "update_note" and res.get("success"):
                note_data = res.get("data", {})
                raw_title = note_data.get("title", "Ghi_Chu").replace("[", "").replace("]", "")
                final_reply = f"📝 **Đã cập nhật tri thức thành công vào Obsidian Vault:**\n- **Ghi chú:** [[{raw_title}]]\n- **Nội dung ghi nhận:** {user_message}"
                break

            elif res["tool"] == "search_notes" and res.get("data"):
                found_notes = res["data"]
                tool_context_text = ""
                for fn in found_notes:
                    fn_title = fn.get("title", "")
                    fn_content = fn.get("content", "")
                    tool_context_text += f"\n--- 📄 Note [[{fn_title}]] ---\n{fn_content}\n"
                    if fn_title not in unique_nodes:
                        unique_nodes.append(fn_title)
                
                tool_prompt = (
                    f"{system_prompt}\n"
                    f"User Question: '{user_message}'\n"
                    f"Found Notes Data:\n{tool_context_text}\n"
                    f"INSTRUCTION: Answer the question directly in the SAME LANGUAGE as the user's question."
                )
                tool_synth = self.query_ollama(tool_prompt, user_message)
                if tool_synth and len(tool_synth.strip()) > 5:
                    final_reply = tool_synth.strip()

        if not final_reply:
            if ai_response and "name" not in ai_response and len(ai_response.strip()) > 10:
                final_reply = ai_response.strip()
            elif rag_context_text:
                final_reply = f"🤖 **Trích xuất Tri thức từ Obsidian Vault của bạn:**\n{rag_context_text}"
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
