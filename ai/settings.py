from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """LLM settings that can be set using environment variables.

    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # gpt_4: str = "gpt-4o"
    # gpt_4: str = "gpt-4o-mini"
    # gpt_4_vision: str = "gpt-4o"
    # gpt_4_vision: str = "gpt-4o-mini"
    # embedding_model: str = "text-embedding-3-small"
    embedding_model: str = "text-embedding-ada-002"
    # default_max_tokens: int = 4096
    default_temperature: float = 0


# Create AISettings object
ai_settings = AISettings()
