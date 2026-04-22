from fastapi import HTTPException, status


class ProfSimError(Exception):
    """Base domain exception."""
    def __init__(self, message: str, code: str = "PROFSIM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


# ── Auth ──────────────────────────────────────────────────
class AuthenticationError(ProfSimError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class TokenExpiredError(ProfSimError):
    def __init__(self):
        super().__init__("Token has expired", "TOKEN_EXPIRED")


class InvalidTokenError(ProfSimError):
    def __init__(self):
        super().__init__("Invalid token", "INVALID_TOKEN")


class PermissionDeniedError(ProfSimError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")


# ── Resource ──────────────────────────────────────────────
class NotFoundError(ProfSimError):
    def __init__(self, resource: str, identifier: str | None = None):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg, "NOT_FOUND")
        self.resource = resource


class ConflictError(ProfSimError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")


# ── Simulation ────────────────────────────────────────────
class SimulationError(ProfSimError):
    def __init__(self, message: str):
        super().__init__(message, "SIMULATION_ERROR")


class InvalidDecisionError(SimulationError):
    def __init__(self, option_key: str):
        super().__init__(f"Option '{option_key}' is not valid for the current step")
        self.code = "INVALID_DECISION"


class PreconditionNotMetError(SimulationError):
    def __init__(self, option_key: str):
        super().__init__(f"Preconditions not met for option '{option_key}'")
        self.code = "PRECONDITION_FAILED"


class SessionNotActiveError(SimulationError):
    def __init__(self, status: str):
        super().__init__(f"Session is not active (status: {status})")
        self.code = "SESSION_NOT_ACTIVE"


class ScenarioNotFoundError(NotFoundError):
    def __init__(self, scenario_id: str):
        super().__init__("Scenario", scenario_id)


# ── Rate Limiting ─────────────────────────────────────────
class RateLimitExceededError(ProfSimError):
    def __init__(self):
        super().__init__("Rate limit exceeded. Please slow down.", "RATE_LIMIT_EXCEEDED")


# ── AI ────────────────────────────────────────────────────
class AIProviderError(ProfSimError):
    def __init__(self, message: str):
        super().__init__(message, "AI_PROVIDER_ERROR")


# ── HTTP mapping ──────────────────────────────────────────
EXCEPTION_HTTP_MAP: dict[type[ProfSimError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ScenarioNotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidDecisionError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    PreconditionNotMetError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    SessionNotActiveError: status.HTTP_409_CONFLICT,
    RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
    SimulationError: status.HTTP_400_BAD_REQUEST,
    AIProviderError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def domain_exception_to_http(exc: ProfSimError) -> HTTPException:
    status_code = EXCEPTION_HTTP_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "message": exc.message},
    )
