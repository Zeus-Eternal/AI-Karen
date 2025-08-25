# SpaCy Analyzer with Persona Logic

## Overview

The `SpacyAnalyzer` is a comprehensive text analysis component that implements the `Analyzer` protocol for the Response Core orchestrator. It provides intent detection, sentiment analysis, entity extraction, and intelligent persona selection based on user input patterns.

## Features

### Intent Detection
- **Pattern-based matching**: Uses regex patterns to identify user intents
- **spaCy integration**: Leverages spaCy's NLP capabilities for sophisticated analysis
- **Fallback mechanisms**: Graceful degradation when spaCy is unavailable

Supported intents:
- `optimize_code`: Code optimization requests
- `debug_error`: Error debugging and troubleshooting
- `technical_question`: Technical questions and explanations
- `creative_task`: Creative projects and brainstorming
- `business_advice`: Business strategy and planning
- `documentation`: Documentation and writing tasks
- `troubleshoot`: General problem-solving
- `explain_concept`: Concept explanations and learning
- `casual_chat`: Casual conversation and greetings
- `general_assist`: General assistance requests

### Sentiment Analysis
- **Keyword-based detection**: Identifies emotional indicators in text
- **spaCy enhancement**: Uses linguistic features for better accuracy
- **Multi-dimensional analysis**: Detects various sentiment types

Supported sentiments:
- `frustrated`: User frustration and annoyance
- `confused`: Confusion and uncertainty
- `excited`: Enthusiasm and excitement
- `urgent`: Time-sensitive requests
- `positive`: Positive emotions and satisfaction
- `negative`: Negative emotions and dissatisfaction
- `neutral`: Neutral or unclear sentiment
- `calm`: Calm and composed state

### Entity Extraction
- **spaCy NER**: Named entity recognition using spaCy models
- **Metadata enrichment**: Additional linguistic features and statistics
- **Fallback extraction**: Basic entity detection when spaCy is unavailable

### Persona Selection
- **Intent + Sentiment mapping**: Intelligent persona selection based on user state
- **Confidence scoring**: Weighted persona recommendations
- **Fallback logic**: Default persona selection for edge cases

Available personas:
- `support-assistant`: Patient support for frustrated users
- `technical-expert`: Technical expertise for code and development
- `creative-collaborator`: Creative assistance and brainstorming
- `business-advisor`: Professional business guidance
- `casual-friend`: Friendly casual conversation

### Profile Gap Detection
- **Onboarding flow support**: Identifies missing user profile information
- **Priority-based gaps**: Categorizes gaps by importance
- **Contextual questions**: Generates relevant onboarding questions

Detected gaps:
- Project context and information
- Technology stack and preferences
- Experience level and background
- User goals and objectives

## Usage

### Basic Usage

```python
from ai_karen_engine.core.response.analyzer import SpacyAnalyzer

# Create analyzer instance
analyzer = SpacyAnalyzer()

# Detect intent
intent = analyzer.detect_intent("How can I optimize this code?")
print(intent)  # "optimize_code"

# Analyze sentiment
sentiment = analyzer.sentiment("This is so frustrating!")
print(sentiment)  # "frustrated"

# Extract entities
entities = analyzer.entities("I'm using Python with Django")
print(entities)  # {"entities": [...], "metadata": {...}}

# Select persona
persona = analyzer.select_persona("debug_error", "frustrated")
print(persona)  # "support-assistant"
```

### Async Profile Gap Detection

```python
import asyncio

async def detect_gaps():
    analyzer = SpacyAnalyzer()
    ui_caps = {"project_name": None}  # Missing project info
    
    gaps = await analyzer.detect_profile_gaps("Help me code", ui_caps)
    print(gaps["next_question"])  # Onboarding question

asyncio.run(detect_gaps())
```

### Factory Function

```python
from ai_karen_engine.core.response.analyzer import create_spacy_analyzer

# Create with default spaCy service
analyzer = create_spacy_analyzer()

# Create with custom spaCy service
from ai_karen_engine.services.spacy_service import SpacyService
custom_service = SpacyService()
analyzer = create_spacy_analyzer(spacy_service=custom_service)
```

## Integration with Response Core

The analyzer integrates seamlessly with the Response Core orchestrator:

```python
from ai_karen_engine.core.response import create_response_orchestrator

# The orchestrator automatically uses the new SpacyAnalyzer
orchestrator = create_response_orchestrator(user_id="user123")

# Analyzer is used internally for all text analysis
response = orchestrator.respond(
    user_text="I'm getting an error in my code",
    ui_caps={"copilotkit": True}
)
```

## Configuration

### Intent Patterns
Intent detection patterns can be customized by modifying the `_build_intent_patterns()` method. Patterns use Python regex syntax:

```python
IntentType.OPTIMIZE_CODE: [
    r'\b(optimize|improve|refactor|performance|faster|efficient)\b',
    r'\b(slow|inefficient|bottleneck)\b',
    r'\b(make.*better|speed.*up|clean.*up)\b'
]
```

### Sentiment Keywords
Sentiment detection keywords can be customized in `_build_sentiment_keywords()`:

```python
SentimentType.FRUSTRATED: [
    'frustrated', 'annoying', 'irritating', 'stupid', 'hate', 'terrible'
]
```

### Persona Mappings
Persona selection rules can be customized in `_build_persona_mappings()`:

```python
PersonaMapping(IntentType.DEBUG_ERROR, SentimentType.FRUSTRATED, "support-assistant", 0.9)
```

## Error Handling

The analyzer includes comprehensive error handling:

- **spaCy failures**: Graceful fallback to keyword-based analysis
- **Async context issues**: Proper handling of event loop conflicts
- **Invalid inputs**: Safe defaults for empty or malformed text
- **Service unavailability**: Fallback mechanisms when dependencies fail

## Performance Considerations

- **Caching**: spaCy service includes built-in caching for parsed messages
- **Async support**: Non-blocking operations for better performance
- **Lazy loading**: spaCy models loaded on-demand
- **Memory efficiency**: Efficient pattern matching and keyword lookup

## Testing

The analyzer includes comprehensive test coverage:

```bash
# Run unit tests
python -m pytest tests/test_spacy_analyzer.py -v

# Run integration tests
python -m pytest tests/test_spacy_analyzer_integration.py -v
```

## Requirements Compliance

This implementation satisfies the following requirements from the specification:

- **Requirement 2.1**: spaCy-based intent and sentiment analysis
- **Requirement 3.1-3.3**: Persona selection based on intent + mood mapping
- **Requirement 3.4**: Profile gap detection for onboarding flows
- **Requirement 12.1-12.3**: Integration with existing reasoning system

## Architecture

The analyzer follows a modular architecture:

```
SpacyAnalyzer
├── Intent Detection
│   ├── Pattern Matching
│   └── spaCy Analysis
├── Sentiment Analysis
│   ├── Keyword Detection
│   └── Linguistic Features
├── Entity Extraction
│   ├── spaCy NER
│   └── Metadata Enrichment
├── Persona Selection
│   ├── Mapping Rules
│   └── Confidence Scoring
└── Profile Gap Detection
    ├── Pattern Analysis
    └── Onboarding Logic
```

## Future Enhancements

Planned improvements include:

1. **Machine Learning Models**: Custom trained models for intent/sentiment
2. **Context Awareness**: Multi-turn conversation context
3. **Domain Adaptation**: Specialized analysis for different domains
4. **Performance Optimization**: Faster pattern matching and caching
5. **Multilingual Support**: Analysis in multiple languages