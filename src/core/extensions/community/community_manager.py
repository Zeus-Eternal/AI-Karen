"""
Extension community management system.
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class CommunityChannel(Enum):
    """Community channels available."""
    DISCORD = "discord"
    FORUM = "forum"
    GITHUB = "github"
    DOCS = "docs"
    BLOG = "blog"
    NEWSLETTER = "newsletter"


@dataclass
class CommunityMember:
    """Community member profile."""
    developer_id: str
    username: str
    email: str
    joined_at: datetime
    last_active: datetime
    reputation: int
    badges: List[str]
    contributions: Dict[str, int]
    preferences: Dict[str, Any]


@dataclass
class CommunityEvent:
    """Community event information."""
    event_id: str
    title: str
    description: str
    event_type: str  # workshop, webinar, hackathon, meetup
    start_time: datetime
    end_time: datetime
    location: str  # online, city, or venue
    max_participants: Optional[int]
    registration_url: str
    tags: List[str]


class CommunityManager:
    """Manages the extension developer community."""
    
    def __init__(self):
        self.community_config = self._load_community_config()
        self.members_file = Path.home() / ".kari" / "community_profile.json"
        self.members_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_community_config(self) -> Dict[str, Any]:
        """Load community configuration."""
        return {
            "channels": {
                CommunityChannel.DISCORD: {
                    "name": "Kari Extensions Discord",
                    "url": "https://discord.gg/kari-extensions",
                    "description": "Real-time chat with developers and support team",
                    "features": ["chat", "voice", "screen_share", "support"]
                },
                CommunityChannel.FORUM: {
                    "name": "Developer Forum",
                    "url": "https://forum.kari.ai/extensions",
                    "description": "Discussion forum for extension development",
                    "features": ["discussions", "q_and_a", "showcase", "feedback"]
                },
                CommunityChannel.GITHUB: {
                    "name": "GitHub Repository",
                    "url": "https://github.com/kari-ai/extensions",
                    "description": "Source code, issues, and contributions",
                    "features": ["source_code", "issues", "pull_requests", "releases"]
                },
                CommunityChannel.DOCS: {
                    "name": "Documentation",
                    "url": "https://docs.kari.ai/extensions",
                    "description": "Comprehensive extension development guides",
                    "features": ["tutorials", "api_reference", "examples", "best_practices"]
                },
                CommunityChannel.BLOG: {
                    "name": "Developer Blog",
                    "url": "https://blog.kari.ai/extensions",
                    "description": "Latest news, tutorials, and developer stories",
                    "features": ["news", "tutorials", "case_studies", "interviews"]
                },
                CommunityChannel.NEWSLETTER: {
                    "name": "Developer Newsletter",
                    "url": "https://kari.ai/newsletter/developers",
                    "description": "Weekly updates on extension development",
                    "features": ["weekly_updates", "featured_extensions", "tips", "events"]
                }
            },
            "support_levels": {
                "community": {
                    "name": "Community Support",
                    "description": "Free support from community members",
                    "channels": ["discord", "forum"],
                    "response_time": "Best effort"
                },
                "standard": {
                    "name": "Standard Support",
                    "description": "Email support for published extensions",
                    "channels": ["email", "forum"],
                    "response_time": "48 hours"
                },
                "premium": {
                    "name": "Premium Support",
                    "description": "Priority support with dedicated assistance",
                    "channels": ["email", "discord", "video_call"],
                    "response_time": "4 hours"
                }
            },
            "events": {
                "recurring": [
                    {
                        "name": "Extension Developer Meetup",
                        "frequency": "monthly",
                        "format": "online",
                        "description": "Monthly meetup for extension developers"
                    },
                    {
                        "name": "Extension Showcase",
                        "frequency": "quarterly",
                        "format": "online",
                        "description": "Showcase your extensions to the community"
                    }
                ]
            }
        }
    
    def join_community(
        self, 
        developer_id: str,
        username: str,
        email: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> CommunityMember:
        """Register developer in community."""
        member = CommunityMember(
            developer_id=developer_id,
            username=username,
            email=email,
            joined_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            reputation=0,
            badges=[],
            contributions={
                "extensions_published": 0,
                "forum_posts": 0,
                "github_contributions": 0,
                "documentation_edits": 0,
                "community_help": 0
            },
            preferences=preferences or {
                "newsletter": True,
                "event_notifications": True,
                "community_updates": True,
                "marketing_emails": False
            }
        )
        
        self._save_member_profile(member)
        
        # Send welcome message
        self._send_welcome_message(member)
        
        return member
    
    def get_member_profile(self, developer_id: str) -> Optional[CommunityMember]:
        """Get community member profile."""
        if not self.members_file.exists():
            return None
        
        try:
            with open(self.members_file) as f:
                data = json.load(f)
            
            if developer_id not in data:
                return None
            
            member_data = data[developer_id]
            
            return CommunityMember(
                developer_id=member_data["developer_id"],
                username=member_data["username"],
                email=member_data["email"],
                joined_at=datetime.fromisoformat(member_data["joined_at"]),
                last_active=datetime.fromisoformat(member_data["last_active"]),
                reputation=member_data["reputation"],
                badges=member_data["badges"],
                contributions=member_data["contributions"],
                preferences=member_data["preferences"]
            )
            
        except Exception as e:
            print(f"Error loading member profile: {e}")
            return None
    
    def update_member_activity(
        self, 
        developer_id: str,
        activity_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update member activity and contributions."""
        member = self.get_member_profile(developer_id)
        if not member:
            return
        
        member.last_active = datetime.utcnow()
        
        # Update contributions based on activity
        if activity_type == "extension_published":
            member.contributions["extensions_published"] += 1
            member.reputation += 50
            self._check_badges(member, "publisher")
        
        elif activity_type == "forum_post":
            member.contributions["forum_posts"] += 1
            member.reputation += 5
            self._check_badges(member, "contributor")
        
        elif activity_type == "github_contribution":
            member.contributions["github_contributions"] += 1
            member.reputation += 10
            self._check_badges(member, "contributor")
        
        elif activity_type == "documentation_edit":
            member.contributions["documentation_edits"] += 1
            member.reputation += 15
            self._check_badges(member, "documentarian")
        
        elif activity_type == "community_help":
            member.contributions["community_help"] += 1
            member.reputation += 8
            self._check_badges(member, "helper")
        
        self._save_member_profile(member)
    
    def _check_badges(self, member: CommunityMember, badge_category: str) -> None:
        """Check and award badges to member."""
        badges = {
            "publisher": [
                {"name": "First Extension", "condition": lambda m: m.contributions["extensions_published"] >= 1},
                {"name": "Prolific Publisher", "condition": lambda m: m.contributions["extensions_published"] >= 5},
                {"name": "Extension Master", "condition": lambda m: m.contributions["extensions_published"] >= 10}
            ],
            "contributor": [
                {"name": "Community Contributor", "condition": lambda m: m.contributions["forum_posts"] >= 10},
                {"name": "GitHub Contributor", "condition": lambda m: m.contributions["github_contributions"] >= 5},
                {"name": "Active Member", "condition": lambda m: m.reputation >= 100}
            ],
            "documentarian": [
                {"name": "Documentation Helper", "condition": lambda m: m.contributions["documentation_edits"] >= 3},
                {"name": "Documentation Expert", "condition": lambda m: m.contributions["documentation_edits"] >= 10}
            ],
            "helper": [
                {"name": "Community Helper", "condition": lambda m: m.contributions["community_help"] >= 5},
                {"name": "Support Champion", "condition": lambda m: m.contributions["community_help"] >= 20}
            ]
        }
        
        category_badges = badges.get(badge_category, [])
        for badge in category_badges:
            if badge["name"] not in member.badges and badge["condition"](member):
                member.badges.append(badge["name"])
                print(f"🏆 Badge earned: {badge['name']}")
    
    def _save_member_profile(self, member: CommunityMember) -> None:
        """Save member profile to file."""
        data = {}
        if self.members_file.exists():
            with open(self.members_file) as f:
                data = json.load(f)
        
        member_dict = asdict(member)
        member_dict["joined_at"] = member.joined_at.isoformat()
        member_dict["last_active"] = member.last_active.isoformat()
        
        data[member.developer_id] = member_dict
        
        with open(self.members_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _send_welcome_message(self, member: CommunityMember) -> None:
        """Send welcome message to new community member."""
        welcome_message = f"""
🎉 Welcome to the Kari Extensions Community, {member.username}!

We're excited to have you join our community of extension developers. Here's how to get started:

🔗 **Join our channels:**
• Discord: {self.community_config['channels'][CommunityChannel.DISCORD]['url']}
• Forum: {self.community_config['channels'][CommunityChannel.FORUM]['url']}
• Documentation: {self.community_config['channels'][CommunityChannel.DOCS]['url']}

📚 **Resources:**
• Extension Development Guide: https://docs.kari.ai/extensions/getting-started
• API Reference: https://docs.kari.ai/extensions/api
• Example Extensions: https://github.com/kari-ai/extension-examples

🤝 **Get Help:**
• Ask questions in Discord or the forum
• Check out our FAQ: https://docs.kari.ai/extensions/faq
• Report issues: https://github.com/kari-ai/extensions/issues

Happy coding! 🚀
"""
        
        print(welcome_message)
        
        # In a real implementation, this would send an email
        # self._send_email(member.email, "Welcome to Kari Extensions Community", welcome_message)
    
    def get_community_channels(self) -> Dict[str, Any]:
        """Get information about community channels."""
        return self.community_config["channels"]
    
    def get_upcoming_events(self, limit: int = 10) -> List[CommunityEvent]:
        """Get upcoming community events."""
        # In a real implementation, this would fetch from an events API
        # For now, return sample events
        now = datetime.utcnow()
        
        sample_events = [
            CommunityEvent(
                event_id="meetup-2024-01",
                title="Extension Developer Meetup - January 2024",
                description="Monthly meetup for extension developers to share experiences and learn from each other",
                event_type="meetup",
                start_time=now + timedelta(days=7),
                end_time=now + timedelta(days=7, hours=2),
                location="online",
                max_participants=100,
                registration_url="https://events.kari.ai/meetup-2024-01",
                tags=["meetup", "networking", "learning"]
            ),
            CommunityEvent(
                event_id="workshop-api-2024",
                title="Building API Extensions Workshop",
                description="Hands-on workshop on creating extensions with REST APIs",
                event_type="workshop",
                start_time=now + timedelta(days=14),
                end_time=now + timedelta(days=14, hours=3),
                location="online",
                max_participants=50,
                registration_url="https://events.kari.ai/workshop-api-2024",
                tags=["workshop", "api", "hands-on"]
            ),
            CommunityEvent(
                event_id="hackathon-2024-q1",
                title="Kari Extensions Hackathon Q1 2024",
                description="48-hour hackathon to build innovative extensions",
                event_type="hackathon",
                start_time=now + timedelta(days=30),
                end_time=now + timedelta(days=32),
                location="online",
                max_participants=200,
                registration_url="https://events.kari.ai/hackathon-2024-q1",
                tags=["hackathon", "competition", "innovation"]
            )
        ]
        
        return sample_events[:limit]
    
    def get_support_options(self) -> Dict[str, Any]:
        """Get available support options."""
        return self.community_config["support_levels"]
    
    def submit_feedback(
        self, 
        developer_id: str,
        feedback_type: str,
        subject: str,
        message: str,
        extension_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit feedback or support request."""
        feedback_data = {
            "feedback_id": f"feedback_{int(datetime.utcnow().timestamp())}",
            "developer_id": developer_id,
            "feedback_type": feedback_type,  # bug_report, feature_request, general_feedback
            "subject": subject,
            "message": message,
            "extension_name": extension_name,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "submitted"
        }
        
        # In a real implementation, this would submit to a support system
        print(f"📝 Feedback submitted: {subject}")
        
        return {
            "success": True,
            "feedback_id": feedback_data["feedback_id"],
            "message": "Thank you for your feedback! We'll review it and get back to you."
        }
    
    def get_community_stats(self) -> Dict[str, Any]:
        """Get community statistics."""
        # In a real implementation, this would fetch real stats
        return {
            "total_members": 1250,
            "active_this_month": 340,
            "total_extensions": 89,
            "extensions_this_month": 12,
            "forum_posts_this_month": 156,
            "discord_members": 890,
            "github_stars": 2100,
            "documentation_pages": 45
        }
    
    def search_community_content(
        self, 
        query: str,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search community content."""
        # In a real implementation, this would search across all community content
        # For now, return sample results
        return [
            {
                "type": "forum_post",
                "title": f"How to implement {query} in extensions",
                "url": f"https://forum.kari.ai/extensions/posts/how-to-{query}",
                "author": "community_member",
                "created_at": "2024-01-15T10:30:00Z",
                "excerpt": f"Discussion about implementing {query} functionality..."
            },
            {
                "type": "documentation",
                "title": f"{query.title()} API Reference",
                "url": f"https://docs.kari.ai/extensions/api/{query}",
                "section": "API Reference",
                "updated_at": "2024-01-10T14:20:00Z",
                "excerpt": f"Complete API reference for {query} functionality..."
            }
        ]