"""
Kari Memory Page
- Orchestrates: knowledge graph, session explorer, profile, analytics
"""

from components.memory.knowledge_graph import render_knowledge_graph
from components.memory.session_explorer import render_session_explorer
from components.memory.profile_panel import render_profile_panel
from components.memory.memory_analytics import render_memory_analytics

def memory_page(user_ctx=None):
    render_session_explorer(user_ctx=user_ctx)
    render_profile_panel(user_ctx=user_ctx)
    render_knowledge_graph(user_ctx=user_ctx)
    render_memory_analytics(user_ctx=user_ctx)
