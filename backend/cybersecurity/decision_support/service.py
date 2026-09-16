"""
Cybersecurity Decision Support Service.

Application boundary between:
- cybersecurity intelligence;
- decision support agent.

Does NOT:
- execute security actions;
- modify systems;
- contact external security tools.
"""

from __future__ import annotations


from cybersecurity.decision_support.agent.agent import (
    CybersecurityDecisionSupportAgent,
)


class CybersecurityDecisionSupportService:


    def __init__(self):

        self.agent = (
            CybersecurityDecisionSupportAgent()
        )


    async def create_brief(
        self,
        intelligence: dict,
    ):

        return await self.agent.analyse(
            intelligence
        )

