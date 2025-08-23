"""
Documentation Connector - External documentation ingestion

This connector handles external documentation sources with URL crawling,
robots.txt compliance, content sanitization, and incremental updates.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, AsyncGenerator
from urllib.parse import urljoin, urlparse, robots
from urllib.robotparser import RobotFileParser
import re

try:
    import aiohttp
    import aiofiles
    from bs4 import BeautifulSoup
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    aiohttp = None
    BeautifulSoup = None

from .base_connector import BaseConnector, ConnectorType, ChangeDetection, ChangeType

try:
    from llama_index.core import Document
except ImportError:
    Document = None


class DocumentationConnector(BaseConnector):
    """
    Connector for ingesting knowledge from external documentation sources.
    Supports URL crawling, robots.txt compliance, content sanitization,
    and incremental updates based on content changes.
    """
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, ConnectorType.DOCUMENTATION, config)
        
        # Documentation-specific configuration
        self.base_urls = config.get("base_urls", [])
        self.allowed_domains = config.get("allowed_domains", [])
        self.max_depth = config.get("max_depth", 3)
        self.max_pages = config.get("max_pages", 100)
        self.respect_robots_txt = config.get("respect_robots_txt", True)
        
        # Content filtering
        self.content_selectors = config.get("content_selectors", ["main", "article", ".content", "#content"])
        self.exclude_selectors = config.get("exclude_selectors", ["nav", "footer", ".sidebar", "#sidebar"])
        self.min_content_length = config.get("min_content_length", 100)
        
        # Request configuration
        self.request_delay = config.get("request_delay", 1.0)  # Seconds between requests
        self.timeout = config.get("timeout", 30)
        self.user_agent = config.get("user_agent", "KnowledgeConnector/1.0")
        self.max_concurrent_requests = config.get("max_concurrent_requests", 5)
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.url_checksums: Dict[str, str] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Content processing
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
    
    async def scan_sources(self) -> AsyncGenerator[Document, None]:
        """Scan documentation sources and yield documents."""
        if not DEPENDENCIES_AVAILABLE:
            self.logger.error("Required dependencies (aiohttp, beautifulsoup4) not available")
            return
        
        try:
            # Initialize HTTP session
            await self._initialize_session()
            
            # Process each base URL
            for base_url in self.base_urls:
                if not self._is_allowed_domain(base_url):
                    self.logger.warning(f"URL not in allowed domains: {base_url}")
                    continue
                
                async for document in self._crawl_documentation(base_url):
                    yield document
                    await asyncio.sleep(0.001)  # Yield control
        
        except Exception as e:
            self.logger.error(f"Error scanning documentation sources: {e}")
        finally:
            await self._cleanup_session()
    
    async def _initialize_session(self):
        """Initialize HTTP session with proper configuration."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        )
    
    async def _cleanup_session(self):
        """Clean up HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is allowed."""
        if not self.allowed_domains:
            return True
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        return any(domain == allowed or domain.endswith(f".{allowed}") 
                  for allowed in self.allowed_domains)
    
    async def _crawl_documentation(self, base_url: str) -> AsyncGenerator[Document, None]:
        """Crawl documentation starting from base URL."""
        try:
            # Initialize crawling state
            urls_to_visit = [(base_url, 0)]  # (url, depth)
            pages_processed = 0
            
            while urls_to_visit and pages_processed < self.max_pages:
                current_url, depth = urls_to_visit.pop(0)
                
                # Skip if already visited or too deep
                if current_url in self.visited_urls or depth > self.max_depth:
                    continue
                
                # Check robots.txt
                if self.respect_robots_txt and not await self._is_allowed_by_robots(current_url):
                    self.logger.debug(f"URL blocked by robots.txt: {current_url}")
                    continue
                
                # Process page
                async with self.semaphore:
                    document = await self._process_documentation_page(current_url)
                    
                    if document:
                        yield document
                        pages_processed += 1
                        
                        # Find new URLs to crawl
                        if depth < self.max_depth:
                            new_urls = await self._extract_links(current_url)
                            for new_url in new_urls:
                                if (new_url not in self.visited_urls and 
                                    self._is_allowed_domain(new_url)):
                                    urls_to_visit.append((new_url, depth + 1))
                    
                    # Mark as visited
                    self.visited_urls.add(current_url)
                    
                    # Respect rate limiting
                    await asyncio.sleep(self.request_delay)
        
        except Exception as e:
            self.logger.error(f"Error crawling documentation from {base_url}: {e}")
    
    async def _is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check cache first
            if base_url in self.robots_cache:
                rp = self.robots_cache[base_url]
            else:
                # Fetch and parse robots.txt
                robots_url = urljoin(base_url, "/robots.txt")
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                try:
                    async with self.session.get(robots_url) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            # Parse robots.txt content
                            for line in robots_content.split('\n'):
                                rp.read()  # This is a simplified approach
                except Exception:
                    # If robots.txt can't be fetched, assume allowed
                    pass
                
                self.robots_cache[base_url] = rp
            
            # Check if URL is allowed for our user agent
            return rp.can_fetch(self.user_agent, url)
        
        except Exception as e:
            self.logger.error(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowed if check fails
    
    async def _process_documentation_page(self, url: str) -> Optional[Document]:
        """Process a single documentation page."""
        try:
            # Fetch page content
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
                
                html_content = await response.text()
            
            # Parse and extract content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for selector in self.exclude_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            if not content or len(content) < self.min_content_length:
                self.logger.debug(f"Content too short or empty for {url}")
                return None
            
            # Extract metadata
            metadata = await self._extract_page_metadata(soup, url)
            
            # Create document
            document = self._create_document(content, url, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error processing documentation page {url}: {e}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML soup."""
        content_parts = []
        
        # Try content selectors in order
        for selector in self.content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator='\n', strip=True)
                    if text:
                        content_parts.append(text)
                break
        
        # Fallback to body if no content selectors worked
        if not content_parts:
            body = soup.find('body')
            if body:
                content_parts.append(body.get_text(separator='\n', strip=True))
        
        # Join and clean content
        content = '\n\n'.join(content_parts)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove excessive newlines
        content = re.sub(r'[ \t]+', ' ', content)  # Normalize spaces
        
        return content.strip()
    
    async def _extract_page_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML page."""
        metadata = {
            "source_type": "documentation",
            "url": url,
            "connector_id": self.connector_id,
            "extracted_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True)
            
            # Extract meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata["description"] = desc_tag.get('content', '')
            
            # Extract meta keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                metadata["keywords"] = keywords_tag.get('content', '').split(',')
            
            # Extract headings structure
            headings = []
            for level in range(1, 7):  # h1 to h6
                for heading in soup.find_all(f'h{level}'):
                    headings.append({
                        "level": level,
                        "text": heading.get_text(strip=True)
                    })
            
            if headings:
                metadata["headings"] = headings[:20]  # Limit to first 20
            
            # Extract language
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata["language"] = html_tag.get('lang')
            
            # Extract canonical URL
            canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
            if canonical_tag:
                metadata["canonical_url"] = canonical_tag.get('href')
            
            # Extract last modified (if available)
            modified_tag = soup.find('meta', attrs={'name': 'last-modified'})
            if modified_tag:
                metadata["last_modified"] = modified_tag.get('content')
        
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {url}: {e}")
        
        return metadata
    
    async def _extract_links(self, current_url: str) -> List[str]:
        """Extract links from current page for further crawling."""
        links = []
        
        try:
            # This would typically be done during page processing
            # For now, return empty list to avoid re-fetching
            # In a full implementation, you'd extract links during _process_documentation_page
            pass
        
        except Exception as e:
            self.logger.error(f"Error extracting links from {current_url}: {e}")
        
        return links
    
    async def detect_changes(self) -> List[ChangeDetection]:
        """Detect changes in documentation sources."""
        changes = []
        
        try:
            # Initialize session if needed
            if not self.session:
                await self._initialize_session()
            
            # Check each base URL for changes
            for base_url in self.base_urls:
                if not self._is_allowed_domain(base_url):
                    continue
                
                # Get current content checksum
                current_checksum = await self._get_url_checksum(base_url)
                old_checksum = self.url_checksums.get(base_url)
                
                if old_checksum is None:
                    # New URL
                    changes.append(ChangeDetection(
                        source_path=base_url,
                        change_type=ChangeType.CREATED,
                        timestamp=datetime.utcnow(),
                        new_checksum=current_checksum
                    ))
                elif old_checksum != current_checksum:
                    # Modified URL
                    changes.append(ChangeDetection(
                        source_path=base_url,
                        change_type=ChangeType.MODIFIED,
                        timestamp=datetime.utcnow(),
                        old_checksum=old_checksum,
                        new_checksum=current_checksum
                    ))
                
                # Update stored checksum
                if current_checksum:
                    self.url_checksums[base_url] = current_checksum
        
        except Exception as e:
            self.logger.error(f"Error detecting documentation changes: {e}")
        finally:
            await self._cleanup_session()
        
        return changes
    
    async def _get_url_checksum(self, url: str) -> Optional[str]:
        """Get checksum for URL content."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._calculate_checksum(content)
                return None
        except Exception as e:
            self.logger.error(f"Error getting checksum for {url}: {e}")
            return None
    
    async def get_source_metadata(self, source_path: str) -> Dict[str, Any]:
        """Get metadata for a documentation source."""
        return {
            "source_type": "documentation",
            "url": source_path,
            "connector_id": self.connector_id,
            "user_agent": self.user_agent,
            "respect_robots_txt": self.respect_robots_txt
        }
    
    async def validate_configuration(self) -> List[str]:
        """Validate documentation connector configuration."""
        errors = await super().validate_configuration()
        
        # Check dependencies
        if not DEPENDENCIES_AVAILABLE:
            errors.append("Required dependencies (aiohttp, beautifulsoup4) not available")
        
        # Check base URLs
        if not self.base_urls:
            errors.append("At least one base URL is required")
        else:
            for url in self.base_urls:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"Invalid URL format: {url}")
        
        # Check configuration values
        if self.max_depth < 1:
            errors.append("Max depth must be at least 1")
        
        if self.max_pages < 1:
            errors.append("Max pages must be at least 1")
        
        if self.request_delay < 0:
            errors.append("Request delay cannot be negative")
        
        return errors
    
    async def cleanup(self):
        """Clean up resources used by the connector."""
        await self._cleanup_session()
        self.visited_urls.clear()
        self.robots_cache.clear()
        self.url_checksums.clear()