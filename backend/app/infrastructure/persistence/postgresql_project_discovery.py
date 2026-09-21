from __future__ import annotations
from datetime import timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.infrastructure.persistence.project_discovery_records import ProjectDiscoveryCandidateRecord
from app.project_control_center.domain.discovery_models import ProjectDiscoveryCandidate
from app.project_control_center.domain.discovery_ports import ProjectDiscoveryRepository

class PostgreSQLProjectDiscoveryRepository(ProjectDiscoveryRepository):
    def __init__(self, session_factory) -> None:
        if session_factory is None: raise ValueError("session_factory is required.")
        self._session_factory = session_factory

    def get(self, candidate_id):
        with self._session_factory() as session:
            record = session.get(ProjectDiscoveryCandidateRecord, candidate_id)
            return _to_domain(record) if record else None

    def list_candidates(self):
        with self._session_factory() as session:
            records = session.scalars(select(ProjectDiscoveryCandidateRecord).order_by(ProjectDiscoveryCandidateRecord.discovered_at.desc())).all()
            return [_to_domain(r) for r in records]

    def find_by_key(self, candidate_key):
        with self._session_factory() as session:
            record = session.scalar(select(ProjectDiscoveryCandidateRecord).where(ProjectDiscoveryCandidateRecord.candidate_key == candidate_key))
            return _to_domain(record) if record else None

    def save(self, candidate):
        with self._session_factory() as session:
            record = session.get(ProjectDiscoveryCandidateRecord, candidate.candidate_id)
            if record is None:
                record = ProjectDiscoveryCandidateRecord(candidate_id=candidate.candidate_id)
                session.add(record)
            record.candidate_key = candidate.candidate_key
            record.name = candidate.name
            record.description = candidate.description
            record.owner = candidate.owner
            record.source = candidate.source
            record.source_reference = candidate.source_reference
            record.status = candidate.status
            record.discovered_at = candidate.discovered_at
            record.reviewed_at = candidate.reviewed_at
            record.registered_project_id = candidate.registered_project_id
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise
            session.refresh(record)
            return _to_domain(record)

def _to_domain(record):
    discovered_at = record.discovered_at
    reviewed_at = record.reviewed_at
    if discovered_at.tzinfo is None: discovered_at = discovered_at.replace(tzinfo=timezone.utc)
    if reviewed_at is not None and reviewed_at.tzinfo is None: reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)
    return ProjectDiscoveryCandidate(
        candidate_id=record.candidate_id, candidate_key=record.candidate_key, name=record.name,
        description=record.description, owner=record.owner, source=record.source,
        source_reference=record.source_reference, status=record.status,
        discovered_at=discovered_at, reviewed_at=reviewed_at,
        registered_project_id=record.registered_project_id,
    )
