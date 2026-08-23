from dataclasses import dataclass


@dataclass
class DemoResponse:
    scenario: str
    event: dict
    email: dict
    audit: dict
    timeline: dict
    yeti_message: str
