"""
Travel Response Formatter Plugin
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

logger = logging.getLogger(__name__)

@dataclass
class TravelDestination:
    name: str
    country: Optional[str] = None
    description: Optional[str] = None

@dataclass
class TravelActivity:
    name: str
    type: str
    description: Optional[str] = None

@dataclass
class TravelAccommodation:
    name: str
    type: str
    price_range: Optional[str] = None

@dataclass
class TravelTip:
    category: str
    title: str
    description: str

@dataclass
class TravelInfo:
    destination: TravelDestination
    activities: List[TravelActivity] = None
    accommodations: List[TravelAccommodation] = None
    tips: List[TravelTip] = None
    total_duration: Optional[str] = None
    estimated_budget: Optional[str] = None
    
    def __post_init__(self):
        if self.activities is None:
            self.activities = []
        if self.accommodations is None:
            self.accommodations = []
        if self.tips is None:
            self.tips = []

class TravelResponseFormatter(ResponseFormatter):
    def __init__(self):
        super().__init__("travel", "1.0.0")
        self._travel_patterns = [
            r'(?i)\b(?:travel|trip|vacation|holiday|visit|tour)',
            r'(?i)(?:destination|place to visit|tourist attraction)',
            r'(?i)(?:itinerary|schedule|plan)',
            r'(?i)(?:hotel|accommodation|stay|lodging|resort)',
            r'(?i)(?:flight|airline|airport|booking)',
            r'(?i)(?:sightseeing|tourist|tourism|explore)',
        ]
        self._activity_icons = {
            'sightseeing': '🏛️',
            'cultural': '🎭',
            'adventure': '🏔️',
            'beach': '🏖️',
            'food': '🍽️',
            'shopping': '🛍️',
            'nature': '🌿',
        }
        self._accommodation_icons = {
            'hotel': '🏨',
            'resort': '🏖️',
            'hostel': '🏠',
            'apartment': '🏠',
        }
        self._tip_icons = {
            'safety': '🛡️',
            'budget': '💰',
            'cultural': '🌍',
            'general': 'ℹ️',
        }
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        if not self.validate_content(content, context):
            return False
        if context.detected_content_type == ContentType.TRAVEL:
            return True
        content_lower = content.lower()
        travel_keywords = [
            'travel', 'trip', 'vacation', 'holiday', 'visit', 'tour', 'destination',
            'itinerary', 'hotel', 'flight', 'booking', 'sightseeing', 'tourist',
        ]
        keyword_count = sum(1 for keyword in travel_keywords if keyword in content_lower)
        pattern_matches = sum(1 for pattern in self._travel_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        if keyword_count >= 2 or pattern_matches >= 1:
            non_travel_keywords = ['movie', 'recipe', 'cooking', 'weather', 'news', 'product', 'code']
            non_travel_count = sum(1 for keyword in non_travel_keywords if keyword in content_lower)
            return non_travel_count == 0
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not travel-related", self.name)
            travel_info = self._extract_travel_info(content)
            formatted_html = self._generate_travel_card_html(travel_info, context)
            css_classes = self._get_css_classes(context)
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.TRAVEL,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "destination": travel_info.destination.name,
                    "country": travel_info.destination.country,
                    "has_activities": len(travel_info.activities) > 0,
                    "has_accommodations": len(travel_info.accommodations) > 0,
                    "has_tips": len(travel_info.tips) > 0,
                    "duration": travel_info.total_duration,
                    "budget": travel_info.estimated_budget
                },
                css_classes=css_classes,
                has_images=True,
                has_interactive_elements=len(travel_info.activities) > 0 or len(travel_info.accommodations) > 0
            )
        except Exception as e:
            self.logger.error(f"Travel formatting failed: {e}")
            raise FormattingError(f"Failed to format travel content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        return ["typography", "spacing", "colors", "cards", "icons", "badges", "buttons", "links", "gradients", "images"]
    
    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.TRAVEL]
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        if not self.can_format(content, context):
            return 0.0
        score = 0.0
        content_lower = content.lower()
        if context.detected_content_type == ContentType.TRAVEL:
            score += 0.4
        pattern_matches = sum(1 for pattern in self._travel_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        travel_keywords = ['travel', 'trip', 'vacation', 'destination', 'itinerary', 'hotel', 'flight', 'tour']
        keyword_matches = sum(1 for keyword in travel_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.1, 0.3)
        return min(score, 1.0)
    
    def _extract_travel_info(self, content: str) -> TravelInfo:
        destination = self._extract_destination(content)
        travel_info = TravelInfo(destination=destination)
        travel_info.activities = self._extract_activities(content)
        travel_info.accommodations = self._extract_accommodations(content)
        travel_info.tips = self._extract_travel_tips(content)
        travel_info.total_duration = self._extract_duration(content)
        travel_info.estimated_budget = self._extract_budget(content)
        return travel_info
    
    def _extract_destination(self, content: str) -> TravelDestination:
        destination = TravelDestination(name="Unknown Destination")
        destination_patterns = [
            r'(?i)(?:travel|trip|visit|go)\s+to\s+([A-Z][a-zA-Z\s,]+?)(?:\s*[:\-,]|\s*is|\s*offers|$)',
            r'(?i)(?:destination|place)\s*[:\-]?\s*([A-Z][a-zA-Z\s,]+?)(?:\s*[:\-,]|$)',
            r'(?i)(?:in|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\s*(?:is|has|offers|features))',
        ]
        for pattern in destination_patterns:
            match = re.search(pattern, content)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'\s*(?:travel|trip|visit|destination|place|city|country|:)\s*$', '', name, flags=re.IGNORECASE)
                name = re.sub(r'[:\-,]\s*$', '', name)
                if len(name) > 2 and not name.lower() in ['travel', 'trip', 'destination', 'place']:
                    destination.name = name
                    break
        country_patterns = [
            r'(?i)(?:in|at)\s+([A-Z][a-zA-Z\s]+),\s*([A-Z][a-zA-Z\s]+)',
            r'(?i)(?:country|nation)[:\-]?\s*([A-Z][a-zA-Z\s]+)',
        ]
        for pattern in country_patterns:
            match = re.search(pattern, content)
            if match:
                if len(match.groups()) == 2:
                    destination.country = match.group(2).strip()
                else:
                    destination.country = match.group(1).strip()
                break
        desc_patterns = [
            rf'(?i){re.escape(destination.name)}\s+(?:is|offers|features|has)\s+([^.]+\.)',
            r'(?i)(?:known for|famous for)\s+([^.]+\.)',
        ]
        for pattern in desc_patterns:
            match = re.search(pattern, content)
            if match:
                description = match.group(1).strip()
                if len(description) > 10:
                    destination.description = description
                    break
        return destination
    
    def _extract_activities(self, content: str) -> List[TravelActivity]:
        activities = []
        activity_patterns = [
            r'(?i)(?:activities|things to do|attractions)[:\-]\s*([^.]+\.)',
            r'(?i)(?:must visit|must see|don\'t miss)[:\-]\s*([^.]+\.)',
        ]
        for pattern in activity_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                activity_items = re.split(r'[,;]\s*|\n\s*[-•]\s*', match)
                for item in activity_items:
                    item = item.strip()
                    if len(item) > 3 and not item.endswith('.'):
                        activity_type = self._determine_activity_type(item)
                        activity = TravelActivity(name=item, type=activity_type, description=item)
                        activities.append(activity)
        return activities
    
    def _determine_activity_type(self, activity_name: str) -> str:
        activity_lower = activity_name.lower()
        type_keywords = {
            'sightseeing': ['museum', 'monument', 'landmark', 'cathedral', 'church', 'temple', 'palace', 'castle'],
            'cultural': ['theater', 'opera', 'concert', 'festival', 'market', 'bazaar'],
            'adventure': ['hiking', 'climbing', 'trekking', 'safari', 'diving', 'snorkeling'],
            'beach': ['beach', 'coast', 'seaside', 'swimming', 'sunbathing'],
            'food': ['restaurant', 'cafe', 'food', 'dining', 'lunch', 'dinner', 'breakfast'],
            'shopping': ['shop', 'shopping', 'mall', 'boutique', 'store'],
            'nature': ['park', 'garden', 'forest', 'mountain', 'lake', 'river', 'waterfall'],
        }
        for activity_type, keywords in type_keywords.items():
            if any(keyword in activity_lower for keyword in keywords):
                return activity_type
        return 'sightseeing'
    
    def _extract_accommodations(self, content: str) -> List[TravelAccommodation]:
        accommodations = []
        accommodation_patterns = [
            r'(?i)(?:hotel|resort|hostel|accommodation|stay|lodging)[:\-]\s*([^.]+\.)',
            r'(?i)(?:where to stay|recommended hotels)[:\-]\s*([^.]+\.)',
        ]
        for pattern in accommodation_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                accommodation_items = re.split(r'[,;]\s*|\n\s*[-•]\s*', match)
                for item in accommodation_items:
                    item = item.strip()
                    if len(item) > 3:
                        acc_type = self._determine_accommodation_type(item)
                        price_match = re.search(r'(\$\d+[-/]\$\d+|\$\d+|\d+[-/]\d+\s*(?:USD|EUR|per night))', item)
                        price_range = price_match.group(1) if price_match else None
                        accommodation = TravelAccommodation(name=item, type=acc_type, price_range=price_range)
                        accommodations.append(accommodation)
        return accommodations
    
    def _determine_accommodation_type(self, accommodation_name: str) -> str:
        acc_lower = accommodation_name.lower()
        type_keywords = {
            'hotel': ['hotel', 'inn'],
            'resort': ['resort', 'spa'],
            'hostel': ['hostel', 'backpacker'],
            'apartment': ['apartment', 'flat', 'airbnb'],
        }
        for acc_type, keywords in type_keywords.items():
            if any(keyword in acc_lower for keyword in keywords):
                return acc_type
        return 'hotel'
    
    def _extract_travel_tips(self, content: str) -> List[TravelTip]:
        tips = []
        tip_patterns = [
            r'(?i)(?:tip|advice|recommendation)[:\-]\s*([^.]+\.)',
            r'(?i)(?:important|remember|note)[:\-]\s*([^.]+\.)',
        ]
        for pattern in tip_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                tip_text = match.strip()
                if len(tip_text) > 10:
                    category = self._determine_tip_category(tip_text)
                    tip = TravelTip(
                        category=category,
                        title=tip_text[:50] + "..." if len(tip_text) > 50 else tip_text,
                        description=tip_text
                    )
                    tips.append(tip)
        return tips
    
    def _determine_tip_category(self, tip_text: str) -> str:
        tip_lower = tip_text.lower()
        category_keywords = {
            'safety': ['safe', 'danger', 'crime', 'security', 'emergency', 'police'],
            'budget': ['money', 'cost', 'price', 'budget', 'cheap', 'expensive', 'save'],
            'cultural': ['culture', 'custom', 'tradition', 'local', 'etiquette', 'respect'],
        }
        for category, keywords in category_keywords.items():
            if any(keyword in tip_lower for keyword in keywords):
                return category
        return 'general'
    
    def _extract_duration(self, content: str) -> Optional[str]:
        duration_patterns = [
            r'(?i)(?:duration|length|trip)\s*[:\-]?\s*(\d+\s*(?:days?|weeks?|months?))',
            r'(?i)(\d+\s*(?:day|week|month))\s+(?:trip|vacation|holiday)',
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_budget(self, content: str) -> Optional[str]:
        budget_patterns = [
            r'(?i)budget[:\-]?\s*(\$\d+(?:,\d+)?(?:\s*[-/]\s*\$\d+(?:,\d+)?)?)',
            r'(?i)cost[:\-]?\s*(\$\d+(?:,\d+)?(?:\s*[-/]\s*\$\d+(?:,\d+)?)?)',
        ]
        for pattern in budget_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return None
    
    def _generate_travel_card_html(self, travel_info: TravelInfo, context: ResponseContext) -> str:
        theme_name = context.theme_context.get('current_theme', 'light')
        html_parts = []
        html_parts.append('<div class="travel-card response-card">')
        html_parts.append('<div class="travel-header">')
        html_parts.append(f'<h2 class="travel-destination">🌍 {self._escape_html(travel_info.destination.name)}</h2>')
        if travel_info.destination.country:
            html_parts.append(f'<span class="travel-country">{self._escape_html(travel_info.destination.country)}</span>')
        html_parts.append('</div>')
        if travel_info.destination.description:
            html_parts.append('<div class="destination-info">')
            html_parts.append(f'<div class="destination-description">{self._escape_html(travel_info.destination.description)}</div>')
            html_parts.append('</div>')
        if travel_info.total_duration or travel_info.estimated_budget:
            html_parts.append('<div class="trip-overview">')
            html_parts.append('<h3 class="section-title">📋 Trip Overview</h3>')
            html_parts.append('<div class="overview-grid">')
            if travel_info.total_duration:
                html_parts.append(f'<div class="overview-item"><span class="overview-icon">⏱️</span><span class="overview-label">Duration</span><span class="overview-value">{self._escape_html(travel_info.total_duration)}</span></div>')
            if travel_info.estimated_budget:
                html_parts.append(f'<div class="overview-item"><span class="overview-icon">💰</span><span class="overview-label">Budget</span><span class="overview-value">{self._escape_html(travel_info.estimated_budget)}</span></div>')
            html_parts.append('</div>')
            html_parts.append('</div>')
        if travel_info.activities:
            html_parts.append('<div class="travel-activities">')
            html_parts.append('<h3 class="section-title">🎯 Activities & Attractions</h3>')
            html_parts.append('<div class="activities-grid">')
            for activity in travel_info.activities:
                icon = self._activity_icons.get(activity.type, '📍')
                html_parts.append('<div class="activity-card">')
                html_parts.append(f'<div class="activity-header">')
                html_parts.append(f'<span class="activity-icon">{icon}</span>')
                html_parts.append(f'<span class="activity-name">{self._escape_html(activity.name)}</span>')
                html_parts.append('</div>')
                html_parts.append('</div>')
            html_parts.append('</div>')
            html_parts.append('</div>')
        if travel_info.accommodations:
            html_parts.append('<div class="travel-accommodations">')
            html_parts.append('<h3 class="section-title">🏨 Accommodations</h3>')
            html_parts.append('<div class="accommodations-grid">')
            for accommodation in travel_info.accommodations:
                icon = self._accommodation_icons.get(accommodation.type, '🏨')
                html_parts.append('<div class="accommodation-card">')
                html_parts.append(f'<div class="accommodation-header">')
                html_parts.append(f'<span class="accommodation-icon">{icon}</span>')
                html_parts.append(f'<span class="accommodation-name">{self._escape_html(accommodation.name)}</span>')
                html_parts.append('</div>')
                if accommodation.price_range:
                    html_parts.append(f'<div class="accommodation-price">💰 {self._escape_html(accommodation.price_range)}</div>')
                html_parts.append('</div>')
            html_parts.append('</div>')
            html_parts.append('</div>')
        if travel_info.tips:
            html_parts.append('<div class="travel-tips">')
            html_parts.append('<h3 class="section-title">💡 Travel Tips</h3>')
            for tip in travel_info.tips:
                icon = self._tip_icons.get(tip.category, 'ℹ️')
                html_parts.append(f'<div class="travel-tip">')
                html_parts.append(f'<div class="tip-header">{icon} {tip.category.title()} Tip</div>')
                html_parts.append(f'<div class="tip-description">{self._escape_html(tip.description)}</div>')
                html_parts.append('</div>')
            html_parts.append('</div>')
        html_parts.append(self._generate_theme_styles(theme_name))
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    def _generate_theme_styles(self, theme_name: str) -> str:
        if theme_name == 'dark':
            bg_color = '#2d3748'
            text_color = '#e2e8f0'
            accent_color = '#4299e1'
            border_color = '#4a5568'
        else:
            bg_color = '#ffffff'
            text_color = '#2d3748'
            accent_color = '#3182ce'
            border_color = '#e2e8f0'
        return f'''
        <style>
        .travel-card {{
            background: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .travel-header {{
            border-bottom: 2px solid {accent_color};
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .travel-destination {{
            font-size: 1.8em;
            font-weight: bold;
            margin: 0 0 8px 0;
            color: {accent_color};
        }}
        .section-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin: 24px 0 16px 0;
            color: {accent_color};
            border-bottom: 1px solid {border_color};
            padding-bottom: 8px;
        }}
        .activities-grid, .accommodations-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}
        .activity-card, .accommodation-card {{
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 16px;
            background: rgba(66, 153, 225, 0.05);
        }}
        .activity-header, .accommodation-header {{
            display: flex;
            align-items: center;
            font-weight: bold;
        }}
        .activity-icon, .accommodation-icon {{
            margin-right: 8px;
            font-size: 1.2em;
        }}
        .travel-tip {{
            border-left: 4px solid {accent_color};
            padding: 12px 16px;
            margin: 8px 0;
            background: rgba(66, 153, 225, 0.1);
            border-radius: 0 6px 6px 0;
        }}
        .tip-header {{
            font-weight: bold;
            margin-bottom: 4px;
        }}
        @media (max-width: 768px) {{
            .activities-grid, .accommodations-grid {{
                grid-template-columns: 1fr;
            }}
            .travel-card {{
                padding: 16px;
                margin: 8px 0;
            }}
        }}
        </style>
        '''
    
    def _get_css_classes(self, context: ResponseContext) -> List[str]:
        classes = ["response-travel", "formatted-response", "travel-card"]
        theme_name = context.theme_context.get('current_theme', 'light')
        classes.append(f"theme-{theme_name}")
        return classes
    
    def _escape_html(self, text: str) -> str:
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))