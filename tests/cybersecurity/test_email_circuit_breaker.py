import pytest


from cybersecurity.email.email_circuit_breaker import (
    EmailCircuitBreaker,
)



def test_email_circuit_opens_after_failures():


    breaker = EmailCircuitBreaker(
        failure_threshold=3
    )


    breaker.record_failure()

    breaker.record_failure()

    breaker.record_failure()



    status = breaker.status()


    assert (
        status["open"]
        is True
    )

