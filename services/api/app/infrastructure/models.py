from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
from app.database import Base


class Identity(Base):
    __tablename__ = "identities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('provider', 'subject'),
        UniqueConstraint('email'),
    )


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False, default="COMPANY")
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    plan = Column(String, nullable=False, default="BASIC")
    quotas = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('tenants_type_status_idx', 'type', 'status'),
    )


class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('identities.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False, default="VIEWER")
    status = Column(String, nullable=False, default="ACTIVE")
    invited_by_membership_id = Column(UUID(as_uuid=True), ForeignKey('memberships.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'identity_id'),
        Index('memberships_tenant_role_idx', 'tenant_id', 'role'),
        Index('memberships_identity_idx', 'identity_id'),
    )


class SystemAdmin(Base):
    __tablename__ = "system_admins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id = Column(UUID(as_uuid=True), ForeignKey('identities.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False, default="SYSTEM_ADMIN")
    status = Column(String, nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('identity_id'),
    )


class Farm(Base):
    __tablename__ = "farms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    timezone = Column(String, nullable=False, default="America/Sao_Paulo")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('farms_tenant_idx', 'tenant_id'),
    )


class AOI(Base):
    __tablename__ = "aois"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    farm_id = Column(UUID(as_uuid=True), ForeignKey('farms.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    use_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    geom = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)
    area_ha = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('aois_geom_gist', 'geom', postgresql_using='gist'),
        Index('aois_tenant_farm_idx', 'tenant_id', 'farm_id', 'status'),
    )


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    aoi_id = Column(UUID(as_uuid=True), ForeignKey('aois.id', ondelete='SET NULL'), nullable=True)
    job_type = Column(String, nullable=False)
    job_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    payload_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'job_key'),
        Index('jobs_filter_idx', 'tenant_id', 'status', 'job_type', 'created_at'),
        Index('jobs_aoi_time_idx', 'tenant_id', 'aoi_id', 'created_at'),
    )


class OpportunitySignal(Base):
    __tablename__ = "opportunity_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    aoi_id = Column(UUID(as_uuid=True), ForeignKey('aois.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    pipeline_version = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    severity = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    model_version = Column(String, nullable=False)
    change_method = Column(String, nullable=False)
    evidence_json = Column(JSONB, nullable=False)
    features_json = Column(JSONB, nullable=False)
    recommended_actions = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'aoi_id', 'year', 'week', 'pipeline_version', 'signal_type'),
        Index('signals_filter_idx', 'tenant_id', 'status', 'signal_type', 'created_at'),
        Index('signals_aoi_time_idx', 'tenant_id', 'aoi_id', 'year', 'week'),
    )


class CopilotThread(Base):
    __tablename__ = "copilot_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    aoi_id = Column(UUID(as_uuid=True), ForeignKey('aois.id', ondelete='SET NULL'), nullable=True)
    signal_id = Column(UUID(as_uuid=True), ForeignKey('opportunity_signals.id', ondelete='SET NULL'), nullable=True)
    created_by_membership_id = Column(UUID(as_uuid=True), ForeignKey('memberships.id', ondelete='SET NULL'), nullable=True)
    status = Column(String, nullable=False, default="OPEN")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('copilot_threads_idx', 'tenant_id', 'created_at'),
    )


class CopilotApproval(Base):
    __tablename__ = "copilot_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey('copilot_threads.id', ondelete='CASCADE'), nullable=False)
    requested_by_system = Column(Boolean, nullable=False, default=True)
    tool_name = Column(String, nullable=False)
    tool_payload = Column(JSONB, nullable=False)
    decision = Column(String, nullable=False, default="PENDING")
    decided_by_membership_id = Column(UUID(as_uuid=True), ForeignKey('memberships.id', ondelete='SET NULL'), nullable=True)
    decision_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('copilot_approvals_idx', 'tenant_id', 'decision', 'created_at'),
    )
