#!/usr/bin/env python3
"""
Automated Link Checking Utility

This script checks all links in README files and other documentation,
validating both internal and external links.
"""

import os
import re
import sys
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class LinkResult:
    """Result of checking a single link"""
    url: str
    status: str  # 'valid', 'broken', 'timeout', 'error'
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None


@dataclass
class FileResult:
    """Result of checking links in a single file"""
    file_path: str
    total_links: int
    valid_links: int
    broken_links: int
    link_results: List[LinkResult]


class LinkChecker:
    """Automated link checker for documentation files"""
    
    def __init__(self, root_path: str = ".", timeout: int = 10, max_workers: int = 10):
        self.root_path = Path(root_path).resolve()
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = self._create_session()
        self.checked_urls = {}  # Cache for external URLs
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent
        session.headers.update({
            'User-Agent': 'Documentation-Link-Checker/1.0'
        })
        
        return session
    
    def extract_links_from_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract all links from a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []
        
        links = []
        
        # Markdown links: [text](url)
        markdown_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        markdown_links = re.findall(markdown_pattern, content)
        for text, url in markdown_links:
            links.append((text.strip(), url.strip()))
        
        # HTML links: <a href="url">text</a>
        html_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        html_links = re.findall(html_pattern, content, re.IGNORECASE)
        for url, text in html_links:
            links.append((text.strip(), url.strip()))
        
        # Direct URLs in text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        direct_urls = re.findall(url_pattern, content)
        for url in direct_urls:
            links.append(("", url))
        
        return links
    
    def check_internal_link(self, url: str, base_path: Path) -> LinkResult:
        """Check an internal (relative) link"""
        start_time = time.time()
        
        # Handle anchor links
        if url.startswith('#'):
            return LinkResult(
                url=url,
                status='valid',
                response_time=time.time() - start_time
            )
        
        # Remove anchor from URL for file checking
        clean_url = url.split('#')[0] if '#' in url else url
        
        if not clean_url:  # Pure anchor link
            return LinkResult(
                url=url,
                status='valid',
                response_time=time.time() - start_time
            )
        
        # Resolve relative path
        if clean_url.startswith('/'):
            # Absolute path from root
            target_path = self.root_path / clean_url.lstrip('/')
        else:
            # Relative path from current file
            target_path = base_path.parent / clean_url
        
        # Normalize path
        try:
            target_path = target_path.resolve()
        except Exception as e:
            return LinkResult(
                url=url,
                status='error',
                error_message=f"Path resolution error: {e}",
                response_time=time.time() - start_time
            )
        
        # Check if file/directory exists
        if target_path.exists():
            return LinkResult(
                url=url,
                status='valid',
                response_time=time.time() - start_time
            )
        else:
            return LinkResult(
                url=url,
                status='broken',
                error_message=f"File not found: {target_path}",
                response_time=time.time() - start_time
            )
    
    def check_external_link(self, url: str) -> LinkResult:
        """Check an external (HTTP/HTTPS) link"""
        start_time = time.time()
        
        # Check cache first
        if url in self.checked_urls:
            cached_result = self.checked_urls[url]
            return LinkResult(
                url=url,
                status=cached_result['status'],
                status_code=cached_result.get('status_code'),
                error_message=cached_result.get('error_message'),
                response_time=time.time() - start_time
            )
        
        try:
            # Use HEAD request first (faster)
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            # Some servers don't support HEAD, try GET
            if response.status_code == 405:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            response_time = time.time() - start_time
            
            if response.status_code < 400:
                result = LinkResult(
                    url=url,
                    status='valid',
                    status_code=response.status_code,
                    response_time=response_time
                )
                status = 'valid'
            else:
                result = LinkResult(
                    url=url,
                    status='broken',
                    status_code=response.status_code,
                    error_message=f"HTTP {response.status_code}",
                    response_time=response_time
                )
                status = 'broken'
            
            # Cache result
            self.checked_urls[url] = {
                'status': status,
                'status_code': response.status_code,
                'error_message': result.error_message
            }
            
            return result
            
        except requests.exceptions.Timeout:
            result = LinkResult(
                url=url,
                status='timeout',
                error_message="Request timeout",
                response_time=time.time() - start_time
            )
            self.checked_urls[url] = {'status': 'timeout', 'error_message': 'Request timeout'}
            return result
            
        except requests.exceptions.RequestException as e:
            result = LinkResult(
                url=url,
                status='error',
                error_message=str(e),
                response_time=time.time() - start_time
            )
            self.checked_urls[url] = {'status': 'error', 'error_message': str(e)}
            return result
    
    def check_link(self, url: str, base_path: Path) -> LinkResult:
        """Check a single link (internal or external)"""
        # Skip certain URLs
        skip_patterns = [
            'mailto:',
            'javascript:',
            'data:',
            'tel:',
            'ftp:',
        ]
        
        for pattern in skip_patterns:
            if url.startswith(pattern):
                return LinkResult(
                    url=url,
                    status='valid',
                    error_message="Skipped (non-HTTP protocol)"
                )
        
        # Determine if link is internal or external
        if url.startswith(('http://', 'https://')):
            return self.check_external_link(url)
        else:
            return self.check_internal_link(url, base_path)
    
    def check_file_links(self, file_path: Path) -> FileResult:
        """Check all links in a single file"""
        links = self.extract_links_from_file(file_path)
        
        if not links:
            return FileResult(
                file_path=str(file_path),
                total_links=0,
                valid_links=0,
                broken_links=0,
                link_results=[]
            )
        
        # Check links with threading for external URLs
        link_results = []
        external_links = []
        internal_links = []
        
        for text, url in links:
            if url.startswith(('http://', 'https://')):
                external_links.append(url)
            else:
                internal_links.append(url)
        
        # Check internal links (fast, no threading needed)
        for url in internal_links:
            result = self.check_link(url, file_path)
            link_results.append(result)
        
        # Check external links with threading
        if external_links:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {
                    executor.submit(self.check_external_link, url): url 
                    for url in external_links
                }
                
                for future in concurrent.futures.as_completed(future_to_url):
                    result = future.result()
                    link_results.append(result)
        
        # Calculate statistics
        valid_count = sum(1 for r in link_results if r.status == 'valid')
        broken_count = sum(1 for r in link_results if r.status in ['broken', 'error', 'timeout'])
        
        return FileResult(
            file_path=str(file_path),
            total_links=len(link_results),
            valid_links=valid_count,
            broken_links=broken_count,
            link_results=link_results
        )
    
    def check_all_documentation(self, file_patterns: List[str] = None) -> List[FileResult]:
        """Check links in all documentation files"""
        if file_patterns is None:
            file_patterns = ["**/*.md", "**/*.rst", "**/*.txt"]
        
        files_to_check = []
        for pattern in file_patterns:
            files_to_check.extend(self.root_path.glob(pattern))
        
        # Remove duplicates and sort
        files_to_check = sorted(set(files_to_check))
        
        results = []
        for file_path in files_to_check:
            if file_path.is_file():
                print(f"Checking links in: {file_path.relative_to(self.root_path)}")
                result = self.check_file_links(file_path)
                results.append(result)
        
        return results


def main():
    """Main entry point for link checking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check links in documentation files")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--workers", type=int, default=10, help="Number of worker threads")
    parser.add_argument("--files", nargs="+", help="Specific files to check")
    parser.add_argument("--external-only", action="store_true", help="Check only external links")
    parser.add_argument("--internal-only", action="store_true", help="Check only internal links")
    
    args = parser.parse_args()
    
    checker = LinkChecker(timeout=args.timeout, max_workers=args.workers)
    
    if args.files:
        # Check specific files
        results = []
        for file_path in args.files:
            path = Path(file_path)
            if path.exists():
                result = checker.check_file_links(path)
                results.append(result)
            else:
                print(f"Warning: File not found: {file_path}")
    else:
        # Check all documentation
        results = checker.check_all_documentation()
    
    # Display results
    print("\n=== LINK CHECKING RESULTS ===\n")
    
    total_files = len(results)
    total_links = sum(r.total_links for r in results)
    total_valid = sum(r.valid_links for r in results)
    total_broken = sum(r.broken_links for r in results)
    
    for result in results:
        if result.total_links == 0:
            continue
            
        rel_path = Path(result.file_path).relative_to(Path.cwd())
        print(f"📄 {rel_path}")
        print(f"   Links: {result.total_links} total, {result.valid_links} valid, {result.broken_links} broken")
        
        # Show broken links
        broken_links = [r for r in result.link_results if r.status in ['broken', 'error', 'timeout']]
        if broken_links:
            for link in broken_links:
                status_icon = "❌" if link.status == 'broken' else "⚠️"
                print(f"   {status_icon} {link.url} - {link.error_message or link.status}")
        
        print()
    
    print("=== SUMMARY ===")
    print(f"Files checked: {total_files}")
    print(f"Total links: {total_links}")
    print(f"Valid links: {total_valid}")
    print(f"Broken links: {total_broken}")
    
    if total_broken > 0:
        print(f"\n❌ Found {total_broken} broken links")
        sys.exit(1)
    else:
        print(f"\n✅ All {total_links} links are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()