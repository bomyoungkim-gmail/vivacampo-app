from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Environment
    env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"
    
    # Auth
    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    system_admin_issuer: str
    system_admin_audience: str
    
    tenant_claim_key: str = "custom:tenantID"
    roles_claim_key: str = "custom:roles"
    
    # Session token (workspace switch)
    session_jwt_secret: str
    session_jwt_issuer: str
    session_jwt_audience: str
    session_token_ttl_minutes: int = 120
    
    # Database
    database_url: str
    redis_url: str
    
    # AWS
    aws_region: str = "sa-east-1"
    aws_endpoint_url: str | None = None  # For LocalStack
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_bucket: str
    s3_presign_expires_seconds: int = 900
    s3_force_path_style: bool = False
    
    sqs_queue_name: str
    sqs_dlq_name: str
    sqs_visibility_timeout_seconds: int = 900
    sqs_max_receive_count: int = 3
    
    # Pipeline
    pipeline_version: str = "v1"
    max_cloud_cover: int = 60
    min_valid_pixel_ratio: float = 0.15
    
    # Signals
    signals_enabled: bool = True
    signals_change_detection: str = "BFastLike"
    signals_min_history_weeks: int = 12
    signals_score_threshold: float = 0.65
    signals_persistence_weeks: int = 3
    signals_model_version: str = "signals-v1"
    
    # AI Assistant (renamed from Copilot)
    ai_assistant_enabled: bool = True
    ai_assistant_provider: str = "openai"  # openai, anthropic, gemini
    ai_assistant_model: str = "gpt-4"
    ai_assistant_api_key: str | None = None
    ai_assistant_hitl_required: bool = True
    ai_assistant_interrupt_on_tools: str = '["create_notification","trigger_webhook","create_work_order"]'
    ai_assistant_state_store: Literal["postgres", "redis"] = "postgres"
    ai_assistant_max_steps: int = 12
    
    # UI
    ui_min_touch_target_px: int = 44


settings = Settings()
