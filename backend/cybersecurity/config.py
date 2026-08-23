from pydantic_settings import BaseSettings


class CybersecurityEmailSettings(BaseSettings):

    recipient_email: str


    class Config:

        env_prefix = (
            "CYBERSECURITY_"
        )