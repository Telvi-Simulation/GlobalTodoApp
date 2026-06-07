from pydantic import BaseModel, EmailStr, constr, validator, Extra
from uuid import UUID

class OnboardRequest(BaseModel):
    user_id: UUID
    tenant_id: UUID
    full_name: constr(min_length=1, max_length=100)
    email: EmailStr
    initial_site_name: constr(min_length=1, max_length=150)
    consent_marketing: bool = False
    consent_terms: bool

    class Config:
        extra = Extra.forbid

    @validator("consent_terms")
    def consent_terms_must_be_true(cls, v):
        if v is not True:
            raise ValueError("consent_terms must be true")
        return v
