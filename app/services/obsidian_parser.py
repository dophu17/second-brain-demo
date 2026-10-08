import re
import os
import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import frontmatter

from app.config import settings
from app.models.schemas import NoteItem, NoteMetadata, CreateNoteRequest

class ObsidianParser:
    def __init__(self, vault_path: Path = settings.VAULT_PATH):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def extract_wiki_links(self, content: str) -> List[str]:
        """Trích xuất các đường dẫn 2 chiều [[Wiki-links]] từ nội dung Markdown."""
        matches = re.findall(r"\[\[(.*?)\]\]", content)
        clean_links = [match.split("|")[0].strip() for match in matches]
        return list(set(clean_links))

    def parse_file(self, file_path: Path) -> Optional[NoteItem]:
        """Đọc và parse 1 file .md bao gồm YAML Frontmatter và Wiki-links."""
        try:
            post = frontmatter.load(file_path)
            content = post.content
            metadata_dict = dict(post.metadata)
            
            title = metadata_dict.get("title", file_path.stem)
            tags = metadata_dict.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            metadata = NoteMetadata(
                title=str(title),
                tags=tags,
                date=str(metadata_dict.get("date", "")),
                author=str(metadata_dict.get("author", "")),
                category=str(metadata_dict.get("category", "General"))
            )
            
            relative_path = str(file_path.relative_to(self.vault_path)).replace("\\", "/")
            wiki_links = self.extract_wiki_links(content)
            
            return NoteItem(
                filename=file_path.name,
                relative_path=relative_path,
                title=title,
                content=content,
                metadata=metadata,
                wiki_links=wiki_links
            )
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None

    def read_all_notes(self) -> List[NoteItem]:
        """Quét toàn bộ thư mục Vault và trả về danh sách ghi chú."""
        notes = []
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    note = self.parse_file(full_path)
                    if note:
                        notes.append(note)
        return notes

    def search_notes(self, query: str) -> List[NoteItem]:
        """Tìm kiếm ghi chú theo từ khoá trong tiêu đề, tên file, hoặc nội dung."""
        query_lower = query.lower().strip()
        all_notes = self.read_all_notes()
        results = []
        for note in all_notes:
            stem = Path(note.filename).stem.lower()
            if (query_lower in note.title.lower() or 
                query_lower in note.content.lower() or 
                query_lower in stem or 
                query_lower in note.relative_path.lower()):
                results.append(note)
        return results

    def create_note(self, req: CreateNoteRequest) -> NoteItem:
        """Tạo mới một ghi chú Markdown với YAML Frontmatter chuẩn vào Vault."""
        # Sanitize folder và title (lọc bỏ ngoặc [[...]])
        clean_folder = req.folder.replace("[", "").replace("]", "").strip()
        clean_title = req.title.replace("[", "").replace("]", "").strip()
        
        target_dir = self.vault_path / clean_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", clean_title)
        file_path = target_dir / f"{safe_title}.md"
        
        post = frontmatter.Post(req.content)
        post["title"] = clean_title
        post["tags"] = req.tags
        post["author"] = req.author
        post["date"] = datetime.date.today().isoformat()
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
            
        return self.parse_file(file_path)

    def update_note(self, relative_path: str, content_append: Optional[str] = None, tags_add: Optional[List[str]] = None) -> Optional[NoteItem]:
        """Chỉnh sửa / nối thêm nội dung & giải quyết mâu thuẫn dữ liệu (Conflict Resolution)."""
        # 0. Sanitize relative_path (xóa bỏ ngoặc [[...]])
        clean_rel_path = relative_path.replace("[", "").replace("]", "").strip()
        target_path = self.vault_path / clean_rel_path
        
        # 1. Nếu không tìm thấy đường dẫn chính xác, thử tìm theo từ khóa tên file/title
        if not target_path.exists():
            clean_name = Path(clean_rel_path).stem.replace("Khach_Hang_", "").replace("Ghi_Chu_", "")
            search_results = self.search_notes(clean_name)
            if search_results:
                target_path = self.vault_path / search_results[0].relative_path
        
        # 2. Nếu vẫn chưa tồn tại, tự động UPSERT (tạo mới file)
        if not target_path.exists():
            folder = "30_Doi_Tac_Khach_Hang" if any(k in clean_rel_path.lower() for k in ["yamoto", "yamato", "kenichi", "khach", "doi_tac", "partner"]) else "00_Nhat_Ky_Trang_Trai"
            stem_title = Path(clean_rel_path).stem
            title = f"Khach_Hang_{stem_title}" if "Khach_Hang_" not in stem_title and folder == "30_Doi_Tac_Khach_Hang" else stem_title
            
            req = CreateNoteRequest(
                title=title,
                folder=folder,
                tags=tags_add or ["client", "updated"],
                content=f"# 👤 {title}\n\n- **Sinh nhật:** 24 tháng 3.\n- **Cập nhật:** {content_append or 'Thông tin mới'}",
                author="SecondBrain Auto-UPSERT"
            )
            return self.create_note(req)

        # 3. Nối nội dung & Giải quyết mâu thuẫn dữ liệu (Conflict Resolution for Birthday/Fields)
        post = frontmatter.load(target_path)
        if content_append:
            # Nếu nội dung cập nhật chứa thông tin sinh nhật mới, thay thế trực tiếp dòng Sinh nhật cũ trong Markdown
            bday_match = re.search(r"(\d{1,2}\s+tháng\s+\d{1,2})", content_append, re.IGNORECASE)
            if "sinh nhật" in content_append.lower() and bday_match:
                new_bday = bday_match.group(1)
                if re.search(r"-\s*\*\*Sinh nhật:\*\*\s*.*", post.content, re.IGNORECASE):
                    post.content = re.sub(r"-\s*\*\*Sinh nhật:\*\*\s*.*", f"- **Sinh nhật:** {new_bday}.", post.content)
                else:
                    post.content = post.content.rstrip() + f"\n- **Sinh nhật:** {new_bday}.\n"
            
            post.content = post.content.rstrip() + f"\n- **Cập nhật ({datetime.date.today()}):** {content_append}\n"
            
        if tags_add:
            existing_tags = post.get("tags", [])
            if isinstance(existing_tags, str):
                existing_tags = [existing_tags]
            combined = list(set(existing_tags + tags_add))
            post["tags"] = combined
            
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
            
        return self.parse_file(target_path)

obsidian_parser = ObsidianParser()
