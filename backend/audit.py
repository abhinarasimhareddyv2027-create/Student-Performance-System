from sqlalchemy.orm import Session

from database.academic_models import AuditEvent
from services.auth_service import AuthenticatedUser


def record_audit(
    session: Session,
    actor: AuthenticatedUser,
    action: str,
    entity: str,
    entity_id: int | None,
) -> None:
    session.add(
        AuditEvent(
            actor_user_id=actor.id,
            action=action,
            entity_type=entity,
            entity_id=entity_id,
        )
    )