from pydantic_settings import BaseSettings, SettingsConfigDict

#Việc dùng Settings sẽ giữ được nguyên tắc configuration tập trung, tránh phải import os và gọi đơn lẻ các biến
class Settings(BaseSettings):
    app_name: str = "Smart Home IoT"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str = "sqlite:///./smart_home.db"

    mqtt_broker_host: str = "127.0.0.1"
    mqtt_broker_port: int = 1883
    mqtt_keepalive: int = 60
    mqtt_client_id: str = "smart_home_backend"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()