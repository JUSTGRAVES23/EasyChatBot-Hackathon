from datetime import datetime, timezone

class PrivacyAuditService:
    def create_record(self, action: str, subject_hash: str):
        return {'action': action, 'subject_hash': subject_hash, 'created_at': datetime.now(timezone.utc)}
