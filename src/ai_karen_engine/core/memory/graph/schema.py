"""Schema constants for LeanGraph relationship layer."""

NODE_TYPES = ["MemoryEvent", "Entity", "Assertion", "User", "Tenant", "Conversation"]
EDGE_TYPES = [
    "BELONGS_TO_TENANT",
    "BELONGS_TO_USER",
    "OCCURRED_IN_CONVERSATION",
    "MENTIONS",
    "ASSERTS",
    "SUPPORTED_BY",
    "CONTRADICTS",
    "REINFORCES",
    "SUPERSEDES",
    "RELATED_TO",
]
