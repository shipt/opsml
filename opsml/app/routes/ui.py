# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, HTTPException, status
from fastapi.templating import Jinja2Templates

from opsml import CardRegistry
from opsml.app.routes.pydantic_models import ErrorMessage, XYMetric, GetMetricRequest, Metrics, Metric
from opsml.app.routes.metrics import get_metric
from opsml.helpers.logging import ArtifactLogger
from opsml.types import RegistryType

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
    uid: Optional[str] = None,
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

    if uid:
        _registry: CardRegistry = getattr(request.app.state.registries, registry)
        card = _registry.list_cards(uid=uid)

        if card:
            name = card[0]["name"]
            repository = card[0]["repository"]
            version = card[0]["version"]

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

    if not repositories:
        return {"repositories": [], "names": []}

    if repository is None:
        repository = repositories[0]

    card_names = _registry._registry.get_unique_card_names(repository=repository)

    assert isinstance(card_names, list)
    assert isinstance(repositories, list)

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/opsml/ui/metrics")
async def get_metrics_for_ui(request: Request, payload: GetMetricRequest) -> Dict[str, XYMetric]:
    """Gets metrics from the metric table and formats for rendering in UI"""
    try:
        metric_dump: Dict[str, XYMetric] = {}

        metrics: Metrics = get_metric(request, payload)

        assert isinstance(metrics.metric, list)

        for metric in metrics.metric:
            assert isinstance(metric, Metric)

            if metric.name not in metric_dump:
                metric_dump[metric.name] = XYMetric()

            metric_dump[metric.name].x.append(metric.step)
            metric_dump[metric.name].y.append(metric.value)

        return metric_dump

    except Exception as e:
        logger.error(f"Error rendering 500 page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics for UI",
        )


@router.get("/opsml/dev")
async def test(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("include/test.html", {"request": request})
