from .settings import ExpressionSettings

def allow_external_engines(settings: ExpressionSettings) -> bool:
    return settings.active_engine != 'builtin'
