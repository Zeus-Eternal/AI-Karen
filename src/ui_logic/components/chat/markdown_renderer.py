"""
Kari Markdown Renderer
- Safe, audit-ready markdown rendering for chat
- Prevents injection, sanitizes output
"""

from typing import Union, Dict
from markdown import markdown
from bs4 import BeautifulSoup

def render_safe_markdown(response: Union[str, Dict]) -> str:
    if isinstance(response, str):
        # Remove HTML tags, then render markdown
        clean_text = BeautifulSoup(response, "html.parser").get_text()
        return markdown(clean_text)
    elif isinstance(response, dict) and "content" in response:
        content = BeautifulSoup(response["content"], "html.parser").get_text()
        role = response.get("role", "Kari")
        return f"**{role}:**\n\n{markdown(content)}"
    else:
        # Render as code block for non-string/dict
        return f"```json\n{response}\n```"
