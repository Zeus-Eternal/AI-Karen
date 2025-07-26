from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List


class MarketplaceClient:
    """Simple marketplace interface for extension downloads."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or "https://example.com"
        self.logger = logging.getLogger("extension.marketplace")

    async def list_available_extensions(self) -> List[Dict[str, Any]]:
        """List available extensions from the marketplace."""
        self.logger.info("Listing extensions from marketplace")
        return []

    async def download_extension(
        self, extension_id: str, version: str, destination: Path
    ) -> bool:
        """Download an extension to the given destination."""
        self.logger.info(
            "Downloading %s@%s from %s", extension_id, version, self.base_url
        )
        # Placeholder implementation
        return False

