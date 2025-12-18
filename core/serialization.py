# core/serialization.py

from __future__ import annotations
from typing import Dict, Any
from .models import Alert


def alert_to_dict(alert: Alert) -> Dict[str, Any]:
    return {
        "id": alert.id,
        "sphere": alert.sphere.value,
        "persona": alert.persona.value,
        "priority": alert.priority.value,
        "title": alert.title,
        "message": alert.message,
        "created_at": alert.created_at.isoformat(),
        "estimated_impact": alert.estimated_impact,
        "reliability_score": alert.reliability_score,
        "reliability": alert.reliability.value,
        "is_suppressed": alert.is_suppressed,
        "data": alert.data,
    }
