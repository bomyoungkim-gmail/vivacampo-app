import types

from worker.application.dtos.signals_week import SignalsWeekCommand
from worker.application.use_cases import signals_week as signals_module
from worker.application.use_cases.signals_week import SignalsWeekUseCase
from worker.config import settings
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.signals_provider import AoiInfoRepository, SignalRepository, SignalsObservationsRepository


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.status = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status.append((job_id, status, error_message))

    def upsert_job(self, *, tenant_id: str, aoi_id: str, job_type: str, job_key: str, payload: dict):
        return None

    def commit(self) -> None:
        return None


class FakeObservationsRepository(SignalsObservationsRepository):
    def __init__(self, observations):
        self._observations = observations

    def list_recent(self, *, tenant_id: str, aoi_id: str, limit: int):
        return self._observations


class FakeAoiInfoRepository(AoiInfoRepository):
    def get_use_type(self, *, tenant_id: str, aoi_id: str) -> str:
        return "PASTURE"


class FakeSignalRepository(SignalRepository):
    def __init__(self):
        self.created = []

    def get_existing(self, *, tenant_id: str, aoi_id: str, year: int, week: int, signal_type: str, pipeline_version: str):
        return None

    def update_signal(self, *, signal_id: str, score: float, evidence: dict, features: dict) -> None:
        return None

    def create_signal(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        signal_type: str,
        severity: str,
        confidence: str,
        score: float,
        evidence: dict,
        features: dict,
        recommended_actions: list,
        created_at,
        pipeline_version: str,
        model_version: str,
        change_method: str,
    ) -> None:
        self.created.append(signal_type)


def test_signals_week_insufficient_history():
    original_min_weeks = settings.signals_min_history_weeks
    settings.signals_min_history_weeks = 3
    use_case = SignalsWeekUseCase(
        job_repo=FakeJobRepository(),
        observations_repo=FakeObservationsRepository([]),
        aoi_repo=FakeAoiInfoRepository(),
        signal_repo=FakeSignalRepository(),
    )

    command = SignalsWeekCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.reason == "insufficient_history"
    settings.signals_min_history_weeks = original_min_weeks


def test_signals_week_creates_signal():
    observations = [
        {"baseline": 0.6, "valid_pixel_ratio": 0.9},
        {"baseline": 0.6, "valid_pixel_ratio": 0.8},
    ]

    original_min_weeks = settings.signals_min_history_weeks
    original_threshold = settings.signals_score_threshold
    settings.signals_min_history_weeks = 2
    settings.signals_score_threshold = 0.1

    signal_repo = FakeSignalRepository()
    use_case = SignalsWeekUseCase(
        job_repo=FakeJobRepository(),
        observations_repo=FakeObservationsRepository(observations),
        aoi_repo=FakeAoiInfoRepository(),
        signal_repo=signal_repo,
    )

    # Patch scoring functions to keep deterministic
    original_extract = signals_module.extract_features
    original_rule = signals_module.calculate_rule_score
    original_change = signals_module.calculate_change_score
    original_ml = signals_module.calculate_ml_score
    original_final = signals_module.calculate_final_score
    original_signal = signals_module.determine_signal_type
    original_actions = signals_module.get_recommended_actions
    original_severity = signals_module.determine_severity
    original_confidence = signals_module.determine_confidence
    original_detect = signals_module.detect_change_simple

    signals_module.extract_features = lambda obs: {"ok": True}
    signals_module.calculate_rule_score = lambda features, use_type: 0.9
    signals_module.calculate_change_score = lambda change: 0.9
    signals_module.calculate_ml_score = lambda features: 0.9
    signals_module.calculate_final_score = lambda rule, change, ml: 0.95
    signals_module.determine_signal_type = lambda use_type, features, change: "FERTILIZATION"
    signals_module.get_recommended_actions = lambda signal_type: ["action"]
    signals_module.determine_severity = lambda score: "HIGH"
    signals_module.determine_confidence = lambda score, ratio, count: "HIGH"
    signals_module.detect_change_simple = lambda obs: {}

    command = SignalsWeekCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    try:
        result = use_case.execute(command)
    finally:
        signals_module.extract_features = original_extract
        signals_module.calculate_rule_score = original_rule
        signals_module.calculate_change_score = original_change
        signals_module.calculate_ml_score = original_ml
        signals_module.calculate_final_score = original_final
        signals_module.determine_signal_type = original_signal
        signals_module.get_recommended_actions = original_actions
        signals_module.determine_severity = original_severity
        signals_module.determine_confidence = original_confidence
        signals_module.detect_change_simple = original_detect
        settings.signals_min_history_weeks = original_min_weeks
        settings.signals_score_threshold = original_threshold

    assert result.status == "OK"
    assert result.signal_type == "FERTILIZATION"
    assert signal_repo.created == ["FERTILIZATION"]
