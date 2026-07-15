"""Unit tests: core/exceptions.py"""
import pytest

from ai.src.core.exceptions import (
    AIServiceError,
    ForbiddenError,
    IndexingError,
    LLMError,
    NotFoundError,
    PipelineError,
    ToolExecutionError,
    UnauthorizedError,
)


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_ai_service_error(self):
        for exc in (
            UnauthorizedError,
            ForbiddenError,
            NotFoundError,
            PipelineError,
            IndexingError,
            LLMError,
            ToolExecutionError,
        ):
            assert issubclass(exc, AIServiceError)

    def test_exceptions_can_be_raised_with_message(self):
        with pytest.raises(LLMError, match="rate limit"):
            raise LLMError("rate limit")
