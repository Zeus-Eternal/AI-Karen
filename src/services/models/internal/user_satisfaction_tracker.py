"""
User Satisfaction Tracking and Feedback Collection System

This module provides comprehensive user satisfaction tracking, feedback collection,
and analysis capabilities for the intelligent response optimization system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
import threading

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback"""
    RATING = "rating"
    THUMBS_UP_DOWN = "thumbs_up_down"
    DETAILED_FEEDBACK = "detailed_feedback"
    IMPLICIT_BEHAVIOR = "implicit_behavior"
    FOLLOW_UP_QUESTION = "follow_up_question"


class SatisfactionLevel(Enum):
    """User satisfaction levels"""
    VERY_DISSATISFIED = 1
    DISSATISFIED = 2
    NEUTRAL = 3
    SATISFIED = 4
    VERY_SATISFIED = 5


class BehaviorSignal(Enum):
    """Implicit behavior signals"""
    QUICK_FOLLOW_UP = "quick_follow_up"
    COPY_RESPONSE = "copy_response"
    SHARE_RESPONSE = "share_response"
    BOOKMARK_RESPONSE = "bookmark_response"
    IMMEDIATE_EXIT = "immediate_exit"
    LONG_READ_TIME = "long_read_time"
    SCROLL_THROUGH_RESPONSE = "scroll_through_response"
    CLICK_LINKS = "click_links"
    REGENERATE_REQUEST = "regenerate_request"


@dataclass
class UserFeedback:
    """User feedback data"""
    feedback_id: str
    response_id: str
    user_id: str
    session_id: str
    feedback_type: FeedbackType
    timestamp: datetime
    rating: Optional[int] = None  # 1-5 scale
    thumbs_up: Optional[bool] = None
    detailed_comment: Optional[str] = None
    behavior_signals: List[BehaviorSignal] = None
    response_time_when_feedback: float = 0.0
    response_length: int = 0
    model_used: str = ""
    optimizations_applied: List[str] = None
    context_tags: List[str] = None
    
    def __post_init__(self):
        if self.behavior_signals is None:
            self.behavior_signals = []
        if self.optimizations_applied is None:
            self.optimizations_applied = []
        if self.context_tags is None:
            self.context_tags = []


@dataclass
class SatisfactionMetrics:
    """Aggregated satisfaction metrics"""
    period_start: datetime
    period_end: datetime
    total_feedback_count: int
    avg_rating: float
    satisfaction_distribution: Dict[SatisfactionLevel, int]
    thumbs_up_percentage: float
    net_promoter_score: Optional[float]
    common_complaints: List[Tuple[str, int]]
    common_praise: List[Tuple[str, int]]
    satisfaction_by_model: Dict[str, float]
    satisfaction_by_optimization: Dict[str, float]
    behavior_signal_frequency: Dict[BehaviorSignal, int]
    improvement_suggestions: List[str]


@dataclass
class FeedbackAnalysis:
    """Analysis of user feedback patterns"""
    feedback_trend: str  # IMPROVING, DECLINING, STABLE
    key_issues: List[str]
    positive_patterns: List[str]
    model_performance_ranking: List[Tuple[str, float]]
    optimization_effectiveness: Dict[str, float]
    user_segment_insights: Dict[str, Dict[str, Any]]
    actionable_recommendations: List[str]


class UserSatisfactionTracker:
    """Comprehensive user satisfaction tracking system"""
    
    def __init__(self, max_feedback_history: int = 50000):
        self.max_feedback_history = max_feedback_history
        self.feedback_history: deque = deque(maxlen=max_feedback_history)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.lock = threading.Lock()
        
        # Feedback collection settings
        self.implicit_feedback_enabled = True
        self.feedback_request_frequency = 0.1  # Request explicit feedback for 10% of responses
        self.satisfaction_threshold = 3.0  # Below this is considered dissatisfied
        
        # Start background analysis
        self._start_background_analysis()
    
    def start_session_tracking(self, session_id: str, user_id: str) -> None:
        """Start tracking user satisfaction for a session"""
        with self.lock:
            self.active_sessions[session_id] = {
                'user_id': user_id,
                'start_time': datetime.now(),
                'responses_count': 0,
                'feedback_given': 0,
                'behavior_signals': [],
                'last_response_time': None,
                'cumulative_satisfaction': []
            }
    
    def record_response_delivered(
        self, 
        response_id: str, 
        session_id: str, 
        response_time: float,
        response_length: int,
        model_used: str,
        optimizations_applied: List[str] = None
    ) -> None:
        """Record that a response was delivered to track implicit feedback"""
        if optimizations_applied is None:
            optimizations_applied = []
            
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session['responses_count'] += 1
                session['last_response_time'] = datetime.now()
                session['last_response_id'] = response_id
                session['last_response_data'] = {
                    'response_time': response_time,
                    'response_length': response_length,
                    'model_used': model_used,
                    'optimizations_applied': optimizations_applied
                }
    
    def record_explicit_feedback(
        self,
        response_id: str,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        rating: Optional[int] = None,
        thumbs_up: Optional[bool] = None,
        detailed_comment: Optional[str] = None,
        context_tags: List[str] = None
    ) -> str:
        """Record explicit user feedback"""
        feedback_id = self._generate_feedback_id()
        
        # Get response data from session
        response_data = {}
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if 'last_response_data' in session:
                    response_data = session['last_response_data']
                session['feedback_given'] += 1
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            response_id=response_id,
            user_id=user_id,
            session_id=session_id,
            feedback_type=feedback_type,
            timestamp=datetime.now(),
            rating=rating,
            thumbs_up=thumbs_up,
            detailed_comment=detailed_comment,
            response_time_when_feedback=response_data.get('response_time', 0.0),
            response_length=response_data.get('response_length', 0),
            model_used=response_data.get('model_used', ''),
            optimizations_applied=response_data.get('optimizations_applied', []),
            context_tags=context_tags or []
        )
        
        with self.lock:
            self.feedback_history.append(feedback)
            
            # Update user profile
            user_profile = self.user_profiles[user_id]
            if 'feedback_count' not in user_profile:
                user_profile['feedback_count'] = 0
                user_profile['avg_rating'] = 0.0
                user_profile['total_rating'] = 0.0
            
            user_profile['feedback_count'] += 1
            if rating:
                user_profile['total_rating'] += rating
                user_profile['avg_rating'] = user_profile['total_rating'] / user_profile['feedback_count']
            
            user_profile['last_feedback'] = datetime.now()
        
        logger.info(f"Recorded explicit feedback: {feedback_type.value} for response {response_id}")
        return feedback_id
    
    def record_behavior_signal(
        self, 
        session_id: str, 
        signal: BehaviorSignal, 
        response_id: Optional[str] = None
    ) -> None:
        """Record implicit behavior signal"""
        if not self.implicit_feedback_enabled:
            return
            
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session['behavior_signals'].append({
                    'signal': signal,
                    'timestamp': datetime.now(),
                    'response_id': response_id or session.get('last_response_id')
                })
                
                # Convert behavior signals to implicit satisfaction scores
                satisfaction_score = self._behavior_to_satisfaction_score(signal)
                if satisfaction_score:
                    session['cumulative_satisfaction'].append(satisfaction_score)
    
    def get_satisfaction_metrics(self, time_period: timedelta) -> SatisfactionMetrics:
        """Get aggregated satisfaction metrics for a time period"""
        cutoff_time = datetime.now() - time_period
        
        with self.lock:
            relevant_feedback = [
                f for f in self.feedback_history 
                if f.timestamp >= cutoff_time
            ]
        
        if not relevant_feedback:
            return SatisfactionMetrics(
                period_start=cutoff_time,
                period_end=datetime.now(),
                total_feedback_count=0,
                avg_rating=0.0,
                satisfaction_distribution={},
                thumbs_up_percentage=0.0,
                net_promoter_score=None,
                common_complaints=[],
                common_praise=[],
                satisfaction_by_model={},
                satisfaction_by_optimization={},
                behavior_signal_frequency={},
                improvement_suggestions=[]
            )
        
        # Calculate metrics
        ratings = [f.rating for f in relevant_feedback if f.rating is not None]
        thumbs_feedback = [f.thumbs_up for f in relevant_feedback if f.thumbs_up is not None]
        
        avg_rating = statistics.mean(ratings) if ratings else 0.0
        thumbs_up_percentage = (sum(thumbs_feedback) / len(thumbs_feedback) * 100) if thumbs_feedback else 0.0
        
        # Satisfaction distribution
        satisfaction_distribution = defaultdict(int)
        for rating in ratings:
            if rating <= 2:
                satisfaction_distribution[SatisfactionLevel.DISSATISFIED] += 1
            elif rating == 3:
                satisfaction_distribution[SatisfactionLevel.NEUTRAL] += 1
            else:
                satisfaction_distribution[SatisfactionLevel.SATISFIED] += 1
        
        # Net Promoter Score (9-10 promoters, 0-6 detractors, 7-8 passive)
        # Adapting 1-5 scale: 5 = promoter, 1-2 = detractor, 3-4 = passive
        promoters = len([r for r in ratings if r == 5])
        detractors = len([r for r in ratings if r <= 2])
        nps = ((promoters - detractors) / len(ratings) * 100) if ratings else None
        
        # Analyze comments
        complaints, praise = self._analyze_feedback_comments(relevant_feedback)
        
        # Satisfaction by model
        satisfaction_by_model = defaultdict(list)
        for feedback in relevant_feedback:
            if feedback.rating and feedback.model_used:
                satisfaction_by_model[feedback.model_used].append(feedback.rating)
        
        satisfaction_by_model = {
            model: statistics.mean(ratings) 
            for model, ratings in satisfaction_by_model.items()
        }
        
        # Satisfaction by optimization
        satisfaction_by_optimization = defaultdict(list)
        for feedback in relevant_feedback:
            if feedback.rating:
                for opt in feedback.optimizations_applied:
                    satisfaction_by_optimization[opt].append(feedback.rating)
        
        satisfaction_by_optimization = {
            opt: statistics.mean(ratings) 
            for opt, ratings in satisfaction_by_optimization.items()
        }
        
        # Behavior signal frequency
        behavior_signal_frequency = defaultdict(int)
        for feedback in relevant_feedback:
            for signal in feedback.behavior_signals:
                behavior_signal_frequency[signal] += 1
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            avg_rating, satisfaction_by_model, satisfaction_by_optimization, complaints
        )
        
        return SatisfactionMetrics(
            period_start=cutoff_time,
            period_end=datetime.now(),
            total_feedback_count=len(relevant_feedback),
            avg_rating=avg_rating,
            satisfaction_distribution=dict(satisfaction_distribution),
            thumbs_up_percentage=thumbs_up_percentage,
            net_promoter_score=nps,
            common_complaints=complaints,
            common_praise=praise,
            satisfaction_by_model=satisfaction_by_model,
            satisfaction_by_optimization=satisfaction_by_optimization,
            behavior_signal_frequency=dict(behavior_signal_frequency),
            improvement_suggestions=improvement_suggestions
        )
    
    def analyze_feedback_trends(self, time_period: timedelta) -> FeedbackAnalysis:
        """Analyze feedback trends and patterns"""
        cutoff_time = datetime.now() - time_period
        
        with self.lock:
            relevant_feedback = [
                f for f in self.feedback_history 
                if f.timestamp >= cutoff_time
            ]
        
        if not relevant_feedback:
            return FeedbackAnalysis(
                feedback_trend="STABLE",
                key_issues=[],
                positive_patterns=[],
                model_performance_ranking=[],
                optimization_effectiveness={},
                user_segment_insights={},
                actionable_recommendations=[]
            )
        
        # Analyze trend
        feedback_trend = self._analyze_satisfaction_trend(relevant_feedback)
        
        # Identify key issues and positive patterns
        key_issues = self._identify_key_issues(relevant_feedback)
        positive_patterns = self._identify_positive_patterns(relevant_feedback)
        
        # Model performance ranking
        model_performance = defaultdict(list)
        for feedback in relevant_feedback:
            if feedback.rating and feedback.model_used:
                model_performance[feedback.model_used].append(feedback.rating)
        
        model_performance_ranking = [
            (model, statistics.mean(ratings))
            for model, ratings in model_performance.items()
        ]
        model_performance_ranking.sort(key=lambda x: x[1], reverse=True)
        
        # Optimization effectiveness
        optimization_effectiveness = {}
        for feedback in relevant_feedback:
            if feedback.rating:
                for opt in feedback.optimizations_applied:
                    if opt not in optimization_effectiveness:
                        optimization_effectiveness[opt] = []
                    optimization_effectiveness[opt].append(feedback.rating)
        
        optimization_effectiveness = {
            opt: statistics.mean(ratings)
            for opt, ratings in optimization_effectiveness.items()
        }
        
        # User segment insights
        user_segment_insights = self._analyze_user_segments(relevant_feedback)
        
        # Actionable recommendations
        actionable_recommendations = self._generate_actionable_recommendations(
            feedback_trend, key_issues, model_performance_ranking, optimization_effectiveness
        )
        
        return FeedbackAnalysis(
            feedback_trend=feedback_trend,
            key_issues=key_issues,
            positive_patterns=positive_patterns,
            model_performance_ranking=model_performance_ranking,
            optimization_effectiveness=optimization_effectiveness,
            user_segment_insights=user_segment_insights,
            actionable_recommendations=actionable_recommendations
        )
    
    def should_request_feedback(self, session_id: str) -> bool:
        """Determine if we should request explicit feedback from user"""
        import random
        
        with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Don't request too frequently
            if session['feedback_given'] > 0 and session['responses_count'] < 5:
                return False
            
            # Request based on frequency setting
            return random.random() < self.feedback_request_frequency
    
    def get_user_satisfaction_profile(self, user_id: str) -> Dict[str, Any]:
        """Get satisfaction profile for a specific user"""
        with self.lock:
            profile = self.user_profiles.get(user_id, {})
            
            # Get recent feedback
            recent_feedback = [
                f for f in self.feedback_history 
                if f.user_id == user_id and f.timestamp >= datetime.now() - timedelta(days=30)
            ]
            
            profile['recent_feedback_count'] = len(recent_feedback)
            if recent_feedback:
                ratings = [f.rating for f in recent_feedback if f.rating]
                profile['recent_avg_rating'] = statistics.mean(ratings) if ratings else None
                profile['recent_feedback_types'] = list(set(f.feedback_type.value for f in recent_feedback))
            
            return profile
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID"""
        import uuid
        return f"feedback_{uuid.uuid4().hex[:12]}"
    
    def _behavior_to_satisfaction_score(self, signal: BehaviorSignal) -> Optional[float]:
        """Convert behavior signal to implicit satisfaction score"""
        signal_scores = {
            BehaviorSignal.COPY_RESPONSE: 4.5,
            BehaviorSignal.SHARE_RESPONSE: 5.0,
            BehaviorSignal.BOOKMARK_RESPONSE: 4.5,
            BehaviorSignal.LONG_READ_TIME: 4.0,
            BehaviorSignal.SCROLL_THROUGH_RESPONSE: 3.5,
            BehaviorSignal.CLICK_LINKS: 4.0,
            BehaviorSignal.IMMEDIATE_EXIT: 1.5,
            BehaviorSignal.QUICK_FOLLOW_UP: 2.0,
            BehaviorSignal.REGENERATE_REQUEST: 2.0
        }
        return signal_scores.get(signal)
    
    def _analyze_feedback_comments(self, feedback_list: List[UserFeedback]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        """Analyze feedback comments to extract common complaints and praise"""
        complaints = defaultdict(int)
        praise = defaultdict(int)
        
        # Simple keyword-based analysis (could be enhanced with NLP)
        complaint_keywords = ['slow', 'wrong', 'bad', 'error', 'confusing', 'unhelpful', 'incomplete']
        praise_keywords = ['fast', 'good', 'helpful', 'clear', 'accurate', 'complete', 'excellent']
        
        for feedback in feedback_list:
            if feedback.detailed_comment:
                comment_lower = feedback.detailed_comment.lower()
                
                for keyword in complaint_keywords:
                    if keyword in comment_lower:
                        complaints[keyword] += 1
                
                for keyword in praise_keywords:
                    if keyword in comment_lower:
                        praise[keyword] += 1
        
        # Sort by frequency
        complaints = sorted(complaints.items(), key=lambda x: x[1], reverse=True)[:5]
        praise = sorted(praise.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return complaints, praise
    
    def _generate_improvement_suggestions(
        self, 
        avg_rating: float, 
        satisfaction_by_model: Dict[str, float],
        satisfaction_by_optimization: Dict[str, float],
        complaints: List[Tuple[str, int]]
    ) -> List[str]:
        """Generate improvement suggestions based on satisfaction data"""
        suggestions = []
        
        if avg_rating < self.satisfaction_threshold:
            suggestions.append(f"Overall satisfaction is low ({avg_rating:.1f}/5.0) - investigate primary causes")
        
        # Model-specific suggestions
        if satisfaction_by_model:
            worst_model = min(satisfaction_by_model.items(), key=lambda x: x[1])
            best_model = max(satisfaction_by_model.items(), key=lambda x: x[1])
            
            if worst_model[1] < self.satisfaction_threshold:
                suggestions.append(f"Model '{worst_model[0]}' has low satisfaction ({worst_model[1]:.1f}) - consider optimization or replacement")
            
            if best_model[1] - worst_model[1] > 1.0:
                suggestions.append(f"Consider routing more traffic to high-performing model '{best_model[0]}' ({best_model[1]:.1f} rating)")
        
        # Optimization-specific suggestions
        if satisfaction_by_optimization:
            ineffective_opts = [opt for opt, rating in satisfaction_by_optimization.items() if rating < self.satisfaction_threshold]
            if ineffective_opts:
                suggestions.append(f"Review optimization strategies: {', '.join(ineffective_opts)} show low satisfaction")
        
        # Complaint-based suggestions
        if complaints:
            top_complaint = complaints[0]
            if top_complaint[0] == 'slow':
                suggestions.append("Address response speed issues - consider caching and optimization improvements")
            elif top_complaint[0] == 'wrong':
                suggestions.append("Improve response accuracy - review model selection and training data")
            elif top_complaint[0] == 'confusing':
                suggestions.append("Enhance response clarity - improve content formatting and structure")
        
        return suggestions
    
    def _analyze_satisfaction_trend(self, feedback_list: List[UserFeedback]) -> str:
        """Analyze satisfaction trend over time"""
        if len(feedback_list) < 10:
            return "STABLE"
        
        # Sort by timestamp
        feedback_list.sort(key=lambda f: f.timestamp)
        
        # Split into first and second half
        mid_point = len(feedback_list) // 2
        first_half = feedback_list[:mid_point]
        second_half = feedback_list[mid_point:]
        
        first_ratings = [f.rating for f in first_half if f.rating]
        second_ratings = [f.rating for f in second_half if f.rating]
        
        if not first_ratings or not second_ratings:
            return "STABLE"
        
        first_avg = statistics.mean(first_ratings)
        second_avg = statistics.mean(second_ratings)
        
        difference = second_avg - first_avg
        
        if difference > 0.3:
            return "IMPROVING"
        elif difference < -0.3:
            return "DECLINING"
        else:
            return "STABLE"
    
    def _identify_key_issues(self, feedback_list: List[UserFeedback]) -> List[str]:
        """Identify key issues from feedback"""
        issues = []
        
        # Low rating patterns
        low_ratings = [f for f in feedback_list if f.rating and f.rating <= 2]
        if len(low_ratings) > len(feedback_list) * 0.2:  # More than 20% low ratings
            issues.append("High frequency of low satisfaction ratings")
        
        # Behavior signal patterns
        negative_signals = [BehaviorSignal.IMMEDIATE_EXIT, BehaviorSignal.REGENERATE_REQUEST]
        negative_count = sum(
            len([s for s in f.behavior_signals if s in negative_signals])
            for f in feedback_list
        )
        
        if negative_count > len(feedback_list) * 0.3:
            issues.append("High frequency of negative user behaviors")
        
        return issues
    
    def _identify_positive_patterns(self, feedback_list: List[UserFeedback]) -> List[str]:
        """Identify positive patterns from feedback"""
        patterns = []
        
        # High rating patterns
        high_ratings = [f for f in feedback_list if f.rating and f.rating >= 4]
        if len(high_ratings) > len(feedback_list) * 0.6:  # More than 60% high ratings
            patterns.append("Strong overall user satisfaction")
        
        # Positive behavior signals
        positive_signals = [BehaviorSignal.COPY_RESPONSE, BehaviorSignal.SHARE_RESPONSE, BehaviorSignal.BOOKMARK_RESPONSE]
        positive_count = sum(
            len([s for s in f.behavior_signals if s in positive_signals])
            for f in feedback_list
        )
        
        if positive_count > len(feedback_list) * 0.2:
            patterns.append("High engagement with response content")
        
        return patterns
    
    def _analyze_user_segments(self, feedback_list: List[UserFeedback]) -> Dict[str, Dict[str, Any]]:
        """Analyze satisfaction by user segments"""
        segments = defaultdict(lambda: {'ratings': [], 'count': 0})
        
        # Segment by feedback frequency (power users vs casual users)
        user_feedback_counts = defaultdict(int)
        for feedback in feedback_list:
            user_feedback_counts[feedback.user_id] += 1
        
        for feedback in feedback_list:
            user_feedback_count = user_feedback_counts[feedback.user_id]
            
            if user_feedback_count >= 5:
                segment = "power_users"
            else:
                segment = "casual_users"
            
            segments[segment]['count'] += 1
            if feedback.rating:
                segments[segment]['ratings'].append(feedback.rating)
        
        # Calculate averages
        for segment, data in segments.items():
            if data['ratings']:
                data['avg_rating'] = statistics.mean(data['ratings'])
            else:
                data['avg_rating'] = 0.0
        
        return dict(segments)
    
    def _generate_actionable_recommendations(
        self,
        trend: str,
        key_issues: List[str],
        model_performance: List[Tuple[str, float]],
        optimization_effectiveness: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if trend == "DECLINING":
            recommendations.append("URGENT: Satisfaction is declining - investigate recent changes and implement immediate improvements")
        elif trend == "IMPROVING":
            recommendations.append("Satisfaction is improving - identify and scale successful strategies")
        
        if key_issues:
            recommendations.append(f"Address key issues: {', '.join(key_issues)}")
        
        if model_performance and len(model_performance) > 1:
            best_model = model_performance[0]
            worst_model = model_performance[-1]
            
            if best_model[1] - worst_model[1] > 1.0:
                recommendations.append(f"Route more traffic from '{worst_model[0]}' to '{best_model[0]}' for better satisfaction")
        
        ineffective_optimizations = [
            opt for opt, rating in optimization_effectiveness.items() 
            if rating < 3.0
        ]
        
        if ineffective_optimizations:
            recommendations.append(f"Review and improve optimizations: {', '.join(ineffective_optimizations)}")
        
        return recommendations
    
    def _start_background_analysis(self) -> None:
        """Start background analysis thread"""
        def analyze():
            while True:
                try:
                    # Perform periodic analysis
                    metrics = self.get_satisfaction_metrics(timedelta(hours=1))
                    if metrics.avg_rating < 2.0 and metrics.total_feedback_count > 10:
                        logger.warning(f"Low satisfaction detected: {metrics.avg_rating:.1f}/5.0")
                    
                    time.sleep(300)  # Analyze every 5 minutes
                except Exception as e:
                    logger.error(f"Error in background satisfaction analysis: {e}")
                    time.sleep(600)  # Wait longer on error
        
        import time
        analysis_thread = threading.Thread(target=analyze, daemon=True)
        analysis_thread.start()


# Global user satisfaction tracker instance
satisfaction_tracker = UserSatisfactionTracker()