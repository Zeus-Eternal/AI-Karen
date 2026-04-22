import re


CODE_BLOCK_RE = re.compile(r"```([\w+-]*)\n?(.*?)```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
BULLET_RE = re.compile(r"^\s*[-*]\s+.+$", re.MULTILINE)
NUMBERED_RE = re.compile(r"^\s*\d+\.\s+.+$", re.MULTILINE)
TABLE_RE = re.compile(r"^\|.+\|\s*$", re.MULTILINE)