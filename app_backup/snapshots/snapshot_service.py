from datetime import datetime

def create_snapshot(
    dashboard_type: str,
    period: str,
    metrics: dict
):
    return {
        'dashboard_type': dashboard_type,
        'period': period,
        'created_at': datetime.utcnow().isoformat(),
        'metrics': metrics
    }
