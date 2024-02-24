# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from opsml.types import RegistryType

# Constants
TEMPLATE_PATH = Path(__file__).parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_PATH)

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


@router.get("/")
async def homepage(request: Request) -> RedirectResponse:
    return RedirectResponse("/opsml")
