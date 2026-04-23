from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.sql_models import AuditLog


class AuditLogService:
    """Append-only audit log writer for forensic actions."""

    @staticmethod
    def append(
        db: Session,
        action: str,
        user_id: str,
        job_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        entry = AuditLog(
            job_id=job_id,
            action=action,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            details=details or {}
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
