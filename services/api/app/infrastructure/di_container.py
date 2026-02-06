"""Dependency injection container for API layer."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.application.use_cases.aois import CreateAoiUseCase, ListAoisUseCase
from app.application.use_cases.aoi_management import (
    AoiAssetsUseCase,
    AoiHistoryUseCase,
    DeleteAoiUseCase,
    RequestBackfillUseCase,
    UpdateAoiUseCase,
)
from app.application.use_cases.correlation import CorrelationUseCase, YearOverYearUseCase
from app.application.use_cases.farms import CreateFarmUseCase, ListFarmsUseCase
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
from app.application.use_cases.geocoding import GeocodeUseCase
from app.application.use_cases.weather import GetWeatherHistoryUseCase, RequestWeatherSyncUseCase
from app.infrastructure.adapters.message_queue.local_queue_adapter import LocalQueueAdapter
from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_data_repository import SQLAlchemyAoiDataRepository
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_repository import SQLAlchemyAOIRepository
from app.infrastructure.adapters.persistence.sqlalchemy.aoi_spatial_repository import SQLAlchemyAoiSpatialRepository
from app.infrastructure.adapters.persistence.sqlalchemy.correlation_repository import SQLAlchemyCorrelationRepository
from app.infrastructure.adapters.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository
from app.infrastructure.adapters.persistence.sqlalchemy.job_repository import SQLAlchemyJobRepository
from app.infrastructure.adapters.persistence.sqlalchemy.nitrogen_repository import SQLAlchemyNitrogenRepository
from app.infrastructure.adapters.persistence.sqlalchemy.radar_data_repository import SQLAlchemyRadarDataRepository
from app.infrastructure.adapters.persistence.sqlalchemy.signal_repository import SQLAlchemySignalRepository
from app.infrastructure.adapters.persistence.sqlalchemy.system_admin_repository import SQLAlchemySystemAdminRepository
from app.infrastructure.adapters.persistence.sqlalchemy.tenant_admin_repository import SQLAlchemyTenantAdminRepository
from app.infrastructure.adapters.persistence.sqlalchemy.ai_assistant_repository import SQLAlchemyAiAssistantRepository
from app.infrastructure.adapters.geocoding.nominatim_adapter import NominatimAdapter
from app.infrastructure.adapters.persistence.sqlalchemy.weather_data_repository import SQLAlchemyWeatherDataRepository
from app.infrastructure.adapters.storage.local_fs_adapter import LocalFileSystemAdapter
from app.infrastructure.adapters.storage.s3_adapter import S3Adapter


class ApiContainer:
    """Lightweight DI container. No global state, safe for tests."""

    def __init__(
        self,
        env: Optional[str] = None,
        local_storage_base: Optional[str] = None,
        overrides: Optional[dict[str, object]] = None,
    ):
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
    def farm_repository(self, db: Session) -> SQLAlchemyFarmRepository:
        return self._resolve("farm_repository", SQLAlchemyFarmRepository, db)

    def aoi_repository(self, db: Session) -> SQLAlchemyAOIRepository:
        return self._resolve("aoi_repository", SQLAlchemyAOIRepository, db)

    def aoi_spatial_repository(self, db: Session) -> SQLAlchemyAoiSpatialRepository:
        return self._resolve("aoi_spatial_repository", SQLAlchemyAoiSpatialRepository, db)

    def aoi_data_repository(self, db: Session) -> SQLAlchemyAoiDataRepository:
        return self._resolve("aoi_data_repository", SQLAlchemyAoiDataRepository, db)

    def signal_repository(self, db: Session) -> SQLAlchemySignalRepository:
        return self._resolve("signal_repository", SQLAlchemySignalRepository, db)

    def job_repository(self, db: Session) -> SQLAlchemyJobRepository:
        return self._resolve("job_repository", SQLAlchemyJobRepository, db)

    def correlation_repository(self, db: Session) -> SQLAlchemyCorrelationRepository:
        return self._resolve("correlation_repository", SQLAlchemyCorrelationRepository, db)

    def nitrogen_repository(self, db: Session) -> SQLAlchemyNitrogenRepository:
        return self._resolve("nitrogen_repository", SQLAlchemyNitrogenRepository, db)

    def radar_data_repository(self, db: Session) -> SQLAlchemyRadarDataRepository:
        return self._resolve("radar_data_repository", SQLAlchemyRadarDataRepository, db)

    def weather_data_repository(self, db: Session) -> SQLAlchemyWeatherDataRepository:
        return self._resolve("weather_data_repository", SQLAlchemyWeatherDataRepository, db)

    def system_admin_repository(self, db: Session) -> SQLAlchemySystemAdminRepository:
        return self._resolve("system_admin_repository", SQLAlchemySystemAdminRepository, db)

    def tenant_admin_repository(self, db: Session) -> SQLAlchemyTenantAdminRepository:
        return self._resolve("tenant_admin_repository", SQLAlchemyTenantAdminRepository, db)

    def ai_assistant_repository(self, db: Session) -> SQLAlchemyAiAssistantRepository:
        return self._resolve("ai_assistant_repository", SQLAlchemyAiAssistantRepository, db)

    def geocoding_provider(self) -> NominatimAdapter:
        return self._resolve("geocoding_provider", NominatimAdapter)

    # Use cases (application)
    def create_farm_use_case(self, db: Session) -> CreateFarmUseCase:
        return CreateFarmUseCase(self.farm_repository(db))

    def list_farms_use_case(self, db: Session) -> ListFarmsUseCase:
        return ListFarmsUseCase(self.farm_repository(db))

    def create_aoi_use_case(self, db: Session) -> CreateAoiUseCase:
        return CreateAoiUseCase(self.aoi_repository(db))

    def list_aois_use_case(self, db: Session) -> ListAoisUseCase:
        return ListAoisUseCase(self.aoi_repository(db))

    def update_aoi_use_case(self, db: Session) -> UpdateAoiUseCase:
        return UpdateAoiUseCase(self.aoi_repository(db))

    def delete_aoi_use_case(self, db: Session) -> DeleteAoiUseCase:
        return DeleteAoiUseCase(self.aoi_repository(db))

    def aoi_assets_use_case(self, db: Session) -> AoiAssetsUseCase:
        return AoiAssetsUseCase(self.aoi_data_repository(db))

    def aoi_history_use_case(self, db: Session) -> AoiHistoryUseCase:
        return AoiHistoryUseCase(self.aoi_data_repository(db))

    def request_backfill_use_case(self, db: Session) -> RequestBackfillUseCase:
        queue = self.message_queue()
        return RequestBackfillUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )

    def tile_use_case(self, db: Session) -> GetAoiTileUseCase:
        return GetAoiTileUseCase(self.aoi_spatial_repository(db))

    def tilejson_use_case(self, db: Session) -> GetAoiTileJsonUseCase:
        return GetAoiTileJsonUseCase(
            repo=self.aoi_spatial_repository(db),
            api_base_url=getattr(settings, "api_base_url", "http://localhost:8000"),
            cdn_enabled=getattr(settings, "cdn_enabled", False),
            cdn_tiles_url=getattr(settings, "cdn_tiles_url", None),
        )

    def tile_export_use_case(self, db: Session) -> RequestAoiExportUseCase:
        return RequestAoiExportUseCase(
            repo=self.aoi_spatial_repository(db),
            storage=self.object_storage(),
        )

    def tile_export_status_use_case(self) -> GetAoiExportStatusUseCase:
        return GetAoiExportStatusUseCase(storage=self.object_storage())

    def tile_export_generate_use_case(self, db: Session) -> GenerateAoiExportUseCase:
        return GenerateAoiExportUseCase(
            repo=self.aoi_spatial_repository(db),
            storage=self.object_storage(),
            tiler_url=getattr(settings, "tiler_url", "http://tiler:8080"),
        )

    def list_tenants_use_case(self, db: Session) -> ListTenantsUseCase:
        return ListTenantsUseCase(self.system_admin_repository(db))

    def create_tenant_use_case(self, db: Session) -> CreateTenantUseCase:
        return CreateTenantUseCase(self.system_admin_repository(db))

    def update_tenant_use_case(self, db: Session) -> UpdateTenantUseCase:
        return UpdateTenantUseCase(self.system_admin_repository(db))

    def list_system_jobs_use_case(self, db: Session) -> ListSystemJobsUseCase:
        return ListSystemJobsUseCase(self.system_admin_repository(db))

    def system_retry_job_use_case(self, db: Session) -> SystemRetryJobUseCase:
        return SystemRetryJobUseCase(self.system_admin_repository(db))

    def reprocess_missing_aois_use_case(self, db: Session) -> ReprocessMissingAoisUseCase:
        queue = self.message_queue()
        return ReprocessMissingAoisUseCase(
            repo=self.system_admin_repository(db),
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
            pipeline_version=settings.pipeline_version,
        )

    def list_missing_weeks_use_case(self, db: Session) -> ListMissingWeeksUseCase:
        return ListMissingWeeksUseCase(self.system_admin_repository(db))

    def reprocess_missing_weeks_use_case(self, db: Session) -> ReprocessMissingWeeksUseCase:
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

    def system_health_use_case(self, db: Session) -> SystemHealthUseCase:
        return SystemHealthUseCase(self.system_admin_repository(db))

    def queue_stats_use_case(self, db: Session) -> QueueStatsUseCase:
        return QueueStatsUseCase(self.system_admin_repository(db))

    def global_audit_log_use_case(self, db: Session) -> GlobalAuditLogUseCase:
        return GlobalAuditLogUseCase(self.system_admin_repository(db))

    def list_tenant_members_use_case(self, db: Session) -> ListMembersUseCase:
        return ListMembersUseCase(self.tenant_admin_repository(db))

    def invite_tenant_member_use_case(self, db: Session) -> InviteMemberUseCase:
        return InviteMemberUseCase(self.tenant_admin_repository(db))

    def update_member_role_use_case(self, db: Session) -> UpdateMemberRoleUseCase:
        return UpdateMemberRoleUseCase(self.tenant_admin_repository(db))

    def update_member_status_use_case(self, db: Session) -> UpdateMemberStatusUseCase:
        return UpdateMemberStatusUseCase(self.tenant_admin_repository(db))

    def get_tenant_settings_use_case(self, db: Session) -> GetTenantSettingsUseCase:
        return GetTenantSettingsUseCase(self.tenant_admin_repository(db))

    def update_tenant_settings_use_case(self, db: Session) -> UpdateTenantSettingsUseCase:
        return UpdateTenantSettingsUseCase(self.tenant_admin_repository(db))

    def tenant_audit_log_use_case(self, db: Session) -> GetTenantAuditLogUseCase:
        return GetTenantAuditLogUseCase(self.tenant_admin_repository(db))

    def create_ai_thread_use_case(self, db: Session) -> CreateThreadUseCase:
        return CreateThreadUseCase(self.ai_assistant_repository(db))

    def list_ai_threads_use_case(self, db: Session) -> ListThreadsUseCase:
        return ListThreadsUseCase(self.ai_assistant_repository(db))

    def ai_messages_use_case(self, db: Session) -> GetMessagesUseCase:
        return GetMessagesUseCase(self.ai_assistant_repository(db))

    def list_ai_approvals_use_case(self, db: Session) -> ListApprovalsUseCase:
        return ListApprovalsUseCase(self.ai_assistant_repository(db))

    def ai_approval_thread_use_case(self, db: Session) -> GetApprovalThreadUseCase:
        return GetApprovalThreadUseCase(self.ai_assistant_repository(db))

    def geocode_use_case(self) -> GeocodeUseCase:
        return GeocodeUseCase(self.geocoding_provider())

    def list_signals_use_case(self, db: Session) -> ListSignalsUseCase:
        return ListSignalsUseCase(self.signal_repository(db))

    def get_signal_use_case(self, db: Session) -> GetSignalUseCase:
        return GetSignalUseCase(self.signal_repository(db))

    def ack_signal_use_case(self, db: Session) -> AckSignalUseCase:
        return AckSignalUseCase(self.signal_repository(db))

    def list_jobs_use_case(self, db: Session) -> ListJobsUseCase:
        return ListJobsUseCase(self.job_repository(db))

    def get_job_use_case(self, db: Session) -> GetJobUseCase:
        return GetJobUseCase(self.job_repository(db))

    def list_job_runs_use_case(self, db: Session) -> ListJobRunsUseCase:
        return ListJobRunsUseCase(self.job_repository(db))

    def retry_job_use_case(self, db: Session) -> RetryJobUseCase:
        return RetryJobUseCase(self.job_repository(db))

    def cancel_job_use_case(self, db: Session) -> CancelJobUseCase:
        return CancelJobUseCase(self.job_repository(db))

    def correlation_use_case(self, db: Session) -> CorrelationUseCase:
        return CorrelationUseCase(self.correlation_repository(db))

    def year_over_year_use_case(self, db: Session) -> YearOverYearUseCase:
        return YearOverYearUseCase(self.correlation_repository(db))

    def nitrogen_use_case(self, db: Session) -> GetNitrogenStatusUseCase:
        return GetNitrogenStatusUseCase(self.nitrogen_repository(db))

    def radar_history_use_case(self, db: Session) -> GetRadarHistoryUseCase:
        return GetRadarHistoryUseCase(self.radar_data_repository(db))

    def weather_history_use_case(self, db: Session) -> GetWeatherHistoryUseCase:
        return GetWeatherHistoryUseCase(self.weather_data_repository(db))

    def request_weather_sync_use_case(self, db: Session) -> RequestWeatherSyncUseCase:
        queue = self.message_queue()
        return RequestWeatherSyncUseCase(
            job_repo=self.job_repository(db),
            queue=queue,
            queue_name=settings.sqs_queue_name,
        )
