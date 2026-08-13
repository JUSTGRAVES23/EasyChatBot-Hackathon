"""
G9 Runtime Capability End-to-End Test.

Validates the official AI Runtime execution path:

Application
    |
    v
CapabilityRequest
    |
    v
CapabilityGateway
    |
    v
CapabilityRegistry
    |
    v
LiveIntelligenceExecutor
    |
    v
LiveIntelligenceAgent
    |
    v
Parallel + Gemini/Fallback
    |
    v
CapabilityResult


Validation goals:

- Runtime gateway works
- Capability registration works
- LIVE_INTELLIGENCE capability resolves
- Provider-independent execution works
- Structured intelligence is returned
"""


from __future__ import annotations

import asyncio
import uuid


from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_agents.live_intelligence_agent.composition import (
    create_live_intelligence_agent,
)



from dataclasses import dataclass


@dataclass(frozen=True)
class DemoGovernanceResult:
    """
    Minimal governance decision result.
    """

    allowed: bool = True



class DemoGovernance:
    """
    Minimal governance implementation
    matching CapabilityGateway contract.
    """

    def evaluate(
        self,
        request,
    ) -> DemoGovernanceResult:
        """
        Allow capability execution.
        """

        return DemoGovernanceResult(
            allowed=True
        )



async def main() -> None:

    print("=" * 70)
    print(
        "       G9 RUNTIME CAPABILITY END-TO-END TEST"
    )
    print("=" * 70)
    print()


    # --------------------------------------------------
    # 1. Create Live Intelligence Agent
    # --------------------------------------------------

    agent = create_live_intelligence_agent()


    executor = LiveIntelligenceExecutor(
        agent=agent,
    )


    print(
        "Live Intelligence executor: PASS"
    )


    # --------------------------------------------------
    # 2. Register capability
    # --------------------------------------------------

    registry = CapabilityRegistry(
        executors=[
            executor,
        ]
    )


    print(
        "Capability registry: PASS"
    )


    # --------------------------------------------------
    # 3. Create gateway
    # --------------------------------------------------

    gateway = CapabilityGateway(
        registry=registry,
        governance=DemoGovernance(),
    )


    print(
        "Capability gateway: PASS"
    )

    print()


    # --------------------------------------------------
    # 4. Create runtime request
    # --------------------------------------------------

    request = CapabilityRequest(
        request_id=str(
            uuid.uuid4()
        ),
        capability=CapabilityType.LIVE_INTELLIGENCE,
        payload={
            "topic": (
                "What are the most important "
                "current developments in artificial intelligence?"
            ),
            "language": "French",
            "learner_level": "B2",
        },
    )


    print(
        "Capability request created: PASS"
    )

    print()


    # --------------------------------------------------
    # 5. Execute through Runtime Gateway
    # --------------------------------------------------

    result = await gateway.execute(
        request
    )


    print(
        "========== RESULT =========="
    )

    print()


    print(
        "Status:",
        result.status,
    )


    intelligence = result.output


    print()

    print(
        "Topic:"
    )

    print(
        intelligence.topic
    )


    print()

    print(
        "Summary:"
    )

    print(
        intelligence.summary
    )


    print()

    print(
        "Sources:",
        len(
            intelligence.sources
        )
    )


    print()

    print(
        "Key information:"
    )

    for item in intelligence.key_information:
        print(
            "-",
            item
        )


    print()


    # --------------------------------------------------
    # 6. Validation
    # --------------------------------------------------

    if not intelligence.summary:
        raise RuntimeError(
            "No intelligence summary returned."
        )


    if not intelligence.key_information:
        raise RuntimeError(
            "No key information returned."
        )


    print(
        "Structured intelligence: PASS"
    )


    print()

    print("=" * 70)

    print(
        "G9_RUNTIME_CAPABILITY_END_TO_END_SUCCESS"
    )

    print("=" * 70)



if __name__ == "__main__":
    asyncio.run(main())