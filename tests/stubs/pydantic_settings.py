import os

from ai_karen_engine.pydantic_stub import BaseModel, ValidationError


class SettingsConfigDict(dict):
    pass


class BaseSettings(BaseModel):
    model_config: SettingsConfigDict = SettingsConfigDict()

    def __init__(self):
        data = {}
        for name in self.__annotations__:
            env_name = name.upper()
            default = getattr(self.__class__, name, None)
            value = os.getenv(env_name, default)
            if value is None:
                raise ValidationError(f"Missing environment variable: {env_name}")
            data[name] = value
        super().__init__(**data)
