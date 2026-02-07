from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Environment
    env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"
    
    # Database
    database_url: str
    
    # AWS
    aws_region: str = "sa-east-1"
    aws_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_connect_timeout_seconds: int = 5
    aws_read_timeout_seconds: int = 60
    s3_bucket: str
    s3_force_path_style: bool = False
    
    sqs_queue_name: str
    sqs_queue_high_priority_name: str = "vivacampo-jobs-high"
    sqs_dlq_name: str
    sqs_visibility_timeout_seconds: int = 900
    sqs_max_receive_count: int = 3
    
    # TiTiler
    tiler_url: str = "http://tiler:8080"
    api_url: str = "http://api:8000"

    # Pipeline
    pipeline_version: str = "v1"
    max_cloud_cover: int = 100
    min_valid_pixel_ratio: float = 0.01

    # Providers
    satellite_provider: str = "planetary_computer"
    weather_provider: str = "open_meteo"
    satellite_fallback_providers: str = ""
    cdse_client_id: str | None = None
    cdse_client_secret: str | None = None

    # Dynamic Tiling (ADR-0007)
    # When enabled, skips per-AOI COG generation and uses MosaicJSON + TiTiler instead
    use_dynamic_tiling: bool = True  # Default to new architecture
    dynamic_tiling_stats_only: bool = True  # Only calculate stats, no COG upload
    
    # Signals
    signals_enabled: bool = True
    signals_change_detection: str = "BFastLike"
    signals_min_history_weeks: int = 12
    signals_score_threshold: float = 0.65
    signals_persistence_weeks: int = 3
    signals_model_version: str = "signals-v1"


settings = Settings()
