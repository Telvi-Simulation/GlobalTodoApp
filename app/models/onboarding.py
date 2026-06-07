import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

Base = declarative_base()

class UserOnboardingData(Base):
    __tablename__ = "user_onboarding_data"

    id = sa.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(PG_UUID(as_uuid=True), nullable=False)
    tenant_id = sa.Column(PG_UUID(as_uuid=True), nullable=False)
    full_name = sa.Column(sa.String(100), nullable=False)
    email = sa.Column(sa.String(254), nullable=False)
    initial_site_name = sa.Column(sa.String(150), nullable=False)
    consent_marketing = sa.Column(sa.Boolean, default=False)
    consent_terms = sa.Column(sa.Boolean, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
