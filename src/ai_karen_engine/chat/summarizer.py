"""
Conversation Summarizer
LLM-based summarization for chat memory management
"""

from typing import List, Dict, Any
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.llm_orchestrator import LLMOrchestrator

logger = get_logger(__name__)


async def summarize_conversation(turns: List[Dict[str, Any]]) -> str:
    """
    Summarize a list of conversation turns using LLM
    
    Args:
        turns: List of turn dictionaries with 'prompt' and 'response' keys
        
    Returns:
        Concise summary of the conversation
    """
    
    if not turns:
        return ""
    
    try:
        # Format conversation for summarization
        conversation_text = []
        for turn in turns:
            conversation_text.append(f"User: {turn['prompt']}")
            conversation_text.append(f"Assistant: {turn['response']}")
        
        full_conversation = "\n".join(conversation_text)
        
        # Create summarization prompt
        prompt = f"""Please provide a concise summary of the following conversation between a user and an AI assistant. Focus on:
1. Key topics discussed
2. Important information shared
3. Decisions made or conclusions reached
4. Any ongoing context that would be useful for future conversations

Conversation:
{full_conversation}

Summary:"""
        
        # Get LLM orchestrator
        llm_orchestrator = LLMOrchestrator()
        
        # Generate summary
        response = await llm_orchestrator.generate_response(
            prompt=prompt,
            max_tokens=300,
            temperature=0.3,  # Lower temperature for more focused summaries
            system_prompt="You are a helpful assistant that creates concise, accurate summaries of conversations."
        )
        
        summary = response.get("response", "").strip()
        
        if not summary:
            # Fallback summary if LLM fails
            summary = f"Conversation with {len(turns)} exchanges covering various topics."
        
        logger.info(f"Generated summary for {len(turns)} conversation turns")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to summarize conversation: {e}")
        
        # Fallback summary
        topics = []
        for turn in turns[:3]:  # Look at first few turns for topics
            if len(turn['prompt']) > 10:
                # Extract potential topics from prompts
                words = turn['prompt'].lower().split()
                topics.extend([word for word in words if len(word) > 4])
        
        if topics:
            unique_topics = list(set(topics))[:5]  # Max 5 topics
            return f"Discussion about {', '.join(unique_topics)} and related topics ({len(turns)} exchanges)."
        else:
            return f"Conversation with {len(turns)} exchanges covering various topics."


async def extract_key_topics(text: str, max_topics: int = 5) -> List[str]:
    """
    Extract key topics from conversation text
    
    Args:
        text: Conversation text to analyze
        max_topics: Maximum number of topics to return
        
    Returns:
        List of key topics
    """
    
    try:
        prompt = f"""Extract the {max_topics} most important topics or themes from the following text. Return only the topics as a comma-separated list, no explanations.

Text:
{text}

Topics:"""
        
        # Get LLM orchestrator
        llm_orchestrator = LLMOrchestrator()
        
        # Generate topics
        response = await llm_orchestrator.generate_response(
            prompt=prompt,
            max_tokens=100,
            temperature=0.2,
            system_prompt="You are a helpful assistant that extracts key topics from text."
        )
        
        topics_text = response.get("response", "").strip()
        
        if topics_text:
            # Parse topics
            topics = [topic.strip() for topic in topics_text.split(",")]
            return topics[:max_topics]
        
        return []
        
    except Exception as e:
        logger.error(f"Failed to extract topics: {e}")
        return []


async def should_reference_memory(user_message: str) -> bool:
    """
    Determine if the user message requires referencing chat memory
    
    Args:
        user_message: The user's message
        
    Returns:
        True if memory should be referenced
    """
    
    # Keywords that suggest the user is asking about past conversation
    memory_keywords = [
        "remember", "recall", "earlier", "before", "previous", "ago",
        "mentioned", "discussed", "talked about", "said", "told",
        "what did", "when did", "how did", "why did", "where did",
        "last time", "yesterday", "today", "this morning", "this week"
    ]
    
    user_lower = user_message.lower()
    
    # Check for memory keywords
    for keyword in memory_keywords:
        if keyword in user_lower:
            return True
    
    # Check for question patterns that might reference past context
    question_patterns = [
        "what was", "what were", "how was", "how were", "why was", "why were",
        "when was", "when were", "where was", "where were", "who was", "who were"
    ]
    
    for pattern in question_patterns:
        if pattern in user_lower:
            return True
    
    return False


def extract_search_query(user_message: str) -> str:
    """
    Extract a search query from the user's message for semantic search
    
    Args:
        user_message: The user's message
        
    Returns:
        Extracted search query
    """
    
    # Remove common question words and focus on content
    stop_words = {
        "what", "how", "why", "when", "where", "who", "which", "whose",
        "did", "do", "does", "is", "are", "was", "were", "will", "would",
        "could", "should", "can", "may", "might", "must", "shall",
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "up", "about", "into", "through",
        "during", "before", "after", "above", "below", "between", "among",
        "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
    }
    
    # Extract meaningful words
    words = user_message.lower().split()
    meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Return the most relevant words as search query
    return " ".join(meaningful_words[:10])  # Limit to 10 words