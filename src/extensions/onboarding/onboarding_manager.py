"""
Extension developer onboarding manager.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ..sdk import ExtensionSDK


class OnboardingStage(Enum):
    """Onboarding stages for developers."""
    WELCOME = "welcome"
    SETUP = "setup"
    FIRST_EXTENSION = "first_extension"
    ADVANCED_FEATURES = "advanced_features"
    MARKETPLACE = "marketplace"
    COMMUNITY = "community"
    COMPLETED = "completed"


@dataclass
class OnboardingProgress:
    """Track developer onboarding progress."""
    developer_id: str
    current_stage: OnboardingStage
    completed_stages: List[OnboardingStage]
    started_at: datetime
    last_activity: datetime
    completed_tutorials: List[str]
    created_extensions: List[str]
    published_extensions: List[str]
    achievements: List[str]


class OnboardingManager:
    """Manages the developer onboarding experience."""
    
    def __init__(self, sdk: ExtensionSDK):
        self.sdk = sdk
        self.progress_file = Path.home() / ".kari" / "developer_progress.json"
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize onboarding stages
        self.stages = {
            OnboardingStage.WELCOME: {
                "title": "Welcome to Kari Extensions",
                "description": "Get started with extension development",
                "tasks": [
                    "complete_welcome_tutorial",
                    "setup_development_environment"
                ],
                "estimated_time": "15 minutes"
            },
            OnboardingStage.SETUP: {
                "title": "Development Environment Setup",
                "description": "Configure your development environment",
                "tasks": [
                    "install_sdk",
                    "verify_installation",
                    "configure_workspace"
                ],
                "estimated_time": "10 minutes"
            },
            OnboardingStage.FIRST_EXTENSION: {
                "title": "Create Your First Extension",
                "description": "Build a simple extension from template",
                "tasks": [
                    "create_basic_extension",
                    "understand_manifest",
                    "run_development_server",
                    "test_extension"
                ],
                "estimated_time": "30 minutes"
            },
            OnboardingStage.ADVANCED_FEATURES: {
                "title": "Advanced Extension Features",
                "description": "Learn about APIs, UIs, and automation",
                "tasks": [
                    "create_api_extension",
                    "add_ui_components",
                    "implement_background_tasks",
                    "use_plugin_orchestration"
                ],
                "estimated_time": "60 minutes"
            },
            OnboardingStage.MARKETPLACE: {
                "title": "Publishing to Marketplace",
                "description": "Package and publish your extension",
                "tasks": [
                    "validate_extension",
                    "package_extension",
                    "create_marketplace_account",
                    "publish_extension"
                ],
                "estimated_time": "20 minutes"
            },
            OnboardingStage.COMMUNITY: {
                "title": "Join the Community",
                "description": "Connect with other developers",
                "tasks": [
                    "join_discord_server",
                    "participate_in_forum",
                    "contribute_to_docs",
                    "share_extension"
                ],
                "estimated_time": "15 minutes"
            }
        }
    
    def start_onboarding(self, developer_id: str) -> OnboardingProgress:
        """Start onboarding process for a new developer."""
        progress = OnboardingProgress(
            developer_id=developer_id,
            current_stage=OnboardingStage.WELCOME,
            completed_stages=[],
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            completed_tutorials=[],
            created_extensions=[],
            published_extensions=[],
            achievements=[]
        )
        
        self._save_progress(progress)
        return progress
    
    def get_progress(self, developer_id: str) -> Optional[OnboardingProgress]:
        """Get onboarding progress for a developer."""
        if not self.progress_file.exists():
            return None
        
        try:
            with open(self.progress_file) as f:
                data = json.load(f)
            
            if developer_id not in data:
                return None
            
            progress_data = data[developer_id]
            
            # Convert back to dataclass
            progress = OnboardingProgress(
                developer_id=progress_data["developer_id"],
                current_stage=OnboardingStage(progress_data["current_stage"]),
                completed_stages=[OnboardingStage(s) for s in progress_data["completed_stages"]],
                started_at=datetime.fromisoformat(progress_data["started_at"]),
                last_activity=datetime.fromisoformat(progress_data["last_activity"]),
                completed_tutorials=progress_data["completed_tutorials"],
                created_extensions=progress_data["created_extensions"],
                published_extensions=progress_data["published_extensions"],
                achievements=progress_data["achievements"]
            )
            
            return progress
            
        except Exception as e:
            print(f"Error loading progress: {e}")
            return None
    
    def update_progress(
        self, 
        developer_id: str,
        completed_task: Optional[str] = None,
        created_extension: Optional[str] = None,
        published_extension: Optional[str] = None
    ) -> OnboardingProgress:
        """Update developer progress."""
        progress = self.get_progress(developer_id)
        if not progress:
            progress = self.start_onboarding(developer_id)
        
        progress.last_activity = datetime.utcnow()
        
        # Track completed tasks
        if completed_task:
            if completed_task not in progress.completed_tutorials:
                progress.completed_tutorials.append(completed_task)
        
        # Track created extensions
        if created_extension:
            if created_extension not in progress.created_extensions:
                progress.created_extensions.append(created_extension)
                self._check_achievements(progress, "first_extension")
        
        # Track published extensions
        if published_extension:
            if published_extension not in progress.published_extensions:
                progress.published_extensions.append(published_extension)
                self._check_achievements(progress, "first_publication")
        
        # Check if current stage is completed
        self._check_stage_completion(progress)
        
        self._save_progress(progress)
        return progress
    
    def _check_stage_completion(self, progress: OnboardingProgress) -> None:
        """Check if current stage is completed and advance if needed."""
        current_stage_info = self.stages[progress.current_stage]
        required_tasks = current_stage_info["tasks"]
        
        # Check if all tasks are completed
        completed_tasks = set(progress.completed_tutorials)
        
        # Special checks for certain stages
        if progress.current_stage == OnboardingStage.FIRST_EXTENSION:
            if len(progress.created_extensions) > 0:
                completed_tasks.add("create_basic_extension")
        
        if progress.current_stage == OnboardingStage.MARKETPLACE:
            if len(progress.published_extensions) > 0:
                completed_tasks.add("publish_extension")
        
        # Check if stage is complete
        if all(task in completed_tasks for task in required_tasks):
            if progress.current_stage not in progress.completed_stages:
                progress.completed_stages.append(progress.current_stage)
            
            # Advance to next stage
            next_stage = self._get_next_stage(progress.current_stage)
            if next_stage:
                progress.current_stage = next_stage
    
    def _get_next_stage(self, current_stage: OnboardingStage) -> Optional[OnboardingStage]:
        """Get the next onboarding stage."""
        stage_order = [
            OnboardingStage.WELCOME,
            OnboardingStage.SETUP,
            OnboardingStage.FIRST_EXTENSION,
            OnboardingStage.ADVANCED_FEATURES,
            OnboardingStage.MARKETPLACE,
            OnboardingStage.COMMUNITY,
            OnboardingStage.COMPLETED
        ]
        
        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def _check_achievements(self, progress: OnboardingProgress, achievement_type: str) -> None:
        """Check and award achievements."""
        achievements = {
            "first_extension": {
                "title": "First Extension Creator",
                "description": "Created your first extension",
                "condition": lambda p: len(p.created_extensions) >= 1
            },
            "first_publication": {
                "title": "Publisher",
                "description": "Published your first extension to marketplace",
                "condition": lambda p: len(p.published_extensions) >= 1
            },
            "prolific_creator": {
                "title": "Prolific Creator",
                "description": "Created 5 or more extensions",
                "condition": lambda p: len(p.created_extensions) >= 5
            },
            "tutorial_master": {
                "title": "Tutorial Master",
                "description": "Completed all onboarding tutorials",
                "condition": lambda p: len(p.completed_tutorials) >= 10
            },
            "quick_learner": {
                "title": "Quick Learner",
                "description": "Completed onboarding in under 2 hours",
                "condition": lambda p: (p.last_activity - p.started_at) < timedelta(hours=2)
            }
        }
        
        for achievement_id, achievement in achievements.items():
            if achievement_id not in progress.achievements:
                if achievement["condition"](progress):
                    progress.achievements.append(achievement_id)
                    print(f"🏆 Achievement unlocked: {achievement['title']}")
    
    def _save_progress(self, progress: OnboardingProgress) -> None:
        """Save progress to file."""
        data = {}
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                data = json.load(f)
        
        # Convert dataclass to dict for JSON serialization
        progress_dict = asdict(progress)
        progress_dict["current_stage"] = progress.current_stage.value
        progress_dict["completed_stages"] = [s.value for s in progress.completed_stages]
        progress_dict["started_at"] = progress.started_at.isoformat()
        progress_dict["last_activity"] = progress.last_activity.isoformat()
        
        data[progress.developer_id] = progress_dict
        
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_current_stage_info(self, developer_id: str) -> Dict[str, Any]:
        """Get information about current onboarding stage."""
        progress = self.get_progress(developer_id)
        if not progress:
            return self.stages[OnboardingStage.WELCOME]
        
        stage_info = self.stages[progress.current_stage].copy()
        stage_info["progress"] = progress
        
        return stage_info
    
    def get_next_steps(self, developer_id: str) -> List[Dict[str, Any]]:
        """Get recommended next steps for developer."""
        progress = self.get_progress(developer_id)
        if not progress:
            return self._get_welcome_steps()
        
        current_stage_info = self.stages[progress.current_stage]
        completed_tasks = set(progress.completed_tutorials)
        
        next_steps = []
        for task in current_stage_info["tasks"]:
            if task not in completed_tasks:
                next_steps.append({
                    "task": task,
                    "title": self._get_task_title(task),
                    "description": self._get_task_description(task),
                    "action": self._get_task_action(task)
                })
        
        return next_steps
    
    def _get_welcome_steps(self) -> List[Dict[str, Any]]:
        """Get welcome steps for new developers."""
        return [
            {
                "task": "complete_welcome_tutorial",
                "title": "Complete Welcome Tutorial",
                "description": "Learn the basics of Kari extension development",
                "action": "kari-ext tutorial welcome"
            },
            {
                "task": "setup_development_environment",
                "title": "Setup Development Environment",
                "description": "Install and configure the Kari Extensions SDK",
                "action": "pip install kari-extensions-sdk"
            }
        ]
    
    def _get_task_title(self, task: str) -> str:
        """Get human-readable title for task."""
        titles = {
            "complete_welcome_tutorial": "Complete Welcome Tutorial",
            "setup_development_environment": "Setup Development Environment",
            "install_sdk": "Install Extensions SDK",
            "verify_installation": "Verify Installation",
            "configure_workspace": "Configure Workspace",
            "create_basic_extension": "Create Basic Extension",
            "understand_manifest": "Understand Extension Manifest",
            "run_development_server": "Run Development Server",
            "test_extension": "Test Extension",
            "create_api_extension": "Create API Extension",
            "add_ui_components": "Add UI Components",
            "implement_background_tasks": "Implement Background Tasks",
            "use_plugin_orchestration": "Use Plugin Orchestration",
            "validate_extension": "Validate Extension",
            "package_extension": "Package Extension",
            "create_marketplace_account": "Create Marketplace Account",
            "publish_extension": "Publish Extension",
            "join_discord_server": "Join Discord Server",
            "participate_in_forum": "Participate in Forum",
            "contribute_to_docs": "Contribute to Documentation",
            "share_extension": "Share Your Extension"
        }
        return titles.get(task, task.replace('_', ' ').title())
    
    def _get_task_description(self, task: str) -> str:
        """Get description for task."""
        descriptions = {
            "complete_welcome_tutorial": "Learn the fundamentals of Kari extension development",
            "setup_development_environment": "Install and configure your development tools",
            "create_basic_extension": "Create your first extension using a template",
            "validate_extension": "Ensure your extension meets quality standards",
            "publish_extension": "Share your extension with the community"
        }
        return descriptions.get(task, f"Complete the {task.replace('_', ' ')} task")
    
    def _get_task_action(self, task: str) -> str:
        """Get CLI command or action for task."""
        actions = {
            "create_basic_extension": "kari-ext create my-first-extension",
            "validate_extension": "kari-ext validate",
            "package_extension": "kari-ext package",
            "publish_extension": "kari-ext publish",
            "run_development_server": "kari-ext dev --watch"
        }
        return actions.get(task, f"Complete {task}")