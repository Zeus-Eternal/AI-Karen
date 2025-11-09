"""
SearxNG Plugin for AI-Karen
Prompt-first privacy-respecting search plugin with Docker management
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import aiohttp

logger = logging.getLogger(__name__)

class SearxNGPlugin:
    """
    SearxNG search plugin with integrated Docker management
    
    Features:
    - Privacy-respecting search
    - Docker container management
    - Configurable search engines
    - Rate limiting and security
    - Multiple output formats
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'http://localhost:8080')
        self.timeout = self.config.get('timeout', 10)
        self.auto_deploy = self.config.get('auto_deploy', True)
        self.docker_compose_path = self.config.get('docker_compose_path')
        
        # Plugin directory
        self.plugin_dir = Path(__file__).parent
        self.docker_dir = self.plugin_dir / 'docker'
        
        # Deployment status
        self._is_deployed = False
        self._health_checked = False
    
    async def initialize(self) -> None:
        """Initialize the SearxNG plugin"""
        try:
            # Check if already running
            if await self._check_health():
                self._is_deployed = True
                logger.info("SearxNG already running and healthy")
                return
            
            # Auto-deploy if enabled
            if self.auto_deploy:
                await self.deploy()
            
            logger.info("SearxNG plugin initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize SearxNG plugin: {e}")
            raise
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        category: str = "general",
        language: str = "en",
        time_range: Optional[str] = None,
        safe_search: int = 1,
        format: str = "json"
    ) -> List[Dict[str, Any]]:
        """
        Perform search using SearxNG
        
        Args:
            query: Search query
            num_results: Number of results (max 50)
            category: Search category
            language: Language code
            time_range: Time filter
            safe_search: Safe search level (0-2)
            format: Output format (json, html, csv, rss)
            
        Returns:
            List of search results
        """
        if not await self._ensure_running():
            raise RuntimeError("SearxNG is not available")
        
        try:
            params = {
                'q': query,
                'format': format,
                'categories': category,
                'language': language,
                'safesearch': safe_search
            }
            
            if time_range:
                params['time_range'] = time_range
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Search failed with status {response.status}")
                    
                    if format == "json":
                        data = await response.json()
                        results = data.get('results', [])[:num_results]
                        return self._process_results(results)
                    else:
                        return await response.text()
                        
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise Exception(f"Search failed: {str(e)}")
    
    def _process_results(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and normalize search results"""
        processed = []
        for i, result in enumerate(raw_results):
            processed_result = {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'content': result.get('content', ''),
                'engine': result.get('engine', ''),
                'category': result.get('category', ''),
                'score': result.get('score', 0),
                'position': i + 1
            }
            
            # Add optional fields
            for field in ['publishedDate', 'img_src', 'thumbnail']:
                if field in result:
                    processed_result[field] = result[field]
            
            processed.append(processed_result)
        
        return processed
    
    async def deploy(self) -> bool:
        """Deploy SearxNG using Docker Compose"""
        try:
            # Ensure Docker files exist
            await self._setup_docker_files()
            
            # Deploy using docker-compose
            cmd = ['docker-compose', 'up', '-d']
            if self.docker_compose_path:
                cmd.extend(['-f', self.docker_compose_path])
            else:
                cmd.extend(['-f', str(self.docker_dir / 'docker-compose.yml')])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.docker_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Docker deployment failed: {error_msg}")
            
            # Wait for service to be ready
            await self._wait_for_ready()
            
            self._is_deployed = True
            logger.info("SearxNG deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
    
    async def stop(self) -> bool:
        """Stop SearxNG containers"""
        try:
            cmd = ['docker-compose', 'down']
            if self.docker_compose_path:
                cmd.extend(['-f', self.docker_compose_path])
            else:
                cmd.extend(['-f', str(self.docker_dir / 'docker-compose.yml')])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.docker_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            self._is_deployed = False
            logger.info("SearxNG stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop SearxNG: {e}")
            return False
    
    async def _check_health(self) -> bool:
        """Check if SearxNG is healthy"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/healthz") as response:
                    return response.status == 200
        except:
            return False
    
    async def _ensure_running(self) -> bool:
        """Ensure SearxNG is running"""
        if await self._check_health():
            return True
        
        if self.auto_deploy and not self._is_deployed:
            await self.deploy()
            return await self._check_health()
        
        return False
    
    async def _wait_for_ready(self, max_wait: int = 60) -> None:
        """Wait for SearxNG to be ready"""
        for _ in range(max_wait):
            if await self._check_health():
                return
            await asyncio.sleep(1)
        
        raise TimeoutError("SearxNG did not become ready within timeout")
    
    async def _setup_docker_files(self) -> None:
        """Setup Docker configuration files"""
        self.docker_dir.mkdir(parents=True, exist_ok=True)
        
        # Create docker-compose.yml
        docker_compose = {
            'version': '3.7',
            'services': {
                'redis': {
                    'container_name': 'searxng-redis',
                    'image': 'docker.io/valkey/valkey:8-alpine',
                    'command': 'valkey-server --save 30 1 --loglevel warning',
                    'restart': 'unless-stopped',
                    'networks': ['searxng'],
                    'volumes': ['valkey-data:/data'],
                    'cap_drop': ['ALL'],
                    'cap_add': ['SETGID', 'SETUID', 'DAC_OVERRIDE'],
                    'logging': {
                        'driver': 'json-file',
                        'options': {'max-size': '1m', 'max-file': '1'}
                    }
                },
                'searxng': {
                    'container_name': 'searxng',
                    'image': 'docker.io/searxng/searxng:latest',
                    'restart': 'unless-stopped',
                    'networks': ['searxng'],
                    'ports': ['8080:8080'],
                    'volumes': ['./searxng:/etc/searxng:rw'],
                    'environment': [
                        'SEARXNG_BASE_URL=http://localhost:8080/',
                        'UWSGI_WORKERS=4',
                        'UWSGI_THREADS=4'
                    ],
                    'cap_drop': ['ALL'],
                    'cap_add': ['CHOWN', 'SETGID', 'SETUID'],
                    'logging': {
                        'driver': 'json-file',
                        'options': {'max-size': '1m', 'max-file': '1'}
                    }
                }
            },
            'networks': {'searxng': None},
            'volumes': {'valkey-data': None}
        }
        
        with open(self.docker_dir / 'docker-compose.yml', 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
        
        # Create SearxNG configuration directory
        searxng_dir = self.docker_dir / 'searxng'
        searxng_dir.mkdir(exist_ok=True)
        
        # Create settings.yml
        settings = {
            'use_default_settings': True,
            'ui': {'static_use_hash': True},
            'server': {
                'secret_key': 'change-this-secret-key-in-production',
                'limiter': True,
                'image_proxy': True
            },
            'valkey': {'url': 'valkey://redis:6379/0'},
            'search': {
                'safe_search': 0,
                'autocomplete': '',
                'default_lang': '',
                'formats': ['html', 'json', 'csv', 'rss']
            },
            'ratelimit': {
                'enabled': True,
                'per_second': 5,
                'per_minute': 60
            },
            'timeouts': {
                'total': 10.0,
                'connect': 6.0
            },
            'outgoing': {'request_timeout': 20.0},
            'network': {
                'request_args': {
                    'max_redirects': 3,
                    'allow_redirects': True
                }
            }
        }
        
        with open(searxng_dir / 'settings.yml', 'w') as f:
            yaml.dump(settings, f, default_flow_style=False)
        
        # Create uwsgi.ini
        uwsgi_config = """[uwsgi]
module = searxng.webapp
callable = app
uid = searxng
gid = searxng
workers = %d
threads = %d
master = true
lazy-apps = true
enable-threads = true
http = 0.0.0.0:8080
single-interpreter = true
post-buffering = 4096
buffer-size = 8192
add-header = Connection: close
static-map = /static=/usr/local/searxng/searxng/static
static-expires = /* 86400
static-gzip-all = True
offload-threads = %d
""" % (4, 4, 4)
        
        with open(searxng_dir / 'uwsgi.ini', 'w') as f:
            f.write(uwsgi_config)
        
        # Create limiter.toml
        limiter_config = """[botdetection.ip_limit]
filter_link_local = false
link_local = ["169.254.0.0/16", "fe80::/10"]

[botdetection.ip_lists]
pass_searxng_org = [
    "207.241.225.11",
]
"""
        
        with open(searxng_dir / 'limiter.toml', 'w') as f:
            f.write(limiter_config)
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        return {
            'deployed': self._is_deployed,
            'base_url': self.base_url,
            'auto_deploy': self.auto_deploy,
            'docker_dir': str(self.docker_dir)
        }
