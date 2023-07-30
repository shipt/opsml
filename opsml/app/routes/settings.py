# pylint: disable=protected-access
from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from opsml import version
from opsml.app.core.config import config
from opsml.app.routes.pydantic_models import StorageSettingsResponse
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.storage.storage_system import StorageSystem

logger = ArtifactLogger.get_logger(__name__)

router = APIRouter()


@router.get("/settings", response_model=StorageSettingsResponse, name="settings")
def get_storage_settings() -> StorageSettingsResponse:
    """Returns backend storage path and type"""

    storage_type = StorageSystem.LOCAL.value
    if bool(config.STORAGE_URI):
        if not config.is_proxy and "gs://" in config.STORAGE_URI:
            storage_type = StorageSystem.GCS.value
        if config.is_proxy:
            # this should setup the api storage client
            storage_type = StorageSystem.API.value

    return StorageSettingsResponse(
        storage_type=storage_type,
        storage_uri=config.STORAGE_URI,
        proxy=config.is_proxy,
        version=version.__version__,
    )


@router.get("/home", name="home")
def home(request: Request):
    redirect_url = request.url_for("/")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
