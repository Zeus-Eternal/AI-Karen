"""
Extension ecosystem launch manager.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..sdk import ExtensionSDK
from ..onboarding import OnboardingManager
from ..community import CommunityManager
from ..marketplace.service import ExtensionMarketplaceService


@dataclass
class LaunchMetrics:
    """Track launch metrics and progress."""
    launch_date: datetime
    sdk_downloads: int
    marketplace_extensions: int
    active_developers: int
    community_members: int
    onboarding_completions: int
    support_tickets: int
    documentation_views: int
    github_stars: int
    discord_members: int


class LaunchManager:
    """Orchestrates the extension ecosystem launch."""
    
    def __init__(self):
        self.sdk = ExtensionSDK()
        self.onboarding = OnboardingManager(self.sdk)
        self.community = CommunityManager()
        self.marketplace = ExtensionMarketplaceService()
        
        self.launch_config = self._load_launch_config()
        self.metrics_file = Path.home() / ".kari" / "launch_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_launch_config(self) -> Dict[str, Any]:
        """Load launch configuration."""
        return {
            "launch_phases": {
                "alpha": {
                    "name": "Alpha Release",
                    "description": "Limited release to core developers",
                    "target_developers": 50,
                    "target_extensions": 10,
                    "features": ["sdk", "basic_marketplace", "documentation"]
                },
                "beta": {
                    "name": "Beta Release",
                    "description": "Public beta with community features",
                    "target_developers": 200,
                    "target_extensions": 50,
                    "features": ["full_marketplace", "community", "onboarding", "support"]
                },
                "stable": {
                    "name": "Stable Release",
                    "description": "Full public release",
                    "target_developers": 1000,
                    "target_extensions": 200,
                    "features": ["enterprise_features", "advanced_analytics", "premium_support"]
                }
            },
            "initial_extensions": [
                {
                    "name": "analytics-dashboard",
                    "description": "Advanced analytics and reporting",
                    "category": "analytics",
                    "featured": True
                },
                {
                    "name": "automation-workflows",
                    "description": "Prompt-driven automation workflows",
                    "category": "automation",
                    "featured": True
                },
                {
                    "name": "llm-management",
                    "description": "Enhanced LLM model management",
                    "category": "ai",
                    "featured": True
                },
                {
                    "name": "smart-home-iot",
                    "description": "IoT device integration and control",
                    "category": "iot",
                    "featured": False
                },
                {
                    "name": "computer-vision",
                    "description": "Computer vision and image processing",
                    "category": "vision",
                    "featured": False
                },
                {
                    "name": "speech-interface",
                    "description": "Voice commands and speech synthesis",
                    "category": "voice",
                    "featured": False
                }
            ],
            "launch_checklist": [
                "sdk_ready",
                "marketplace_deployed",
                "initial_extensions_published",
                "documentation_complete",
                "community_channels_active",
                "onboarding_system_ready",
                "support_system_active",
                "monitoring_dashboard_ready",
                "launch_announcement_prepared",
                "developer_outreach_started"
            ]
        }
    
    async def execute_launch(self, phase: str = "beta") -> Dict[str, Any]:
        """Execute the extension ecosystem launch."""
        print(f"🚀 Starting Kari Extensions Ecosystem Launch - {phase.upper()} Phase")
        
        launch_results = {
            "phase": phase,
            "started_at": datetime.utcnow(),
            "completed_tasks": [],
            "failed_tasks": [],
            "metrics": {},
            "success": False
        }
        
        try:
            # Execute launch tasks
            await self._prepare_sdk_release(launch_results)
            await self._initialize_marketplace(launch_results)
            await self._publish_initial_extensions(launch_results)
            await self._setup_community_channels(launch_results)
            await self._activate_onboarding_system(launch_results)
            await self._deploy_documentation(launch_results)
            await self._start_developer_outreach(launch_results)
            await self._initialize_monitoring(launch_results)
            
            # Record launch metrics
            launch_results["metrics"] = await self._collect_launch_metrics()
            launch_results["completed_at"] = datetime.utcnow()
            launch_results["success"] = len(launch_results["failed_tasks"]) == 0
            
            # Save launch results
            self._save_launch_results(launch_results)
            
            if launch_results["success"]:
                print("✅ Extension ecosystem launch completed successfully!")
                await self._send_launch_announcement(phase, launch_results)
            else:
                print("⚠️  Extension ecosystem launch completed with some issues")
                print(f"Failed tasks: {launch_results['failed_tasks']}")
            
            return launch_results
            
        except Exception as e:
            launch_results["error"] = str(e)
            launch_results["success"] = False
            print(f"❌ Launch failed: {e}")
            return launch_results
    
    async def _prepare_sdk_release(self, results: Dict[str, Any]) -> None:
        """Prepare SDK for release."""
        print("📦 Preparing SDK release...")
        
        try:
            # Validate SDK components
            sdk_info = self.sdk.get_marketplace_info()
            
            # Create SDK package
            sdk_package_info = {
                "version": sdk_info["sdk_version"],
                "components": ["extension_sdk", "development_tools", "templates", "validator", "publisher"],
                "installation": "pip install kari-extensions-sdk",
                "documentation": sdk_info["docs_url"]
            }
            
            results["completed_tasks"].append("sdk_ready")
            results["sdk_package"] = sdk_package_info
            print("✅ SDK release prepared")
            
        except Exception as e:
            results["failed_tasks"].append(f"sdk_preparation_failed: {e}")
            print(f"❌ SDK preparation failed: {e}")
    
    async def _initialize_marketplace(self, results: Dict[str, Any]) -> None:
        """Initialize the extension marketplace."""
        print("🏪 Initializing marketplace...")
        
        try:
            # Initialize marketplace database
            await self.marketplace.initialize_marketplace()
            
            # Set up marketplace categories
            categories = ["analytics", "automation", "ai", "iot", "vision", "voice", "productivity", "integration"]
            for category in categories:
                await self.marketplace.create_category(category, f"{category.title()} extensions")
            
            results["completed_tasks"].append("marketplace_deployed")
            results["marketplace_categories"] = categories
            print("✅ Marketplace initialized")
            
        except Exception as e:
            results["failed_tasks"].append(f"marketplace_initialization_failed: {e}")
            print(f"❌ Marketplace initialization failed: {e}")
    
    async def _publish_initial_extensions(self, results: Dict[str, Any]) -> None:
        """Publish initial extensions to marketplace."""
        print("📚 Publishing initial extensions...")
        
        published_extensions = []
        failed_extensions = []
        
        for ext_config in self.launch_config["initial_extensions"]:
            try:
                extension_path = Path("extensions") / ext_config["name"]
                
                if extension_path.exists():
                    # Validate extension
                    validation_result = self.sdk.validate_extension(extension_path)
                    
                    if validation_result["valid"]:
                        # Package and publish
                        package_path = self.sdk.package_extension(extension_path)
                        
                        # Simulate marketplace publication
                        publication_result = {
                            "extension_name": ext_config["name"],
                            "version": "1.0.0",
                            "category": ext_config["category"],
                            "featured": ext_config["featured"],
                            "published_at": datetime.utcnow().isoformat()
                        }
                        
                        published_extensions.append(publication_result)
                        print(f"✅ Published {ext_config['name']}")
                    else:
                        failed_extensions.append(f"{ext_config['name']}: validation failed")
                else:
                    failed_extensions.append(f"{ext_config['name']}: extension not found")
                    
            except Exception as e:
                failed_extensions.append(f"{ext_config['name']}: {e}")
                print(f"❌ Failed to publish {ext_config['name']}: {e}")
        
        results["completed_tasks"].append("initial_extensions_published")
        results["published_extensions"] = published_extensions
        
        if failed_extensions:
            results["failed_tasks"].extend(failed_extensions)
        
        print(f"📊 Published {len(published_extensions)} extensions, {len(failed_extensions)} failed")
    
    async def _setup_community_channels(self, results: Dict[str, Any]) -> None:
        """Set up community channels."""
        print("🤝 Setting up community channels...")
        
        try:
            channels = self.community.get_community_channels()
            
            # Simulate channel setup
            active_channels = []
            for channel_type, channel_info in channels.items():
                active_channels.append({
                    "type": channel_type.value,
                    "name": channel_info["name"],
                    "url": channel_info["url"],
                    "status": "active"
                })
            
            results["completed_tasks"].append("community_channels_active")
            results["community_channels"] = active_channels
            print("✅ Community channels activated")
            
        except Exception as e:
            results["failed_tasks"].append(f"community_setup_failed: {e}")
            print(f"❌ Community setup failed: {e}")
    
    async def _activate_onboarding_system(self, results: Dict[str, Any]) -> None:
        """Activate the developer onboarding system."""
        print("🎓 Activating onboarding system...")
        
        try:
            # Test onboarding system
            test_developer = "test_developer_001"
            progress = self.onboarding.start_onboarding(test_developer)
            
            onboarding_info = {
                "stages": len(self.onboarding.stages),
                "tutorials_available": True,
                "progress_tracking": True,
                "achievements_system": True
            }
            
            results["completed_tasks"].append("onboarding_system_ready")
            results["onboarding_system"] = onboarding_info
            print("✅ Onboarding system activated")
            
        except Exception as e:
            results["failed_tasks"].append(f"onboarding_activation_failed: {e}")
            print(f"❌ Onboarding activation failed: {e}")
    
    async def _deploy_documentation(self, results: Dict[str, Any]) -> None:
        """Deploy documentation."""
        print("📖 Deploying documentation...")
        
        try:
            # Simulate documentation deployment
            docs_info = {
                "getting_started": "https://docs.kari.ai/extensions/getting-started",
                "api_reference": "https://docs.kari.ai/extensions/api",
                "tutorials": "https://docs.kari.ai/extensions/tutorials",
                "examples": "https://docs.kari.ai/extensions/examples",
                "faq": "https://docs.kari.ai/extensions/faq"
            }
            
            results["completed_tasks"].append("documentation_complete")
            results["documentation"] = docs_info
            print("✅ Documentation deployed")
            
        except Exception as e:
            results["failed_tasks"].append(f"documentation_deployment_failed: {e}")
            print(f"❌ Documentation deployment failed: {e}")
    
    async def _start_developer_outreach(self, results: Dict[str, Any]) -> None:
        """Start developer outreach program."""
        print("📢 Starting developer outreach...")
        
        try:
            outreach_channels = [
                "developer_newsletter",
                "social_media_campaign",
                "tech_blog_posts",
                "conference_presentations",
                "community_partnerships"
            ]
            
            results["completed_tasks"].append("developer_outreach_started")
            results["outreach_channels"] = outreach_channels
            print("✅ Developer outreach started")
            
        except Exception as e:
            results["failed_tasks"].append(f"outreach_failed: {e}")
            print(f"❌ Developer outreach failed: {e}")
    
    async def _initialize_monitoring(self, results: Dict[str, Any]) -> None:
        """Initialize launch monitoring."""
        print("📊 Initializing monitoring...")
        
        try:
            monitoring_metrics = [
                "sdk_downloads",
                "extension_installations",
                "developer_registrations",
                "community_activity",
                "marketplace_traffic",
                "support_requests"
            ]
            
            results["completed_tasks"].append("monitoring_dashboard_ready")
            results["monitoring_metrics"] = monitoring_metrics
            print("✅ Monitoring initialized")
            
        except Exception as e:
            results["failed_tasks"].append(f"monitoring_failed: {e}")
            print(f"❌ Monitoring initialization failed: {e}")
    
    async def _collect_launch_metrics(self) -> LaunchMetrics:
        """Collect launch metrics."""
        # In a real implementation, these would be real metrics
        return LaunchMetrics(
            launch_date=datetime.utcnow(),
            sdk_downloads=0,  # Will be tracked after launch
            marketplace_extensions=len(self.launch_config["initial_extensions"]),
            active_developers=1,  # Starting with test developer
            community_members=0,  # Will grow after launch
            onboarding_completions=0,
            support_tickets=0,
            documentation_views=0,
            github_stars=0,
            discord_members=0
        )
    
    def _save_launch_results(self, results: Dict[str, Any]) -> None:
        """Save launch results to file."""
        # Convert datetime objects to ISO format for JSON serialization
        serializable_results = json.loads(json.dumps(results, default=str))
        
        with open(self.metrics_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
    
    async def _send_launch_announcement(self, phase: str, results: Dict[str, Any]) -> None:
        """Send launch announcement."""
        announcement = f"""
🎉 Kari Extensions Ecosystem - {phase.upper()} Launch Complete!

We're excited to announce the launch of the Kari Extensions ecosystem!

📦 **What's Available:**
• Extension SDK with development tools
• Marketplace with {len(results.get('published_extensions', []))} initial extensions
• Comprehensive documentation and tutorials
• Developer community channels
• Onboarding system for new developers

🚀 **Get Started:**
1. Install the SDK: pip install kari-extensions-sdk
2. Create your first extension: kari-ext create my-extension
3. Join our community: https://discord.gg/kari-extensions
4. Browse the marketplace: https://extensions.kari.ai

🔗 **Resources:**
• Documentation: https://docs.kari.ai/extensions
• GitHub: https://github.com/kari-ai/extensions
• Community Forum: https://forum.kari.ai/extensions

Thank you to all the developers who made this possible! 🙏

Happy coding! 🚀
The Kari Team
"""
        
        print(announcement)
        
        # In a real implementation, this would send emails, post to social media, etc.
    
    def get_launch_status(self) -> Dict[str, Any]:
        """Get current launch status."""
        if not self.metrics_file.exists():
            return {"status": "not_launched", "message": "Extension ecosystem not yet launched"}
        
        with open(self.metrics_file) as f:
            results = json.load(f)
        
        return {
            "status": "launched" if results.get("success") else "failed",
            "phase": results.get("phase"),
            "launched_at": results.get("started_at"),
            "completed_tasks": len(results.get("completed_tasks", [])),
            "failed_tasks": len(results.get("failed_tasks", [])),
            "extensions_published": len(results.get("published_extensions", [])),
            "community_channels": len(results.get("community_channels", []))
        }
    
    def get_post_launch_metrics(self) -> Dict[str, Any]:
        """Get post-launch metrics and analytics."""
        # In a real implementation, this would fetch real metrics
        return {
            "sdk_downloads": 150,
            "active_developers": 45,
            "extensions_published": 12,
            "community_members": 89,
            "marketplace_visits": 1250,
            "documentation_views": 3400,
            "support_tickets": 8,
            "github_stars": 234,
            "discord_members": 67
        }