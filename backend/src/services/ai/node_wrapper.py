import asyncio
import logging
from collections.abc import Awaitable, Callable

from pydantic import ValidationError

from src.schemas.findings import Finding
from src.schemas.state import ReviewState

logger = logging.getLogger(__name__)

SpecialistFn = Callable[[ReviewState], Awaitable[list[Finding]]]


def specialist_node(name: str, timeout_seconds: int, retries: int) -> Callable[[SpecialistFn], Callable[[ReviewState], Awaitable[dict[str, object]]]]:
    def decorator(fn: SpecialistFn) -> Callable[[ReviewState], Awaitable[dict[str, object]]]:
        async def wrapped(state: ReviewState) -> dict[str, object]:
            last_error: Exception | None = None

            for attempt in range(retries + 1):
                try:
                    result = await asyncio.wait_for(fn(state), timeout=timeout_seconds)
                except TimeoutError:
                    logger.warning("%s timed out after %ss", name, timeout_seconds)
                    return {"findings": [], "specialists_failed": [name]}
                except ValidationError as exc:
                    last_error = exc
                    logger.warning(
                        "%s produced invalid output on attempt %d/%d: %s",
                        name,
                        attempt + 1,
                        retries + 1,
                        exc,
                    )
                    continue
                except Exception:
                    logger.exception("%s raised an unexpected error", name)
                    return {"findings": [], "specialists_failed": [name]}
                else:
                    return {"findings": result, "specialists_run": [name]}

            logger.warning("%s dropped after %d attempts: %s", name, retries + 1, last_error)
            return {"findings": [], "specialists_failed": [name]}

        return wrapped

    return decorator
