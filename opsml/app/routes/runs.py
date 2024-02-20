# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# pylint: disable=protected-access
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from opsml.app.core.dependencies import swap_opsml_root
from opsml.app.routes.utils import error_to_500
from opsml.helpers.logging import ArtifactLogger
from opsml.storage.client import StorageClientBase
from opsml import CardRegistry, RunCard

logger = ArtifactLogger.get_logger()

# Constants
TEMPLATE_PATH = Path(__file__).parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_PATH)

router = APIRouter()


@router.get("/runs/graphics", name="graphic_uris", response_class=HTMLResponse)
@error_to_500
async def get_graphic_page(request: Request, run_uid: str) -> HTMLResponse:
    """Method for generating presigned urls and html for graphics page

    Args:
        request:
            The incoming HTTP request.
        payload:
            ArtifactURIs

    Returns:
        Generated HTML for graphics
    """
    uris = {}

    storage_client: StorageClientBase = request.app.state.storage_client
    run_registry: CardRegistry = request.app.state.registries.run
    storage_root = request.app.state.storage_root

    card: RunCard = run_registry.load_card(uid=run_uid)

    for name, artifact in card.artifact_uris.items():
        remote_path = Path(artifact.remote_path)
        suffix = remote_path.suffix
        if suffix in [".png", ".jpg", ".jpeg", ".tiff", ".gif", ".bmp", ".svg"]:
            remote_path = swap_opsml_root(request, remote_path)

            # get remote path relative to storage root
            remote_path = remote_path.relative_to(storage_root)
            uris[name] = storage_client.generate_presigned_url(remote_path, expiration=600)

    return templates.TemplateResponse("include/project/graphics.html", {"request": request, "uris": uris})
