from fastapi import APIRouter, HTTPException

from opsml_artifacts.app.core.config import config
from opsml_artifacts.app.routes.models import HealthCheckResult

router = APIRouter()


@router.get("/healthcheck", response_model=HealthCheckResult, name="healthcheck")
def get_healthcheck() -> HealthCheckResult:
    return HealthCheckResult(is_alive=True)


@router.get("/debug")
async def debug() -> dict[str, str]:

    return {
        "url": config.TRACKING_URI,
        "storage": config.STORAGE_URI,
        "app_env": config.APP_ENV,
    }


@router.get(
    "/error",
    description="An endpoint that will return a 500 error for debugging and alert testing",
)
def get_error() -> None:
    raise HTTPException(status_code=500)
