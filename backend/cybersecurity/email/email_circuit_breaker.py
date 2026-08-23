"""
Email Circuit Breaker.

Protects email delivery from repeated failures.

States:

CLOSED
    |
    v
OPEN
    |
    v
HALF_OPEN


Does NOT:
- send emails;
- manage providers;
- generate reports.
"""

from __future__ import annotations

from datetime import datetime, timedelta



class EmailCircuitBreaker:


    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_minutes: int = 30,
    ) -> None:


        self.failure_threshold = (
            failure_threshold
        )


        self.cooldown = timedelta(
            minutes=cooldown_minutes
        )


        self.failures = 0


        self.open_until = None



    def allow_request(
        self,
    ) -> bool:


        if self.open_until is None:

            return True


        if datetime.utcnow() >= self.open_until:

            return True


        return False



    def record_success(
        self,
    ) -> None:


        self.failures = 0

        self.open_until = None



    def record_failure(
        self,
    ) -> None:


        self.failures += 1


        if (
            self.failures
            >= self.failure_threshold
        ):

            self.open_until = (
                datetime.utcnow()
                +
                self.cooldown
            )



    def status(
        self,
    ) -> dict:


        return {

            "failures":
                self.failures,

            "open":
                self.open_until is not None,

            "open_until":
                self.open_until,

        }