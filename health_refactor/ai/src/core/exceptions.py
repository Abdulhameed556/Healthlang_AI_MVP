"""Shared exception hierarchy."""


class AIServiceError(Exception):
    pass

class UnauthorizedError(AIServiceError):
    pass

class ForbiddenError(AIServiceError):
    pass

class NotFoundError(AIServiceError):
    pass

class PipelineError(AIServiceError):
    pass

class IndexingError(AIServiceError):
    pass

class LLMError(AIServiceError):
    pass

class ToolExecutionError(AIServiceError):
    pass
