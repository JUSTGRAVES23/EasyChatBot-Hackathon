"""
Tests for Voice Call Event Repository Contract.

Validates:
- Repository interface behaviour.
- Event persistence contract.
"""

import pytest


from app.application.uai.voice.voice_call_event_repository import (
    VoiceCallEventRepository,
)



def test_repository_is_abstract():

    with pytest.raises(
        TypeError
    ):

        VoiceCallEventRepository()



