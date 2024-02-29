# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from opsml.types import RegistryType
from opsml import CardRegistry
from opsml.helpers.logging import ArtifactLogger
from opsml.app.routes.pydantic_models import ErrorMessage

# Constants
TEMPLATE_PATH = Path(__file__).parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_PATH)
logger = ArtifactLogger.get_logger()

router = APIRouter()


@router.get("/opsml")
async def opsml_homepage(
    request: Request,
    registry: Optional[str] = None,
    name: Optional[str] = None,
    repository: Optional[str] = None,
    version: Optional[str] = None,
) -> HTMLResponse:
    return await opsml_ui_page(
        request,
        registry=registry,
        name=name,
        repository=repository,
        version=version,
    )


@router.get("/opsml/ui")
async def opsml_ui_page(
    request: Request,
    registry: Optional[str] = None,
    name: Optional[str] = None,
    repository: Optional[str] = None,
    version: Optional[str] = None,
) -> HTMLResponse:
    # validate registry type
    if registry:
        try:
            RegistryType.from_str(registry)
        except NotImplementedError:
            registry = RegistryType.MODEL.value

    # default to model
    else:
        registry = RegistryType.MODEL.value

    return templates.TemplateResponse(
        "include/index.html",
        {
            "request": request,
            "registry": registry,
            "name": name,
            "repository": repository,
            "version": version,
        },
    )


@router.get("/opsml/ui/attribution")
async def opsml_attribution_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("include/components/attribution.html", {"request": request})


@router.get("/opsml/repository")
async def opsml_repositories(
    request: Request,
    registry: str,
    repository: Optional[str] = None,
) -> Dict[str, List[str]]:
    """Get the list of repositories and names for a given registry.

    Args:
        request:
            The request object.
        registry:
            The registry type. Defaults to None.
        repository:
            The repository name. Defaults to first repository in repository list if None.

    Returns:
        Dict[str, List[str]]: A dictionary containing the repositories and card names.
    """

    _registry: CardRegistry = getattr(request.app.state.registries, registry)

    repositories = _registry._registry.unique_repositories

    if repository is None:
        repository = repositories[0]

    card_names = _registry._registry.get_unique_card_names(repository=repository)

    return {"repositories": repositories, "names": card_names}


@router.get("/")
async def homepage(request: Request) -> RedirectResponse:
    return RedirectResponse("/opsml")


@router.post("/opsml/ui/error")
async def error_to_500(request: Request, payload: ErrorMessage) -> HTMLResponse:
    try:
        return templates.TemplateResponse(
            "include/500.html",
            {
                "request": request,
                "error_message": payload.message,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering 500 page: {e}")
        return HTMLResponse(status_code=500, content="Internal Server Error")
