"""Dependency injection container for API layer."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db

from app.config import settings
from app.application.use_cases.aois import (
    CreateAoiUseCase,
    ListAoisUseCase,
    SimulateSplitUseCase,
    SplitAoiUseCase,
    AoiStatusUseCase,
    CreateFieldCalibrationUseCase,
    GetCalibrationUseCase,
    GetPredictionUseCase,
    CreateFieldFeedbackUseCase,
)
from app.application.use_cases.aoi_management import (
    AoiAssetsUseCase,
    AoiHistoryUseCase,
    DeleteAoiUseCase,
    RequestBackfillUseCase,
    UpdateAoiUseCase,
)
from app.application.use_cases.correlation import CorrelationUseCase, YearOverYearUseCase
from app.application.use_cases.farms import (
    CreateFarmUseCase,
    DeleteFarmUseCase,
    ListFarmsUseCase,
    UpdateFarmUseCase,
)
from app.application.use_cases.jobs import (
    CancelJobUseCase,
    GetJobUseCase,
    ListJobRunsUseCase,
    ListJobsUseCase,
    RetryJobUseCase,
)
from app.application.use_cases.nitrogen import GetNitrogenStatusUseCase
from app.application.use_cases.radar import GetRadarHistoryUseCase
from app.application.use_cases.signals import AckSignalUseCase, GetSignalUseCase, ListSignalsUseCase
from app.application.use_cases.tiles import (
    GenerateAoiExportUseCase,
    GetAoiExportStatusUseCase,
    GetAoiTileJsonUseCase,
    GetAoiTileUseCase,
    RequestAoiExportUseCase,
)
from app.application.use_cases.system_admin import (
    CreateTenantUseCase,
    GlobalAuditLogUseCase,
    ListMissingWeeksUseCase,
    ListSystemJobsUseCase,
    ListTenantsUseCase,
    QueueStatsUseCase,
    ReprocessJobsUseCase,
    ReprocessMissingAoisUseCase,
    ReprocessMissingWeeksUseCase,
    RetryJobUseCase as SystemRetryJobUseCase,
    SystemHealthUseCase,
    UpdateTenantUseCase,
)
from app.application.use_cases.tenant_admin import (
    GetTenantAuditLogUseCase,
    GetTenantSettingsUseCase,
    InviteMemberUseCase,
    ListMembersUseCase,
    UpdateMemberRoleUseCase,
    UpdateMemberStatusUseCase,
    UpdateTenantSettingsUseCase,
)
from app.application.use_cases.ai_assistant import (
    CreateThreadUseCase,
    GetApprovalThreadUseCase,
    GetMessagesUseCase,
    ListApprovalsUseCase,
    ListThreadsUseCase,
)
from app.application.use_cases.auth import (
    ForgotPasswordUseCase,
    LoginUseCase,
    ResetPasswordUseCase,
    SignupUseCase,
)
from app.application.use_cases.geocoding import GeocodeUseCase
from app.application.use_cases.weather import GetWeatherHistoryUseCase, RequestWeatherSyncUseCase
from app.domain.audit import AuditLogger
from app.domain.quotas import QuotaService
from app.infrastructure.adapters.message_queue.local_queue_adapter import LocalQueueAdapter
from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_data_repository import SQLAlchemyAoiDataRepository
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_repository import SQLAlchemyAOIRepository
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_spatial_repository import SQLAlchemyAoiSpatialRepository
from app.infrastructure.adapters.persistence.sqlalchemy.audit_repository import SQLAlchemyAuditRepository
from app.infrastructure.adapters.persistence.sqlalchemy.correlation_repository import SQLAlchemyCorrelationRepository
from app.infrastructure.adapters.persistence.sqlalchemy.field_calibration_repository import SQLAlchemyFieldCalibrationRepository
from app.infrastructure.adapters.persistence.sqlalchemy.field_feedback_repository import SQLAlchemyFieldFeedbackRepository
from app.infrastructure.adapters.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository
from app.infrastructure.adapters.persistence.sqlalchemy.job_repository import SQLAlchemyJobRepository
from app.infrastructure.adapters.persistence.sqlalchemy.nitrogen_repository import SQLAlchemyNitrogenRepository
from app.infrastructure.adapters.persistence.sqlalchemy.quota_repository import SQLAlchemyQuotaRepository
from app.infrastructure.adapters.persistence.sqlalchemy.radar_data_repository import SQLAlchemyRadarDataRepository
from app.infrastructure.adapters.persistence.sqlalchemy.signal_repository import SQLAlchemySignalRepository
from app.infrastructure.adapters.persistence.sqlalchemy.split_batch_repository import SQLAlchemySplitBatchRepository
from app.infrastructure.adapters.persistence.sqlalchemy.system_admin_repository import SQLAlchemySystemAdminRepository
from app.infrastructure.adapters.persistence.sqlalchemy.tenant_admin_repository import SQLAlchemyTenantAdminRepository
from app.infrastructure.adapters.persistence.sqlalchemy.ai_assistant_repository import SQLAlchemyAiAssistantRepository
from app.infrastructure.adapters.persistence.sqlalchemy.auth_repository import SQLAlchemyAuthRepository
from app.infrastructure.adapters.geocoding.nominatim_adapter import NominatimAdapter
from app.infrastructure.adapters.persistence.sqlalchemy.weather_data_repository import SQLAlchemyWeatherDataRepository
from app.infrastructure.adapters.persistence.sqlalchemy.yield_forecast_repository import SQLAlchemyYieldForecastRepository
from app.infrastructure.adapters.storage.local_fs_adapter import LocalFileSystemAdapter
from app.infrastructure.adapters.storage.s3_adapter import S3Adapter


class ApiContainer:
    """Lightweight DI container. No global state, safe for tests.

    Usage (API/routers):
        container = ApiContainer()
        use_case = container.create_farm_use_case(db)
        result = await use_case.execute(...)

    Usage (tests with overrides):
        container = ApiContainer(overrides={"farm_repository": FakeFarmRepo()})
        use_case = container.create_farm_use_case(db)

    Adding a new dependency:
    1) Add adapter/repo factory (e.g. `def my_repo(self, db): ...`)
    2) Add use case factory wired to the repo
    3) Use `overrides` to inject fakes in tests
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        env: Optional[str] = None,
        local_storage_base: Optional[str] = None,
        overrides: Optional[dict[str, object]] = None,
    ):
        self.db = db
        self.env = env or settings.env
        self.local_storage_base = local_storage_base
        self.overrides = overrides or {}

    def _resolve(self, name: str, factory, *args, **kwargs):
        override = self.overrides.get(name)
        if override is None:
            return factory(*args, **kwargs)
        if callable(override):
            return override(*args, **kwargs)
        return override

    def _require_db(self, db: Optional[Session]) -> Session:
        if db is not None:
            return db
        if self.db is None:
            raise ValueError("db session required")
        return self.db

    def db_session(self) -> Session:
        return self._require_db(None)

    # Adapters (infrastructure)
    def message_queue(self, force_local: bool = False):
        return self._resolve(
            "message_queue",
            lambda: LocalQueueAdapter() if (force_local or settings.use_local_queue or self.env == "local") else SQSAdapter(),
        )

    def object_storage(self, force_local: bool = False):
        def _factory():
            if force_local or settings.use_local_storage:
                base = self.local_storage_base or settings.local_storage_base
                if not base:
                    raise ValueError("local_storage_base required when force_local=True")
                return LocalFileSystemAdapter(base)
            return S3Adapter()

        return self._resolve("object_storage", _factory)

    # Repositories (persistence)
    def farm_repository(self, db: Optional[Session] = None) -> SQLAlchemyFarmRepository:
        db = self._require_db(db)
        return self._resolve("farm_repository", SQLAlchemyFarmRepository, db)

    def aoi_repository(self, db: Optional[Session] = None) -> SQLAlchemyAOIRepository:
        db = self._require_db(db)
        return self._resolve("aoi_repository", SQLAlchemyAOIRepository, db)

    def split_batch_repository(self, db: Optional[Session] = None) -> SQLAlchemySplitBatchRepository:
        db = self._require_db(db)
        return self._resolve("split_batch_repository", SQLAlchemySplitBatchRepository, db)
    def aoi_spatial_repository(self, db: Optional[Session] = None) -> SQLAlchemyAoiSpatialRepository:
        db = self._require_db(db)
        return self._resolve("aoi_spatial_repository", SQLAlchemyAoiSpatialRepository, db)

    def aoi_data_repository(self, db: Optional[Session] = None) -> SQLAlchemyAoiDataRepository:
        db = self._require_db(db)
        return self._resolve("aoi_data_repository", SQLAlchemyAoiDataRepository, db)

    def field_calibration_repository(self, db: Optional[Session] = None) -> SQLAlchemyFieldCalibrationRepository:
        db = self._require_db(db)
        return self._resolve("field_calibration_repository", SQLAlchemyFieldCalibrationRepository, db)

    def yield_forecast_repository(self, db: Optional[Session] = None) -> SQLAlchemyYieldForecastRepository:
        db = self._require_db(db)
        return self._resolve("yield_forecast_repository", SQLAlchemyYieldForecastRepository, db)

    def field_feedback_repository(self, db: Optional[Session] = None) -> SQLAlchemyFieldFeedbackRepository:
        db = self._require_db(db)
        return self._resolve("field_feedback_repository", SQLAlchemyFieldFeedbackRepository, db)

    def signal_repository(self, db: Optional[Session] = None) -> SQLAlchemySignalRepository:
        db = self._require_db(db)
        return self._resolve("signal_repository", SQLAlchemySignalRepository, db)

    def job_repository(self, db: Optional[Session] = None) -> SQLAlchemyJobRepository:
        db = self._require_db(db)
        return self._resolve("job_repository", SQLAlchemyJobRepository, db)

    def correlation_repository(self, db: Optional[Session] = None) -> SQLAlchemyCorrelationRepository:
        db = self._require_db(db)
        return self._resolve("correlation_repository", SQLAlchemyCorrelationRepository, db)

    def nitrogen_repository(self, db: Optional[Session] = None) -> SQLAlchemyNitrogenRepository:
        db = self._require_db(db)
        return self._resolve("nitrogen_repository", SQLAlchemyNitrogenRepository, db)

    def radar_data_repository(self, db: Optional[Session] = None) -> SQLAlchemyRadarDataRepository:
        db = self._require_db(db)
        return self._resolve("radar_data_repository", SQLAlchemyRadarDataRepository, db)

    def weather_data_repository(self, db: Optional[Session] = None) -> SQLAlchemyWeatherDataRepository:
        db = self._require_db(db)
        return self._resolve("weather_data_repository", SQLAlchemyWeatherDataRepository, db)

    def system_admin_repository(self, db: Optional[Session] = None) -> SQLAlchemySystemAdminRepository:
        db = self._require_db(db)
        return self._resolve("system_admin_repository", SQLAlchemySystemAdminRepository, db)

    def tenant_admin_repository(self, db: Optional[Session] = None) -> SQLAlchemyTenantAdminRepository:
        db = self._require_db(db)
        return self._resolve("tenant_admin_repository", SQLAlchemyTenantAdminRepository, db)

    def ai_assistant_repository(self, db: Optional[Session] = None) -> SQLAlchemyAiAssistantRepository:
        db = self._require_db(db)
        return self._resolve("ai_assistant_repository", SQLAlchemyAiAssistantRepository, db)

    def auth_repository(self, db: Optional[Session] = None) -> SQLAlchemyAuthRepository:
        db = self._require_db(db)
        return self._resolve("auth_repository", SQLAlchemyAuthRepository, db)

    def quota_repository(self, db: Optional[Session] = None) -> SQLAlchemyQuotaRepository:
        db = self._require_db(db)
        return self._resolve("quota_repository", SQLAlchemyQuotaRepository, db)

    def audit_repository(self, db: Optional[Session] = None) -> SQLAlchemyAuditRepository:
        db = self._require_db(db)
        return self._resolve("audit_repository", SQLAlchemyAuditRepository, db)

    def geocoding_provider(self) -> NominatimAdapter:
        return self._resolve("geocoding_provider", NominatimAdapter)

    # Use cases (application)
    def create_farm_use_case(self, db: Optional[Session] = None) -> CreateFarmUseCase:
        return CreateFarmUseCase(self.farm_repository(db))

    def update_farm_use_case(self, db: Optional[Session] = None) -> UpdateFarmUseCase:
        return UpdateFarmUseCase(self.farm_repository(db))

    def delete_farm_use_case(self, db: Optional[Session] = None) -> DeleteFarmUseCase:
        return DeleteFarmUseCase(self.farm_repository(db))

    def list_farms_use_case(self, db: Optional[Session] = None) -> ListFarmsUseCase:
        return ListFarmsUseCase(self.farm_repository(db))

    def create_aoi_use_case(self, db: Optional[Session] = None) -> CreateAoiUseCase:
        return CreateAoiUseCase(self.aoi_repository(db))

    def list_aois_use_case(self, db: Optional[Session] = None) -> ListAoisUseCase:
        return ListAoisUseCase(self.aoi_repository(db))

    def simulate_split_use_case(self, db: Optional[Session] = None) -> SimulateSplitUseCase:
        return SimulateSplitUseCase(self.aoi_spatial_repository(db))

    def split_aoi_use_case(self, db: Optional[Session] = None) -> SplitAoiUseCase:
        return SplitAoiUseCase(self.aoi_repository(db), self.split_batch_repository(db))

    def aoi_status_use_case(self, db: Optional[Session] = None) -> AoiStatusUseCase:
        return AoiStatusUseCase(self.job_repository(db))

    def create_field_calibration_use_case(self, db: Optional[Session] = None) -> CreateFieldCalibrationUseCase:
        return CreateFieldCalibrationUseCase(self.aoi_repository(db), self.field_calibration_repository(db))

    def calibration_use_case(self, db: Optional[Session] = None) -> GetCalibrationUseCase:
        return GetCalibrationUseCase(self.field_calibration_repository(db), self.aoi_data_repository(db))

    def prediction_use_case(self, db: Optional[Session] = None) -> GetPredictionUseCase:
        return GetPredictionUseCase(self.yield_forecast_repository(db))

    def create_field_feedback_use_case(self, db: Optional[Session] = None) -> CreateFieldFeedbackUseCase:
        return CreateFieldFeedbackUseCase(self.aoi_repository(db), self.field_feedback_repository(db))

    def update_aoi_use_case(self, db: Optional[Session] = None) -> UpdateAoiUseCase:
        return UpdateAoiUseCase(self.aoi_repository(db))

    def delete_aoi_use_case(self, db: Optional[Session] = None) -> DeleteAoiUseCase:
        return DeleteAoiUseCase(self.aoi_repository(db))

    def aoi_assets_use_case(self, db: Optional[Session] = None) -> AoiAssetsUseCase:
        return AoiAssetsUseCase(self.aoi_data_repository(db))

    def aoi_history_use_case(self, db: Optional[Session] = None) -> AoiHistoryUseCase:
        return AoiHistoryUseCase(self.aoi_data_repository(db))

    def request_backfill_use_case(self, db: Optional[Session] = None) -> RequestBackfillUseCase:
        queue = self.message_queue()
        return RequestBackfillUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )

    def tile_use_case(self, db: Optional[Session] = None) -> GetAoiTileUseCase:
        return GetAoiTileUseCase(self.aoi_spatial_repository(db))

    def tilejson_use_case(self, db: Optional[Session] = None) -> GetAoiTileJsonUseCase:
        return GetAoiTileJsonUseCase(
            repo=self.aoi_spatial_repository(db),
            api_base_url=getattr(settings, "api_base_url", "http://localhost:8000"),
            cdn_enabled=getattr(settings, "cdn_enabled", False),
            cdn_tiles_url=getattr(settings, "cdn_tiles_url", None),
        )

    def tile_export_use_case(self, db: Optional[Session] = None) -> RequestAoiExportUseCase:
        return RequestAoiExportUseCase(
            repo=self.aoi_spatial_repository(db),
            storage=self.object_storage(),
        )

    def tile_export_status_use_case(self) -> GetAoiExportStatusUseCase:
        return GetAoiExportStatusUseCase(storage=self.object_storage())

    def tile_export_generate_use_case(self, db: Optional[Session] = None) -> GenerateAoiExportUseCase:
        return GenerateAoiExportUseCase(
            repo=self.aoi_spatial_repository(db),
            storage=self.object_storage(),
            tiler_url=getattr(settings, "tiler_url", "http://tiler:8080"),
        )

    def list_tenants_use_case(self, db: Optional[Session] = None) -> ListTenantsUseCase:
        return ListTenantsUseCase(self.system_admin_repository(db))

    def create_tenant_use_case(self, db: Optional[Session] = None) -> CreateTenantUseCase:
        return CreateTenantUseCase(self.system_admin_repository(db))

    def update_tenant_use_case(self, db: Optional[Session] = None) -> UpdateTenantUseCase:
        return UpdateTenantUseCase(self.system_admin_repository(db))

    def list_system_jobs_use_case(self, db: Optional[Session] = None) -> ListSystemJobsUseCase:
        return ListSystemJobsUseCase(self.system_admin_repository(db))

    def system_retry_job_use_case(self, db: Optional[Session] = None) -> SystemRetryJobUseCase:
        return SystemRetryJobUseCase(self.system_admin_repository(db))

    def reprocess_missing_aois_use_case(self, db: Optional[Session] = None) -> ReprocessMissingAoisUseCase:
        queue = self.message_queue()
        return ReprocessMissingAoisUseCase(
            repo=self.system_admin_repository(db),
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )

    def list_missing_weeks_use_case(self, db: Optional[Session] = None) -> ListMissingWeeksUseCase:
        return ListMissingWeeksUseCase(self.system_admin_repository(db))

    def reprocess_missing_weeks_use_case(self, db: Optional[Session] = None) -> ReprocessMissingWeeksUseCase:
        queue = self.message_queue()
        backfill_use_case = RequestBackfillUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )
        return ReprocessMissingWeeksUseCase(
            repo=self.system_admin_repository(db),
            backfill_use_case=backfill_use_case,
        )

    def reprocess_jobs_use_case(self, db: Optional[Session] = None) -> ReprocessJobsUseCase:
        queue = self.message_queue()
        return ReprocessJobsUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )

    def system_health_use_case(self, db: Optional[Session] = None) -> SystemHealthUseCase:
        return SystemHealthUseCase(self.system_admin_repository(db))

    def queue_stats_use_case(self, db: Optional[Session] = None) -> QueueStatsUseCase:
        return QueueStatsUseCase(self.system_admin_repository(db))

    def global_audit_log_use_case(self, db: Optional[Session] = None) -> GlobalAuditLogUseCase:
        return GlobalAuditLogUseCase(self.system_admin_repository(db))

    def list_tenant_members_use_case(self, db: Optional[Session] = None) -> ListMembersUseCase:
        return ListMembersUseCase(self.tenant_admin_repository(db))

    def invite_tenant_member_use_case(self, db: Optional[Session] = None) -> InviteMemberUseCase:
        return InviteMemberUseCase(self.tenant_admin_repository(db))

    def update_member_role_use_case(self, db: Optional[Session] = None) -> UpdateMemberRoleUseCase:
        return UpdateMemberRoleUseCase(self.tenant_admin_repository(db))

    def update_member_status_use_case(self, db: Optional[Session] = None) -> UpdateMemberStatusUseCase:
        return UpdateMemberStatusUseCase(self.tenant_admin_repository(db))

    def get_tenant_settings_use_case(self, db: Optional[Session] = None) -> GetTenantSettingsUseCase:
        return GetTenantSettingsUseCase(self.tenant_admin_repository(db))

    def update_tenant_settings_use_case(self, db: Optional[Session] = None) -> UpdateTenantSettingsUseCase:
        return UpdateTenantSettingsUseCase(self.tenant_admin_repository(db))

    def tenant_audit_log_use_case(self, db: Optional[Session] = None) -> GetTenantAuditLogUseCase:
        return GetTenantAuditLogUseCase(self.tenant_admin_repository(db))

    def create_ai_thread_use_case(self, db: Optional[Session] = None) -> CreateThreadUseCase:
        return CreateThreadUseCase(self.ai_assistant_repository(db))

    def list_ai_threads_use_case(self, db: Optional[Session] = None) -> ListThreadsUseCase:
        return ListThreadsUseCase(self.ai_assistant_repository(db))

    def ai_messages_use_case(self, db: Optional[Session] = None) -> GetMessagesUseCase:
        return GetMessagesUseCase(self.ai_assistant_repository(db))

    def list_ai_approvals_use_case(self, db: Optional[Session] = None) -> ListApprovalsUseCase:
        return ListApprovalsUseCase(self.ai_assistant_repository(db))

    def ai_approval_thread_use_case(self, db: Optional[Session] = None) -> GetApprovalThreadUseCase:
        return GetApprovalThreadUseCase(self.ai_assistant_repository(db))

    def geocode_use_case(self) -> GeocodeUseCase:
        return GeocodeUseCase(self.geocoding_provider())

    def signup_use_case(self, db: Optional[Session] = None) -> SignupUseCase:
        return SignupUseCase(self.auth_repository(db))

    def login_use_case(self, db: Optional[Session] = None) -> LoginUseCase:
        return LoginUseCase(self.auth_repository(db))

    def forgot_password_use_case(self, db: Optional[Session] = None) -> ForgotPasswordUseCase:
        return ForgotPasswordUseCase(self.auth_repository(db))

    def reset_password_use_case(self, db: Optional[Session] = None) -> ResetPasswordUseCase:
        return ResetPasswordUseCase(self.auth_repository(db))

    def list_signals_use_case(self, db: Optional[Session] = None) -> ListSignalsUseCase:
        return ListSignalsUseCase(self.signal_repository(db))

    def get_signal_use_case(self, db: Optional[Session] = None) -> GetSignalUseCase:
        return GetSignalUseCase(self.signal_repository(db))

    def ack_signal_use_case(self, db: Optional[Session] = None) -> AckSignalUseCase:
        return AckSignalUseCase(self.signal_repository(db))

    def list_jobs_use_case(self, db: Optional[Session] = None) -> ListJobsUseCase:
        return ListJobsUseCase(self.job_repository(db))

    def get_job_use_case(self, db: Optional[Session] = None) -> GetJobUseCase:
        return GetJobUseCase(self.job_repository(db))

    def list_job_runs_use_case(self, db: Optional[Session] = None) -> ListJobRunsUseCase:
        return ListJobRunsUseCase(self.job_repository(db))

    def retry_job_use_case(self, db: Optional[Session] = None) -> RetryJobUseCase:
        return RetryJobUseCase(self.job_repository(db))

    def cancel_job_use_case(self, db: Optional[Session] = None) -> CancelJobUseCase:
        return CancelJobUseCase(self.job_repository(db))

    def correlation_use_case(self, db: Optional[Session] = None) -> CorrelationUseCase:
        return CorrelationUseCase(self.correlation_repository(db))

    def year_over_year_use_case(self, db: Optional[Session] = None) -> YearOverYearUseCase:
        return YearOverYearUseCase(self.correlation_repository(db))

    def nitrogen_use_case(self, db: Optional[Session] = None) -> GetNitrogenStatusUseCase:
        return GetNitrogenStatusUseCase(self.nitrogen_repository(db))

    def radar_history_use_case(self, db: Optional[Session] = None) -> GetRadarHistoryUseCase:
        return GetRadarHistoryUseCase(self.radar_data_repository(db))

    def weather_history_use_case(self, db: Optional[Session] = None) -> GetWeatherHistoryUseCase:
        return GetWeatherHistoryUseCase(self.weather_data_repository(db))

    def request_weather_sync_use_case(self, db: Optional[Session] = None) -> RequestWeatherSyncUseCase:
        queue = self.message_queue()
        return RequestWeatherSyncUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
        )

    # Domain services
    def quota_service(self, db: Optional[Session] = None) -> QuotaService:
        return QuotaService(self.quota_repository(db))

    def audit_logger(self, db: Optional[Session] = None) -> AuditLogger:
        return AuditLogger(self.audit_repository(db))


def get_container(db: Session = Depends(get_db)) -> ApiContainer:
    return ApiContainer(db=db)
