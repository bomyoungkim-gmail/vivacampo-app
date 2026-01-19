from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Environment
    env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Model paths
    models_dir: Path = Path("/app/models_tflite")

    # Model configuration
    cattle_model_version: str = "v1"
    crop_disease_model_version: str = "v1"
    poultry_model_version: str = "v1"

    # Image processing
    default_image_size: int = 224
    cattle_image_size: int = 384  # Larger for weight estimation

    # Inference settings
    confidence_threshold: float = 0.5
    max_batch_size: int = 8

    # AWS (for model storage/sync)
    aws_region: str = "sa-east-1"
    aws_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_models_bucket: str = "vivacampo-models"

    # TFLite optimization
    tflite_use_gpu: bool = False
    tflite_num_threads: int = 4


settings = Settings()
