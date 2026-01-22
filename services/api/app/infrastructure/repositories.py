from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from uuid import UUID
from app.infrastructure.models import Identity, Tenant, Membership, Farm, AOI, OpportunitySignal


class IdentityRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, identity_id: UUID) -> Optional[Identity]:
        return self.db.query(Identity).filter(Identity.id == identity_id).first()
    
    def get_by_provider_subject(self, provider: str, subject: str) -> Optional[Identity]:
        return self.db.query(Identity).filter(
            Identity.provider == provider,
            Identity.subject == subject
        ).first()
    
    def create(self, provider: str, subject: str, email: str, name: str) -> Identity:
        identity = Identity(
            provider=provider,
            subject=subject,
            email=email,
            name=name,
            status="ACTIVE"
        )
        self.db.add(identity)
        self.db.commit()
        self.db.refresh(identity)
        return identity


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def create(self, type: str, name: str, plan: str = "BASIC") -> Tenant:
        tenant = Tenant(
            type=type,
            name=name,
            status="ACTIVE",
            plan=plan,
            quotas={}
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, membership_id: UUID) -> Optional[Membership]:
        return self.db.query(Membership).filter(Membership.id == membership_id).first()
    
    def get_by_identity(self, identity_id: UUID) -> List[Membership]:
        return self.db.query(Membership).filter(
            Membership.identity_id == identity_id
        ).all()
    
    def get_by_tenant_identity(self, tenant_id: UUID, identity_id: UUID) -> Optional[Membership]:
        return self.db.query(Membership).filter(
            Membership.tenant_id == tenant_id,
            Membership.identity_id == identity_id
        ).first()
    
    def create(self, tenant_id: UUID, identity_id: UUID, role: str) -> Membership:
        membership = Membership(
            tenant_id=tenant_id,
            identity_id=identity_id,
            role=role,
            status="ACTIVE"
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership


class FarmRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, farm_id: UUID, tenant_id: UUID) -> Optional[Farm]:
        # Query farm with active AOI count
        result = self.db.query(
            Farm,
            func.count(AOI.id).label('aoi_count')
        ).outerjoin(
            AOI, 
            (AOI.farm_id == Farm.id) & (AOI.status == 'ACTIVE')
        ).filter(
            Farm.id == farm_id,
            Farm.tenant_id == tenant_id
        ).group_by(
            Farm.id
        ).first()

        if result:
            farm, count = result
            farm.aoi_count = count
            return farm
        return None
    
    def list_by_tenant(self, tenant_id: UUID) -> List[Farm]:
        # Query farm with active AOI count
        result = self.db.query(
            Farm,
            func.count(AOI.id).label('aoi_count')
        ).outerjoin(
            AOI, 
            (AOI.farm_id == Farm.id) & (AOI.status == 'ACTIVE')
        ).filter(
            Farm.tenant_id == tenant_id
        ).group_by(
            Farm.id
        ).order_by(Farm.created_at.desc()).all()
        
        # Merge count into Farm object for Pydantic
        farms = []
        for farm, count in result:
            farm.aoi_count = count
            farms.append(farm)
            
        return farms
    
    def create(self, tenant_id: UUID, name: str, timezone: str) -> Farm:
        farm = Farm(
            tenant_id=tenant_id,
            name=name,
            timezone=timezone
        )
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        return farm


class AOIRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, aoi_id: UUID, tenant_id: UUID) -> Optional[AOI]:
        return self.db.query(AOI).filter(
            AOI.id == aoi_id,
            AOI.tenant_id == tenant_id
        ).first()
    
    def list_by_tenant(self, tenant_id: UUID) -> List[AOI]:
        return self.db.query(AOI).filter(
            AOI.tenant_id == tenant_id,
            AOI.status == "ACTIVE"
        ).order_by(AOI.created_at.desc()).all()
    
    def count_by_tenant(self, tenant_id: UUID) -> int:
        return self.db.query(AOI).filter(
            AOI.tenant_id == tenant_id,
            AOI.status == "ACTIVE"
        ).count()


class SignalRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, signal_id: UUID, tenant_id: UUID) -> Optional[OpportunitySignal]:
        return self.db.query(OpportunitySignal).filter(
            OpportunitySignal.id == signal_id,
            OpportunitySignal.tenant_id == tenant_id
        ).first()
    
    def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
        limit: int = 20
    ) -> List[OpportunitySignal]:
        query = self.db.query(OpportunitySignal).filter(
            OpportunitySignal.tenant_id == tenant_id
        )
        
        if status:
            query = query.filter(OpportunitySignal.status == status)
        
        if signal_type:
            query = query.filter(OpportunitySignal.signal_type == signal_type)
        
        return query.order_by(
            OpportunitySignal.created_at.desc()
        ).limit(limit).all()
