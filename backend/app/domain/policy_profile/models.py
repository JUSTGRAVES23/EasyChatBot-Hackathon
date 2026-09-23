from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from uuid import UUID


class AgePolicyClassification(str, Enum):
    ADULT = "adult"
    STUDENT = "student"
    UNDER_15 = "under_15"
    AGE_15_TO_17 = "age_15_to_17"


@dataclass(frozen=True, slots=True)
class UserPolicyProfile:
    user_id: UUID
    date_of_birth: date
    age_policy_classification: AgePolicyClassification
    jurisdiction: str
    policy_version: str
