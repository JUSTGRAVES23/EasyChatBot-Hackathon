from backend.runtime.context.execution_context import ExecutionContext


def test_execution_context_creation():

    context = ExecutionContext(
        user_id="demo-user",
        request="Discuss today's technology news"
    )

    assert context.user_id == "demo-user"

    assert context.request == (
        "Discuss today's technology news"
    )

    assert context.execution_id is not None

    assert context.created_at is not None


def test_execution_context_is_immutable():

    context = ExecutionContext(
        user_id="demo-user",
        request="Hello"
    )

    try:
        context.user_id = "changed"
        assert False

    except Exception:
        assert True