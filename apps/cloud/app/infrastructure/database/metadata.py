"""Import all frozen Stage 1A mappings for Alembic and metadata tests."""

from sqlalchemy import MetaData

from app.infrastructure.database.base import Base
from app.modules.audit import models as audit_models
from app.modules.device_fleet import models as device_fleet_models
from app.modules.device_operations import models as device_operations_models
from app.modules.jobs import models as job_models
from app.modules.organizations import models as organization_models

_REGISTERED_MODEL_MODULES = (
    audit_models,
    device_fleet_models,
    device_operations_models,
    job_models,
    organization_models,
)

metadata: MetaData = Base.metadata

__all__ = ["metadata"]
