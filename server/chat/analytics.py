"""
Analytics module for conversation and message insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.orm import joinedload

from .models import (
    ChatConversation, ChatMessage, MessageAttachment, ChatProviderConfiguration
)

logger = logging.getLogger(__name__)


class ConversationAnalytics:
    """Analytics service for conversation and message insights."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_user_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a user."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Conversation analytics
            conversation_analytics = await self.get_conversation_analytics(user_id, days)
            
            # Message analytics
            message_analytics = await self.get_message_analytics(user_id, days)
            
            # Provider analytics
            provider_analytics = await self.get_provider_analytics(user_id, days)
            
            # Usage patterns
            usage_patterns = await self.get_usage_patterns(user_id, days)
            
            # Engagement metrics
            engagement_metrics = await self.get_engagement_metrics(user_id, days)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "conversation_analytics": conversation_analytics,
                "message_analytics": message_analytics,
                "provider_analytics": provider_analytics,
                "usage_patterns": usage_patterns,
                "engagement_metrics": engagement_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            raise
    
    async def get_conversation_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversation-specific analytics."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Basic conversation stats
            basic_stats = await self.db_session.execute(
                select(
                    func.count(ChatConversation.id).label('total_conversations'),
                    func.count(func.distinct(ChatConversation.provider_id)).label('unique_providers'),
                    func.avg(ChatConversation.message_count).label('avg_messages_per_conversation'),
                    func.sum(ChatConversation.message_count).label('total_messages'),
                    func.count(func.distinct(func.date(ChatConversation.created_at))).label('active_days')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
            )
            basic_result = basic_stats.first()
            
            # Conversation duration analytics
            duration_stats = await self.db_session.execute(
                select(
                    func.avg(
                        func.extract('epoch', ChatConversation.updated_at - ChatConversation.created_at)
                    ).label('avg_duration_seconds'),
                    func.min(
                        func.extract('epoch', ChatConversation.updated_at - ChatConversation.created_at)
                    ).label('min_duration_seconds'),
                    func.max(
                        func.extract('epoch', ChatConversation.updated_at - ChatConversation.created_at)
                    ).label('max_duration_seconds')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from,
                    ChatConversation.updated_at > ChatConversation.created_at
                ))
            )
            duration_result = duration_stats.first()
            
            # Daily conversation trends
            daily_trends = await self.db_session.execute(
                select(
                    func.date(ChatConversation.created_at).label('date'),
                    func.count(ChatConversation.id).label('conversations_created'),
                    func.count(func.distinct(ChatConversation.provider_id)).label('unique_providers')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .group_by(func.date(ChatConversation.created_at))
                .order_by('date')
            )
            daily_results = daily_trends.all()
            
            # Hourly conversation patterns
            hourly_patterns = await self.db_session.execute(
                select(
                    func.extract('hour', ChatConversation.created_at).label('hour'),
                    func.count(ChatConversation.id).label('conversations')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .group_by(func.extract('hour', ChatConversation.created_at))
                .order_by('hour')
            )
            hourly_results = hourly_patterns.all()
            
            return {
                "basic_stats": {
                    "total_conversations": basic_result.total_conversations or 0,
                    "unique_providers": basic_result.unique_providers or 0,
                    "average_messages_per_conversation": float(basic_result.avg_messages_per_conversation or 0),
                    "total_messages": basic_result.total_messages or 0,
                    "active_days": basic_result.active_days or 0
                },
                "duration_stats": {
                    "average_duration_seconds": float(duration_result.avg_duration_seconds or 0),
                    "minimum_duration_seconds": float(duration_result.min_duration_seconds or 0),
                    "maximum_duration_seconds": float(duration_result.max_duration_seconds or 0)
                } if duration_result else {
                    "average_duration_seconds": 0,
                    "minimum_duration_seconds": 0,
                    "maximum_duration_seconds": 0
                },
                "daily_trends": [
                    {
                        "date": result.date.isoformat(),
                        "conversations_created": result.conversations_created,
                        "unique_providers": result.unique_providers
                    }
                    for result in daily_results
                ],
                "hourly_patterns": [
                    {
                        "hour": int(result.hour),
                        "conversations": result.conversations
                    }
                    for result in hourly_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation analytics: {e}")
            raise
    
    async def get_message_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get message-specific analytics."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Message stats by role
            role_stats = await self.db_session.execute(
                select(
                    ChatMessage.role,
                    func.count(ChatMessage.id).label('count'),
                    func.avg(ChatMessage.token_count).label('avg_tokens'),
                    func.sum(ChatMessage.token_count).label('total_tokens'),
                    func.avg(ChatMessage.processing_time_ms).label('avg_processing_time'),
                    func.sum(ChatMessage.processing_time_ms).label('total_processing_time')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(ChatMessage.role)
            )
            role_results = role_stats.all()
            
            # Message length distribution
            length_distribution = await self.db_session.execute(
                select(
                    func.case(
                        (func.length(ChatMessage.content) < 100, 'short'),
                        (func.length(ChatMessage.content) < 500, 'medium'),
                        (func.length(ChatMessage.content) < 1000, 'long'),
                        else_='very_long'
                    ).label('length_category'),
                    func.count(ChatMessage.id).label('count')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(
                    func.case(
                        (func.length(ChatMessage.content) < 100, 'short'),
                        (func.length(ChatMessage.content) < 500, 'medium'),
                        (func.length(ChatMessage.content) < 1000, 'long'),
                        else_='very_long'
                    )
                )
                .order_by('count DESC')
            )
            length_results = length_distribution.all()
            
            # Attachment analytics
            attachment_analytics = await self.db_session.execute(
                select(
                    func.count(MessageAttachment.id).label('total_attachments'),
                    func.count(func.distinct(MessageAttachment.message_id)).label('messages_with_attachments'),
                    func.avg(MessageAttachment.file_size).label('avg_file_size'),
                    func.sum(MessageAttachment.file_size).label('total_size'),
                    func.count(func.distinct(MessageAttachment.mime_type)).label('unique_mime_types')
                )
                .join(ChatMessage)
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    MessageAttachment.created_at >= date_from
                ))
            )
            attachment_result = attachment_analytics.first()
            
            # MIME type distribution
            mime_distribution = await self.db_session.execute(
                select(
                    MessageAttachment.mime_type,
                    func.count(MessageAttachment.id).label('count'),
                    func.avg(MessageAttachment.file_size).label('avg_size')
                )
                .join(ChatMessage)
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    MessageAttachment.created_at >= date_from
                ))
                .group_by(MessageAttachment.mime_type)
                .order_by(desc('count'))
                .limit(10)
            )
            mime_results = mime_distribution.all()
            
            return {
                "role_stats": [
                    {
                        "role": result.role,
                        "count": result.count,
                        "average_tokens": float(result.avg_tokens or 0),
                        "total_tokens": result.total_tokens or 0,
                        "average_processing_time_ms": float(result.avg_processing_time or 0),
                        "total_processing_time_ms": result.total_processing_time or 0
                    }
                    for result in role_results
                ],
                "length_distribution": [
                    {
                        "category": result.length_category,
                        "count": result.count
                    }
                    for result in length_results
                ],
                "attachment_analytics": {
                    "total_attachments": attachment_result.total_attachments or 0,
                    "messages_with_attachments": attachment_result.messages_with_attachments or 0,
                    "average_file_size": float(attachment_result.avg_file_size or 0),
                    "total_size": attachment_result.total_size or 0,
                    "unique_mime_types": attachment_result.unique_mime_types or 0
                } if attachment_result else {
                    "total_attachments": 0,
                    "messages_with_attachments": 0,
                    "average_file_size": 0,
                    "total_size": 0,
                    "unique_mime_types": 0
                },
                "mime_type_distribution": [
                    {
                        "mime_type": result.mime_type,
                        "count": result.count,
                        "average_size": float(result.avg_size or 0)
                    }
                    for result in mime_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get message analytics: {e}")
            raise
    
    async def get_provider_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get provider-specific analytics."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Provider usage stats
            provider_stats = await self.db_session.execute(
                select(
                    ChatConversation.provider_id,
                    func.count(ChatConversation.id).label('conversation_count'),
                    func.sum(ChatConversation.message_count).label('total_messages'),
                    func.avg(ChatConversation.message_count).label('avg_messages_per_conversation'),
                    func.count(func.distinct(func.date(ChatConversation.created_at))).label('active_days')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .group_by(ChatConversation.provider_id)
                .order_by(desc('conversation_count'))
            )
            provider_results = provider_stats.all()
            
            # Provider performance metrics
            performance_metrics = await self.db_session.execute(
                select(
                    ChatMessage.provider_id,
                    func.count(ChatMessage.id).label('message_count'),
                    func.avg(ChatMessage.processing_time_ms).label('avg_processing_time'),
                    func.min(ChatMessage.processing_time_ms).label('min_processing_time'),
                    func.max(ChatMessage.processing_time_ms).label('max_processing_time'),
                    func.avg(ChatMessage.token_count).label('avg_tokens_per_message'),
                    func.sum(ChatMessage.token_count).label('total_tokens')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from,
                    ChatMessage.provider_id.isnot(None)
                ))
                .group_by(ChatMessage.provider_id)
                .order_by(desc('message_count'))
            )
            performance_results = performance_metrics.all()
            
            # Provider cost estimation (if available)
            cost_estimation = await self.db_session.execute(
                select(
                    ChatMessage.provider_id,
                    func.sum(
                        func.coalesce(
                            (ChatMessage.token_count * 0.002),  # Example pricing: $0.002 per 1K tokens
                            0
                        )
                    ).label('estimated_cost')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from,
                    ChatMessage.provider_id.isnot(None),
                    ChatMessage.token_count.isnot(None)
                ))
                .group_by(ChatMessage.provider_id)
                .order_by(desc('estimated_cost'))
            )
            cost_results = cost_estimation.all()
            
            return {
                "usage_stats": [
                    {
                        "provider_id": result.provider_id,
                        "conversation_count": result.conversation_count,
                        "total_messages": result.total_messages or 0,
                        "average_messages_per_conversation": float(result.avg_messages_per_conversation or 0),
                        "active_days": result.active_days
                    }
                    for result in provider_results
                ],
                "performance_metrics": [
                    {
                        "provider_id": result.provider_id,
                        "message_count": result.message_count,
                        "average_processing_time_ms": float(result.avg_processing_time or 0),
                        "minimum_processing_time_ms": int(result.min_processing_time or 0),
                        "maximum_processing_time_ms": int(result.max_processing_time or 0),
                        "average_tokens_per_message": float(result.avg_tokens_per_message or 0),
                        "total_tokens": result.total_tokens or 0
                    }
                    for result in performance_results
                ],
                "cost_estimation": [
                    {
                        "provider_id": result.provider_id,
                        "estimated_cost": float(result.estimated_cost or 0)
                    }
                    for result in cost_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get provider analytics: {e}")
            raise
    
    async def get_usage_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage patterns and trends."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Daily activity patterns
            daily_activity = await self.db_session.execute(
                select(
                    func.date(ChatMessage.created_at).label('date'),
                    func.count(ChatMessage.id).label('message_count'),
                    func.count(func.distinct(ChatMessage.conversation_id)).label('conversation_count'),
                    func.avg(ChatMessage.processing_time_ms).label('avg_processing_time')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(func.date(ChatMessage.created_at))
                .order_by('date')
            )
            daily_results = daily_activity.all()
            
            # Hourly activity patterns
            hourly_activity = await self.db_session.execute(
                select(
                    func.extract('hour', ChatMessage.created_at).label('hour'),
                    func.count(ChatMessage.id).label('message_count'),
                    func.count(func.distinct(ChatMessage.conversation_id)).label('conversation_count')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(func.extract('hour', ChatMessage.created_at))
                .order_by('hour')
            )
            hourly_results = hourly_activity.all()
            
            # Day of week patterns
            dow_patterns = await self.db_session.execute(
                select(
                    func.extract('dow', ChatMessage.created_at).label('day_of_week'),
                    func.count(ChatMessage.id).label('message_count'),
                    func.count(func.distinct(ChatMessage.conversation_id)).label('conversation_count')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
                .group_by(func.extract('dow', ChatMessage.created_at))
                .order_by('day_of_week')
            )
            dow_results = dow_patterns.all()
            
            # Conversation length distribution
            conv_length_dist = await self.db_session.execute(
                select(
                    func.case(
                        (ChatConversation.message_count < 5, 'very_short'),
                        (ChatConversation.message_count < 10, 'short'),
                        (ChatConversation.message_count < 20, 'medium'),
                        (ChatConversation.message_count < 50, 'long'),
                        else_='very_long'
                    ).label('length_category'),
                    func.count(ChatConversation.id).label('count')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .group_by(
                    func.case(
                        (ChatConversation.message_count < 5, 'very_short'),
                        (ChatConversation.message_count < 10, 'short'),
                        (ChatConversation.message_count < 20, 'medium'),
                        (ChatConversation.message_count < 50, 'long'),
                        else_='very_long'
                    )
                )
                .order_by('count DESC')
            )
            conv_length_results = conv_length_dist.all()
            
            return {
                "daily_activity": [
                    {
                        "date": result.date.isoformat(),
                        "message_count": result.message_count,
                        "conversation_count": result.conversation_count,
                        "average_processing_time_ms": float(result.avg_processing_time or 0)
                    }
                    for result in daily_results
                ],
                "hourly_activity": [
                    {
                        "hour": int(result.hour),
                        "message_count": result.message_count,
                        "conversation_count": result.conversation_count
                    }
                    for result in hourly_results
                ],
                "day_of_week_patterns": [
                    {
                        "day_of_week": int(result.day_of_week),
                        "message_count": result.message_count,
                        "conversation_count": result.conversation_count
                    }
                    for result in dow_results
                ],
                "conversation_length_distribution": [
                    {
                        "length_category": result.length_category,
                        "count": result.count
                    }
                    for result in conv_length_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage patterns: {e}")
            raise
    
    async def get_engagement_metrics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get engagement and retention metrics."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Active days calculation
            active_days_result = await self.db_session.execute(
                select(
                    func.count(func.distinct(func.date(ChatMessage.created_at))).label('active_days')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from
                ))
            )
            active_days = active_days_result.scalar() or 0
            
            # Conversation completion rate
            completion_stats = await self.db_session.execute(
                select(
                    func.count(ChatConversation.id).label('total_conversations'),
                    func.count(
                        func.case(
                            (ChatConversation.message_count >= 2, 1),
                            else_=None
                        )
                    ).label('completed_conversations')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
            )
            completion_result = completion_stats.first()
            
            # Average session duration (estimated)
            session_duration = await self.db_session.execute(
                select(
                    func.avg(
                        func.extract('epoch', 
                            func.coalesce(ChatConversation.updated_at, ChatConversation.created_at) - 
                            ChatConversation.created_at
                        )
                    ).label('avg_session_duration_seconds')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
            )
            duration_result = session_duration.first()
            
            # Message response time (user to assistant)
            response_time = await self.db_session.execute(
                select(
                    func.avg(
                        func.extract('epoch', 
                            func.lead(ChatMessage.created_at)
                            .over(
                                partition_by=ChatMessage.conversation_id,
                                order_by=ChatMessage.created_at
                            ) - ChatMessage.created_at
                        )
                    ).label('avg_response_time_seconds')
                )
                .join(ChatConversation)
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatMessage.created_at >= date_from,
                    ChatMessage.role == 'user'
                ))
            )
            response_result = response_time.first()
            
            # Calculate engagement score
            engagement_score = 0
            if active_days > 0:
                engagement_score += (active_days / days) * 30  # 30% weight
            
            if completion_result and completion_result.total_conversations > 0:
                completion_rate = completion_result.completed_conversations / completion_result.total_conversations
                engagement_score += completion_rate * 25  # 25% weight
            
            if duration_result and duration_result.avg_session_duration_seconds:
                # Normalize session duration (higher is better up to a point)
                session_score = min(duration_result.avg_session_duration_seconds / 300, 1) * 20  # 20% weight
                engagement_score += session_score
            
            if response_result and response_result.avg_response_time_seconds:
                # Lower response time is better
                response_score = max(1 - (response_result.avg_response_time_seconds / 60), 0) * 25  # 25% weight
                engagement_score += response_score
            
            return {
                "active_days": active_days,
                "active_days_percentage": (active_days / days) * 100,
                "conversation_completion_rate": (
                    (completion_result.completed_conversations / completion_result.total_conversations) * 100
                    if completion_result and completion_result.total_conversations > 0 else 0
                ),
                "average_session_duration_seconds": float(duration_result.avg_session_duration_seconds or 0),
                "average_response_time_seconds": float(response_result.avg_response_time_seconds or 0),
                "engagement_score": round(engagement_score, 2),
                "engagement_grade": self._get_engagement_grade(engagement_score)
            }
            
        except Exception as e:
            logger.error(f"Failed to get engagement metrics: {e}")
            raise
    
    def _get_engagement_grade(self, score: float) -> str:
        """Get engagement grade based on score."""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Poor"
    
    async def get_top_conversations(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top conversations by various metrics."""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Top conversations by message count
            top_by_messages = await self.db_session.execute(
                select(
                    ChatConversation.id,
                    ChatConversation.title,
                    ChatConversation.provider_id,
                    ChatConversation.message_count,
                    ChatConversation.created_at,
                    ChatConversation.updated_at
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .order_by(desc(ChatConversation.message_count))
                .limit(limit)
            )
            message_results = top_by_messages.all()
            
            # Top conversations by duration
            top_by_duration = await self.db_session.execute(
                select(
                    ChatConversation.id,
                    ChatConversation.title,
                    ChatConversation.provider_id,
                    ChatConversation.message_count,
                    ChatConversation.created_at,
                    ChatConversation.updated_at,
                    func.extract('epoch', 
                        func.coalesce(ChatConversation.updated_at, ChatConversation.created_at) - 
                        ChatConversation.created_at
                    ).label('duration_seconds')
                )
                .where(and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= date_from
                ))
                .order_by(desc('duration_seconds'))
                .limit(limit)
            )
            duration_results = top_by_duration.all()
            
            return {
                "top_by_messages": [
                    {
                        "conversation_id": str(result.id),
                        "title": result.title,
                        "provider_id": result.provider_id,
                        "message_count": result.message_count,
                        "created_at": result.created_at.isoformat(),
                        "updated_at": result.updated_at.isoformat()
                    }
                    for result in message_results
                ],
                "top_by_duration": [
                    {
                        "conversation_id": str(result.id),
                        "title": result.title,
                        "provider_id": result.provider_id,
                        "message_count": result.message_count,
                        "created_at": result.created_at.isoformat(),
                        "updated_at": result.updated_at.isoformat(),
                        "duration_seconds": float(result.duration_seconds or 0)
                    }
                    for result in duration_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get top conversations: {e}")
            raise