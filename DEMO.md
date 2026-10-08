# BÁO CÁO CẤU TRÚC KHOA HỌC & KĨ THUẬT DEMO BỘ NÃO THỨ 2 QUẢN LÝ TRANG TRẠI NÔNG NGHIỆP NHẬT BẢN (DEMO.md)
**Dự án:** Người làm cho con người trở thành Thiên tài AI (人を天才にするAIプロダクト / Second Brain AI)

> **Ngày cập nhật:** 07/10/2026  
> **Miền ứng dụng:** Nông nghiệp Thông minh & Quản lý Trang trại Nhật Bản (スマート農業・農場管理)  
> **Phân công thực hiện:** Phú (Dev Solo Implementation), Độ (PM)  
> **Lưu ý phạm vi:** Giản lược phần giao diện LINE Bot/Voice STT, tập trung 100% vào **Kiến trúc Cốt lõi AI Agent, NetworkX Knowledge Graph & Obsidian Vault Nông nghiệp**.

---

## 📂 1. Cấu trúc Danh mục Quản lý Nông nghiệp Khoa học (Scientific Farm Vault Structure)

Thư mục `10_Projects` cũ trước đây là tên mặc định của phương pháp Zettelkasten chung. Khi áp dụng trực tiếp cho miền Nông nghiệp Nhật Bản, thư mục được tái cấu trúc thành các danh mục chuyên biệt, khoa học và dễ quản lý:

```
vault/
├── 00_Nhat_Ky_Trang_Trai/         # Tiếp nhận ghi chú hàng ngày & Nhật ký canh tác tự động
│   └── Welcome_Nong_Trai.md
├── 10_Trong_Trot/                 # Quy trình & Kỹ thuật trồng trọt nông sản Nhật Bản
│   └── Crown_Melon_Shizuoka.md    # Kỹ thuật trồng Dưa lưới Shizuoka (bón Kali, giảm 30% tưới nước)
├── 20_Chan_Nuoi/                  # Quy trình chăn nuôi, dinh dưỡng & thú y gia súc
│   └── Wagyu_Kagoshima.md         # Quy trình chăn nuôi & chăm sóc sức khỏe Bò Wagyu A5
├── 30_Doi_Tac_Khach_Hang/         # Khách hàng thân thiết & Đơn vị bao tiêu xuất khẩu
│   ├── Hiep_Hoi_JA.md             # Hiệp hội Nông nghiệp Nhật Bản (JA農協)
│   └── Khach_Hang_Kenichi.md      # Hồ sơ khách hàng VIP thu mua (đã lưu sở thích: Trà đạo, Golf, Bút máy)
└── 40_Gia_Ca_Thi_Truong/          # Báo giá thị trường & biến động chi phí vật tư nông nghiệp
    └── Gia_Ca_Nong_San_Nhat_Ban.md
```

---

## 🏗️ 2. Mô hình Kiến trúc Kỹ thuật Hệ thống (Docker + Ollama Local + Obsidian Vault)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         MÁY LOCAL DEV (HOST OS)                          │
│                                                                          │
│  ┌───────────────────────────┐           ┌────────────────────────────┐  │
│  │   Ollama Local LLM Server │           │    Obsidian Vault Local    │  │
│  │   http://localhost:11434  │           │      (./vault/*.md)        │  │
│  └─────────────▲─────────────┘           └─────────────▲──────────────┘  │
│                │                                       │                  │
│                │ http://host.docker.internal:11434     │ Mount Volume     │
│                │                                       │ ./vault:/app/vault
│  ┌─────────────┴───────────────────────────────────────┴───────────────┐  │
│  │                   DOCKER CONTAINER (second-brain-app)               │  │
│  │                                                                     │  │
│  │ 🚀 FastAPI Server (app/main.py) - Port 8008                         │  │
│  │ 📄 Obsidian Parser (python-frontmatter + Regex Wiki-links)        │  │
│  │ 🕸️ NetworkX Knowledge Graph Engine (Backlinks calculation)        │  │
│  │ 🤖 Hermes Agent Client (Tool Calling: search, create, update)     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🟢 3. CÁC KỸ THUẬT ĐÃ TRIỂN KHAI THÀNH CÔNG (Implemented Core Technologies)

| STT | Kỹ thuật / Công nghệ | Trạng thái | Chi tiết Kỹ thuật đã Thực thi |
| --- | --- | --- | --- |
| 1 | **Local-first Persistence & Volume Mount** | 🟢 **Hoàn thành** | Dữ liệu lưu trữ dạng Markdown `.md` chuẩn Zettelkasten. Mount volume Docker (`./vault:/app/vault`) giúp đồng bộ thời gian thực với phần mềm Obsidian trên máy host. |
| 2 | **YAML Frontmatter & Wiki-Links Parser** | 🟢 **Hoàn thành** | Module `obsidian_parser.py` bóc tách tự động metadata cấu trúc (tags, date, author, category) và trích xuất liên kết ngữ nghĩa hai chiều `[[Wiki-links]]` bằng Regex. |
| 3 | **Directed Knowledge Graph Engine** | 🟢 **Hoàn thành** | Module `graph_engine.py` dùng **NetworkX** xây dựng Đồ thị Tri thức (Nodes & Edges), tính toán liên kết ngược (**Backlinks**) và trích xuất ngữ cảnh khu vực đồ thị (Graph Neighborhood Context). |
| 4 | **ChatML Agent Tool Calling Core** | 🟢 **Hoàn thành** | Module `hermes_agent.py` tích hợp Ollama Local LLM, định dạng ChatML `<tools>`, `<tool_call>`, tự động thực thi Tool Calling (`create_note`, `update_note`, `search_notes`). |
| 5 | **Entity-Centric Context Ingestion** | 🟢 **Hoàn thành** | Tự động đọc và trích xuất thuộc tính thực thể (ví dụ: sở thích trà đạo, sinh nhật của ngài Kenichi trong `Khach_Hang_Kenichi.md`) để AI tự động suy luận & gợi ý quà tặng / quyết định cá nhân hóa. |
| 6 | **Docker Containerization & Network Host Routing** | 🟢 **Hoàn thành** | Đóng gói ứng dụng bằng Docker Compose (`ports: 8008:8000`), định tuyến mạng `host.docker.internal:11434` kết nối Ollama offline không cần gọi API đám mây. |
| 7 | **RESTful API & OpenAPI Interactive UI** | 🟢 **Hoàn thành** | FastAPI server cung cấp các endpoints `/api/demo/chat`, `/api/demo/notes`, `/api/demo/graph` và Swagger UI tương tác tại `http://localhost:8008/docs`. |
| 8 | **LINE-Style Web Chatbox Interface** | 🟢 **Hoàn thành** | Phục vụ Giao diện Web Chatbox trực quan phong cách LINE (`#06C755`) tại `http://localhost:8008/` cho phép trò chuyện trực tiếp, chuyển đổi 3 Persona (`AgriculturalExpert`, `LivestockExpert`, `SecondBrain`), bấm nhanh câu hỏi mẫu và hiển thị node `graph_context`. |

---

## 🟢 4. CÁC KỸ THUẬT NÂNG CẤP CỐT LÕI AI & DATA (Đã Triển khai Hoàn tất)

| STT | Kỹ thuật / Công nghệ Nâng cấp | Trạng thái | Chi tiết Đã Triển khai |
| --- | --- | --- | --- |
| 1 | **ChromaDB Vector Store & Hybrid Search (Graph RAG)** | **🟢 Đã Hoàn Thành** | Tích hợp `vector_engine.py` với **ChromaDB Client**. Kết hợp **Vector Semantic Search** (tìm kiếm ngữ nghĩa) + **NetworkX Graph Traversal** (đồ thị tri thức 2 chiều) tạo nên mô hình **Hybrid Graph RAG**. |
| 2 | **Advanced Multi-Persona Prompt Engineering** | **🟢 Đã Hoàn Thành** | Xây dựng bộ System Prompts đóng vai chuyên sâu cho các nhân sự ảo: **Agricultural Expert** (Chuyên gia Cây trồng), **Livestock Expert** (Chuyên gia Chăn nuôi & Thú y gia súc), **Second Brain** (Trợ lý Virtual Second Brain). |

| 3 | **Automatic Vault Note Refactoring & Conflict Resolution** | **🟢 Đã Hoàn Thành** | Tích hợp Tool Calling `update_note` trong `hermes_agent.py` & `obsidian_parser.py`. AI Agent tự động phát hiện và thực thi nối/gộp nội dung note cũ mà không làm hỏng YAML Frontmatter. |
| 4 | **Graph RAG Memory Summarization** | **🟢 Đã Hoàn Thành** | Tích hợp Tool Calling `summarize_vault`. Tự động bóc tách tri thức từ tất cả nhật ký nông trại trong Vault và tạo ghi chú tóm tắt tuần/tháng (`00_Nhat_Ky_Trang_Trai/*_Bao_Cao_Tom_Tat_Nong_Trai.md`) liên kết Wiki-links. |

---


## 🌾 5. Kịch bản Demo Nông nghiệp Thông minh Nhật Bản (Japanese Smart Farm)

1. **Giao tiếp & Tư vấn Kỹ thuật Trồng trọt:**
   - **Câu hỏi:** *"Lịch bón phân cho dưa lưới [[Crown_Melon_Shizuoka]] giai đoạn tạo vân lưới như thế nào?"*
   - **Kết quả:** AI Agent dùng **Graph RAG** trích xuất node `Crown_Melon_Shizuoka`, trả lời chính xác quy trình bón phân Kali & giảm 30% tưới nước, đồng thời tự động kích hoạt Tool Call `create_note` lưu nhật ký nông trại vào `00_Nhat_Ky_Trang_Trai/`!

2. **Giao tiếp & Tư vấn Quan hệ Khách hàng Thân thiết (CRM & Gift Suggestion):**
   - **Câu hỏi:** *"Sinh nhật ngài [[Khach_Hang_Kenichi]] nên tặng gì?"*
   - **Kết quả:** AI Agent truy vết node `Khach_Hang_Kenichi`, đọc toàn bộ thuộc tính sở thích (Trà đạo Matcha, chơi Golf, bút máy cổ) và tư vấn 3 món quà tinh tế nhất!

---

## 🚀 6. Hướng dẫn Khởi chạy & Kiểm thử Nhanh

### 1. Khởi chạy bằng Docker:
```bash
docker compose up -d
```
- **Giao diện Swagger UI (Docs):** `http://localhost:8008/docs`
- **Root Status API:** `http://localhost:8008/`

### 2. Chạy Script kiểm thử E2E tự động:
```bash
py scripts/test_demo.py
```
