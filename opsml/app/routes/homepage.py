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
    # validate registry type
    if registry:
        try:
            RegistryType.from_str(registry)
        except NotImplementedError:
            registry = None

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
    card_names = _registry._registry.get_unique_card_names(repository=repository)

    return {"repositories": repositories, "names": card_names}


@router.get("/")
async def homepage(request: Request) -> RedirectResponse:
    return RedirectResponse("/opsml")
