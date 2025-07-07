"""
Kari Home Page
- Orchestrates: Onboarding, activity, branding, news/announcements
"""

from src.ui_logic.components.white_label.branding_center import \
    render_branding_center


def home_page(user_ctx=None):
    # Welcome and Branding
    render_branding_center(user_ctx=user_ctx)
    # Additional: Welcome, onboarding, recent activity (placeholders for now)
    print("Welcome to Kari AI! More onboarding features coming soon.")
