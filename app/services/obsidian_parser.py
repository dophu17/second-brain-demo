import re
import os
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
        # Loại bỏ alias trong link (ví dụ [[Note_Name|Display Name]] -> Note_Name)
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
        target_dir = self.vault_path / req.folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Đảm bảo tên file an toàn
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", req.title)
        file_path = target_dir / f"{safe_title}.md"
        
        post = frontmatter.Post(req.content)
        post["title"] = req.title
        post["tags"] = req.tags
        post["author"] = req.author
        
        import datetime
        post["date"] = datetime.date.today().isoformat()
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
            
        return self.parse_file(file_path)

    def update_note(self, relative_path: str, content_append: Optional[str] = None, tags_add: Optional[List[str]] = None) -> Optional[NoteItem]:
        """Chỉnh sửa / nối thêm nội dung hoặc bổ sung tags vào file Markdown cũ."""
        file_path = self.vault_path / relative_path
        if not file_path.exists():
            return None
            
        post = frontmatter.load(file_path)
        if content_append:
            post.content = post.content.rstrip() + f"\n\n---\n*Cập nhật:* {content_append}\n"
            
        if tags_add:
            existing_tags = post.get("tags", [])
            if isinstance(existing_tags, str):
                existing_tags = [existing_tags]
            combined = list(set(existing_tags + tags_add))
            post["tags"] = combined
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
            
        return self.parse_file(file_path)

obsidian_parser = ObsidianParser()
