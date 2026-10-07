# Second Brain AI Product - Technical Documentation & Research Hub

Chào mừng bạn đến với kho tài liệu tổng hợp khảo sát kỹ thuật dự án **Bộ Não Thông Minh Thứ Hai (Second Brain AI Product / 人を天才にするAIプロダクト)**.

---

## 📌 Nội dung Tài liệu Chính (Master Document)

Toàn bộ thông tin khảo sát kỹ thuật, kiến trúc hệ thống, phương pháp luận và kế hoạch phân công công việc được tổng hợp chi tiết tại:

👉 [**SECOND_BRAIN_MASTER_RESEARCH.md**](file:///c:/dophu17/balocco_apps/second-brain-demo/SECOND_BRAIN_MASTER_RESEARCH.md)

---

## 📁 Thư mục Quản lý Task & Báo cáo Hàng ngày (`reports/`)

Cấu trúc thư mục `reports/` được tổ chức theo từng ngày làm việc (Task ticket định nghĩa yêu cầu & Output kết quả khảo sát):

* 📂 [**`reports/2026-10-01/`**](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-01/)
  - [`task-2026-10-01.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-01/task-2026-10-01.md): Nhiệm vụ đọc hiểu cuộc họp JP, phân tách 2 dự án & tìm hiểu Zettelkasten.
  - [`output-2026-10-01.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-01/output-2026-10-01.md): 5 điểm cốt lõi của phương pháp Zettelkasten áp dụng cho dự án.
* 📂 [**`reports/2026-10-05/`**](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-05/)
  - [`2026-10-05.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-05/2026-10-05.md): Ticket khảo sát kỹ thuật Markdown Parser (Wiki-links/Metadata) & Hermes Agent (6h).
  - [`output-2026-10-05.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-05/output-2026-10-05.md): Kết quả khảo sát 5 điểm kỹ thuật quan trọng của Parser & Hermes Agent.
* 📂 [**`reports/2026-10-06/`**](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-06/)
  - [`task-2026-10-06.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-06/task-2026-10-06.md): Ticket lập kế hoạch phát triển tổng thể & Roadmap cho dự án (6h).
  - [`output-2026-10-06.md`](file:///c:/dophu17/balocco_apps/second-brain-demo/reports/2026-10-06/output-2026-10-06.md): Báo cáo kết quả lập kế hoạch & WBS phát triển.

---

## 📑 Tóm tắt Các Mảng Kiến thức Trong Dự án

1. **Phương pháp luận Quản lý Tri thức (Core Concept):**
   - Zettelkasten (Fleeting Notes, Literature Notes, Permanent Notes, Bi-directional Linking `[[Note]]`).
   - Toshio Okada's Smart Note (スマートノート).
   - Building a Second Brain (BASA / PARA Method - Tiago Forte).

2. **Hệ sinh thái Obsidian (Data Layer & Knowledge Graph):**
   - Cấu trúc file Markdown thuần, YAML Frontmatter, Wiki-links `[[...]]`, tags, aliases.
   - Thao tác Vault qua File System vs Local REST API Plugin.
   - Bảng so sánh thư viện Parser (Unified / `gray-matter` / `markdown-it` / Python options).

3. **Kiến trúc AI & Agent (Intelligence Layer):**
   - Hermes Agent (Nous Research Hermes 2/3, ChatML prompt format, `<tools>`, `<tool_call>`).
   - Graph RAG (Vector Search + Wiki-link Traversal).
   - Multi-Persona prompting framework (CEO, CFO, CMO, Second Brain Alter-Ego).

4. **Giao diện & Trải nghiệm Người dùng (UI/UX Layer):**
   - LINE Bot Integration (Webhook, Flex Messages, Quick Reply).
   - Quick Capture 1-touch trên Tablet Mini 8-inch & Voice STT (Whisper).

5. **Nhiệm vụ Quản lý PL & Phân công Team:**
   - **Khôi:** LINE Bot & STT Pipeline.
   - **Phố:** Obsidian Vault Data Layer & Markdown Parser Engine.
   - **An:** AI Intelligence Layer & Hermes Agent Specification.
   - Quy trình báo cáo công việc cho JP (`ベトナムメンバーの報告書の仕組みの対応`).
