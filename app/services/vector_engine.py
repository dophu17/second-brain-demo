import chromadb
from typing import List, Dict, Any
from pathlib import Path
from app.config import settings
from app.services.obsidian_parser import obsidian_parser

class VectorStoreEngine:
    def __init__(self):
        # Khởi tạo Persistent Client lưu vector DB trong /tmp/chroma_db hoặc in-memory
        try:
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(name="smart_farm_vault")
        except Exception as e:
            print(f"ChromaDB Init Warning: {e}")
            self.client = None
            self.collection = None

    def index_vault(self):
        """Đánh chỉ mục toàn bộ các ghi chú trong Vault vào Vector Database."""
        if not self.collection:
            return
        
        notes = obsidian_parser.read_all_notes()
        if not notes:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for idx, note in enumerate(notes):
            documents.append(f"Title: {note.title}\nCategory: {note.metadata.category}\nContent: {note.content}")
            metadatas.append({
                "title": note.title,
                "relative_path": note.relative_path,
                "author": note.metadata.author or "Farm AI"
            })
            ids.append(f"doc_{idx}_{Path(note.relative_path).stem}")
            
        try:
            # Re-create collection để làm mới chỉ mục
            try:
                self.client.delete_collection("smart_farm_vault")
            except Exception:
                pass
            self.collection = self.client.create_collection(name="smart_farm_vault")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Error indexing ChromaDB: {e}")

    def vector_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Tìm kiếm ngữ nghĩa (Semantic Vector Search) qua ChromaDB."""
        self.index_vault()
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count() or 1)
            )
            
            output = []
            if results and "metadatas" in results and results["metadatas"]:
                for meta_list, doc_list in zip(results["metadatas"], results["documents"]):
                    for meta, doc in zip(meta_list, doc_list):
                        output.append({
                            "title": meta.get("title", ""),
                            "relative_path": meta.get("relative_path", ""),
                            "snippet": doc[:300]
                        })
            return output
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

vector_engine = VectorStoreEngine()
