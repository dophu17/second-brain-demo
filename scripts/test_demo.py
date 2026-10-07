import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.services.obsidian_parser import obsidian_parser
from app.services.graph_engine import graph_engine
from app.services.hermes_agent import hermes_agent_service

def run_e2e_demo():
    print("=" * 75)
    print("🌾 BẮT ĐẦU CHẠY DEMO BỘ NÃO THỨ 2 QUẢN LÝ TRANG TRẠI NÔNG NGHIỆP NHẬT BẢN")
    print("=" * 75)

    # 1. Quét ghi chú ban đầu trong Vault
    print("\n📂 1. Danh mục Quản lý Trang trại trong Obsidian Vault:")
    notes = obsidian_parser.read_all_notes()
    for note in notes:
        print(f"   • [{note.relative_path}] {note.title} (Tags: {note.metadata.tags}, Wiki-links: {note.wiki_links})")

    # 2. Xây dựng Đồ thị tri thức (Knowledge Graph)
    print("\n🕸️ 2. Thống kê Đồ thị Tri thức Nông nghiệp (NetworkX Graph Engine):")
    summary = graph_engine.get_graph_summary()
    print(f"   • Tổng số Nodes: {summary['total_nodes']}")
    print(f"   • Tổng số Edges (Wiki-links): {summary['total_edges']}")
    print(f"   • Top Notes được kết nối nhiều nhất: {summary['top_connected_notes']}")

    # 3. Thử nghiệm gửi Input kỹ thuật nông nghiệp
    user_prompt = "Lịch bón phân cho dưa lưới [[Crown_Melon_Shizuoka]] giai đoạn tạo vân lưới như thế nào?"
    print(f"\n💬 3. Người dùng hỏi Trợ lý Trang trại AI:")
    print(f"   User: \"{user_prompt}\"")

    # 4. Hermes Agent xử lý & Thực thi Tool Calling
    print("\n🤖 4. Hermes Agent xử lý & Thực thi Tool Calling:")
    response = hermes_agent_service.process_chat(user_prompt, persona="CEO")
    
    print(f"   • Trả lời từ AI:\n{response.reply}")
    print(f"   • Tool calls đã thực thi: {response.tool_calls_executed}")
    print(f"   • Ngữ cảnh Đồ thị trích xuất được: {response.graph_context}")

    # 5. Kiểm tra lại Obsidian Vault
    print("\n💾 5. Kiểm tra lại Obsidian Vault sau khi AI tự động cập nhật nhật ký:")
    updated_notes = obsidian_parser.read_all_notes()
    for note in updated_notes:
        print(f"   • [{note.relative_path}] {note.title} (Wiki-links: {note.wiki_links})")

    # 6. Kiểm tra Backlinks của khách hàng Kenichi
    backlinks_kenichi = graph_engine.get_backlinks("Khach_Hang_Kenichi")
    print(f"\n🔗 6. Danh sách Backlinks liên kết tới [[Khach_Hang_Kenichi]]: {backlinks_kenichi}")

    print("\n" + "=" * 75)
    print("✅ DEMO NÔNG NGHIỆP NHẬT BẢN HOÀN THÀNH TỐT ĐẸP!")
    print("=" * 75)

if __name__ == "__main__":
    run_e2e_demo()
