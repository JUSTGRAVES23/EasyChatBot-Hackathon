"""
===============================================================================

File
----
tests/application/voice/test_voice_quality_evaluation_flow.py


Purpose
-------
Regression tests for voice quality evaluation flow.


Architecture Flow
-----------------

Generated Audio

        |

        v

Voice Quality Evaluation Boundary

        |

        v

Quality Result


Validated Behaviour
-------------------

✓ Generated audio can be evaluated

✓ Quality evaluator boundary is isolated

✓ Voice metadata is preserved

✓ Failed quality evaluation is handled

✓ Quality result remains traceable


===============================================================================
"""


from __future__ import annotations


from dataclasses import dataclass





# ============================================================================
# Fake Quality Evaluation Boundary
# ============================================================================


@dataclass(frozen=True)
class VoiceQualityResult:
    """
    Result returned by quality evaluation.
    """

    score: float

    passed: bool

    metadata: dict





class FakeVoiceQualityEvaluator:
    """
    Fake quality evaluator boundary.

    Production implementation can later connect
    to the Quality Management framework.
    """


    def __init__(self):

        self.received_audio = None

        self.received_metadata = None



    def evaluate(
        self,
        *,
        audio,
        metadata,
    ):

        self.received_audio = audio

        self.received_metadata = metadata


        return VoiceQualityResult(

            score=95.0,

            passed=True,

            metadata=metadata,

        )





class FailingVoiceQualityEvaluator:
    """
    Fake failing evaluator.
    """


    def evaluate(
        self,
        *,
        audio,
        metadata,
    ):

        raise RuntimeError(
            "Quality evaluation unavailable."
        )





# ============================================================================
# Tests
# ============================================================================


def test_voice_quality_evaluation_receives_generated_audio():

    evaluator = FakeVoiceQualityEvaluator()


    result = evaluator.evaluate(

        audio=b"generated-audio",

        metadata={

            "character_id": "clara",

            "language": "French",

        },

    )


    assert evaluator.received_audio == (
        b"generated-audio"
    )


    assert result.passed is True





def test_voice_quality_evaluation_preserves_voice_metadata():

    evaluator = FakeVoiceQualityEvaluator()


    metadata = {

        "character_id": "clara",

        "language": "French",

        "interaction_type": "conversation",

    }


    result = evaluator.evaluate(

        audio=b"audio",

        metadata=metadata,

    )


    assert (
        result.metadata
        ==
        metadata
    )


    assert (
        evaluator.received_metadata
        ==
        metadata
    )





def test_voice_quality_score_is_traceable():

    evaluator = FakeVoiceQualityEvaluator()


    result = evaluator.evaluate(

        audio=b"audio",

        metadata={

            "trace_id": "trace-001"

        },

    )


    assert result.score == 95.0


    assert (
        result.metadata["trace_id"]
        ==
        "trace-001"
    )





def test_voice_quality_failure_is_visible():

    evaluator = FailingVoiceQualityEvaluator()


    try:

        evaluator.evaluate(

            audio=b"audio",

            metadata={},

        )


        assert False, (
            "Expected quality evaluation failure."
        )


    except RuntimeError as exc:

        assert (
            "quality"
            in str(exc).lower()
        )





def test_voice_quality_boundary_does_not_modify_audio():

    evaluator = FakeVoiceQualityEvaluator()


    audio = b"original-audio"


    evaluator.evaluate(

        audio=audio,

        metadata={},

    )


    assert (
        evaluator.received_audio
        ==
        audio
    )