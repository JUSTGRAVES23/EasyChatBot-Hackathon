"""
Cybersecurity Decision Support API.

Provides human decision-support reports.

Does NOT:
- execute remediation;
- modify security systems;
- perform autonomous actions.
"""

from fastapi import APIRouter


from cybersecurity.decision_support.service import (
    CybersecurityDecisionSupportService,
)



router = APIRouter(

    prefix="/api/cybersecurity-center",

    tags=[
        "cybersecurity-center"
    ],

)



_service = (
    CybersecurityDecisionSupportService()
)



@router.post(
    "/decision-brief"
)
async def create_decision_brief(
    intelligence: dict,
):

    """
    Generate a cybersecurity decision brief.

    Input:
        Cybersecurity intelligence context.

    Output:
        Human decision-support information.
    """


    result = await _service.create_brief(
        intelligence
    )


    return result

