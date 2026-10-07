import networkx as nx
from typing import Dict, List, Any
from app.services.obsidian_parser import obsidian_parser

class KnowledgeGraphEngine:
    def __init__ (self):
        self.graph = nx.DiGraph()

    def build_graph(self) -> nx.DiGraph:
        """Xây dựng Đồ thị Tri thức từ toàn bộ các ghi chú trong Vault."""
        self.graph.clear()
        notes = obsidian_parser.read_all_notes()
        
        from pathlib import Path
        # Thêm tất cả các Node (dùng cả filename stem lẫn title để khớp [[Wiki-links]])
        for note in notes:
            stem = Path(note.filename).stem.strip()
            title = note.title.strip()
            node_id = stem if stem else title
            self.graph.add_node(
                node_id,
                title=title,
                path=note.relative_path,
                tags=note.metadata.tags,
                author=note.metadata.author
            )
            
        # Thêm các cạnh Edges (Wiki-links)
        for note in notes:
            stem = Path(note.filename).stem.strip()
            title = note.title.strip()
            source_id = stem if stem else title
            for target_link in note.wiki_links:
                target_id = target_link.strip()
                if not self.graph.has_node(target_id):
                    self.graph.add_node(target_id, path="", tags=[], author="Unknown")
                self.graph.add_edge(source_id, target_id)
                
        return self.graph

    def get_backlinks(self, note_title: str) -> List[str]:
        """Lấy danh sách các note trỏ tới (incoming links) note này."""
        self.build_graph()
        if not self.graph.has_node(note_title):
            return []
        in_edges = self.graph.in_edges(note_title)
        return [source for source, _ in in_edges]

    def get_related_context(self, note_title: str, max_depth: int = 1) -> List[str]:
        """Lấy danh sách các tri thức liên quan trực tiếp và gián tiếp (Graph Context)."""
        self.build_graph()
        if not self.graph.has_node(note_title):
            return []
            
        context_nodes = set()
        context_nodes.add(note_title)
        
        # Lấy neighbors cả chiều ra và vào
        successors = list(self.graph.successors(note_title))
        predecessors = list(self.graph.predecessors(note_title))
        
        context_nodes.update(successors)
        context_nodes.update(predecessors)
        
        return list(context_nodes)

    def get_graph_summary(self) -> Dict[str, Any]:
        """Thống kê tổng quan số lượng Nodes, Edges và Top Backlinks."""
        self.build_graph()
        degree_dict = dict(self.graph.in_degree())
        top_backlinks = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "top_connected_notes": [{"note": k, "incoming_links": v} for k, v in top_backlinks]
        }

graph_engine = KnowledgeGraphEngine()
