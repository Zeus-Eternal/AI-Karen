from ai_karen_engine.models.shared_types import PersonalityTone, PersonalityVerbosity


def apply_personality(message: str, tone: PersonalityTone, verbosity: PersonalityVerbosity) -> str:
    """Apply tone and verbosity settings to a message."""
    # Tone adjustments
    if tone == PersonalityTone.FORMAL:
        if "I'd be happy to" in message:
            message = message.replace("I'd be happy to", "I would be pleased to")
    elif tone == PersonalityTone.HUMOROUS:
        if "Which location" in message:
            message = message.replace("Which location", "What magical place")

    # Verbosity adjustments
    if verbosity == PersonalityVerbosity.CONCISE:
        message = message.replace("I'd be happy to check the weather for you. ", "")
        message = message.replace("I'd be happy to look up book information for you. ", "")
    elif verbosity == PersonalityVerbosity.DETAILED:
        lower_msg = message.lower()
        if "weather" in lower_msg:
            message += " I can provide current conditions, temperature, and forecast information."
        elif "book" in lower_msg:
            message += " I can find details like author, publication date, summary, and reviews."

    return message
