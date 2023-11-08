# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from opsml.app.routes.pydantic_models import (
    CardRequest,
    CompareMetricRequest,
    CompareMetricResponse,
    MetricRequest,
    MetricResponse,
    RegisterModelRequest,
)
from opsml.app.routes.route_helpers import ModelRouteHelper
from opsml.app.routes.utils import error_to_500
from opsml.helpers.logging import ArtifactLogger
from opsml.model.challenger import ModelChallenger
from opsml.registry import CardInfo, CardRegistries, CardRegistry, ModelCard, RunCard
from opsml.registry.cards.model import ModelMetadata
from opsml.registry.model.registrar import (
    ModelRegistrar,
    RegistrationError,
    RegistrationRequest,
)

logger = ArtifactLogger.get_logger()

# Constants
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATE_PATH = os.path.abspath(os.path.join(PARENT_DIR, "templates"))
templates = Jinja2Templates(directory=TEMPLATE_PATH)

router = APIRouter()
model_route_helper = ModelRouteHelper()


@router.get("/models/list/")
@error_to_500
async def model_list_homepage(request: Request, team: Optional[str] = None):
    """UI home for listing models in model registry
    Args:
        request:
            The incoming HTTP request.
        team:
            The team to query
    Returns:
        200 if the request is successful. The body will contain a JSON string
        with the list of models.
    """
    return model_route_helper.get_homepage(request=request, team=team)


@router.get("/models/versions/")
@error_to_500
async def model_versions_page(
    request: Request,
    model: Optional[str] = None,
    version: Optional[str] = None,
):
    if model is None:
        return RedirectResponse(url="/opsml/models/list/")

    registry: CardRegistry = request.app.state.registries.model
    versions = registry.list_cards(name=model, as_dataframe=False, limit=50)
    metadata = post_model_metadata(
        request=request,
        payload=CardRequest(name=model, version=version),
    )
    return model_route_helper.get_versions_page(
        request=request,
        name=model,
        version=version,
        versions=versions,
        metadata=metadata,
    )


@router.post("/models/register", name="model_register")
def post_model_register(request: Request, payload: RegisterModelRequest) -> str:
    """Registers a model to a known cloud storage location.

       This is used from within our CI/CD infrastructure to ensure a known good
       GCS location exists for the onnx model.

    Args:
        request:
            The incoming HTTP request.
        payload:
            Details on the model to register. See RegisterModelRequest for more
            information.
    Returns:
        422 if the RegisterModelRequest is invalid (i.e., the version is
        malformed).

        404 if the model is not found.

        200 if the model is found. The body will contain a JSON string with the
        GCS URI to the *folder* where the model is registered.
    """

    # get model metadata
    metadata = post_model_metadata(
        request,
        CardRequest(
            name=payload.name,
            version=payload.version,
            ignore_release_candidate=True,
        ),
    )

    try:
        registrar: ModelRegistrar = request.app.state.model_registrar
        return registrar.register_model(
            RegistrationRequest(name=payload.name, version=payload.version, onnx=payload.onnx),
            metadata,
        )
    except RegistrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unknown error registering model",
        ) from exc


@router.post("/models/metadata", name="model_metadata")
def post_model_metadata(
    request: Request,
    payload: CardRequest,
) -> ModelMetadata:
    """
    Downloads a Model API definition

    Args:
        request:
            The incoming HTTP request

        payload:
            Details on the model to retrieve metadata for.

    Returns:
        ModelMetadata or HTTP_404_NOT_FOUND if the model is not found.
    """
    registry: CardRegistry = request.app.state.registries.model

    try:
        model_card: ModelCard = registry.load_card(  # type:ignore
            name=payload.name,
            version=payload.version,
            uid=payload.uid,
            ignore_release_candidates=payload.ignore_release_candidate,
        )

    except IndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        ) from exc

    return model_card.model_metadata


@router.post("/models/metrics", response_model=MetricResponse, name="model_metrics")
def post_model_metrics(
    request: Request,
    payload: MetricRequest = Body(...),
) -> MetricResponse:
    """Gets metrics associated with a ModelCard"""

    # Get model runcard id
    registries: CardRegistries = request.app.state.registries
    cards: List[Dict[str, Any]] = registries.model.list_cards(
        uid=payload.uid,
        name=payload.name,
        team=payload.team,
        version=payload.version,
        as_dataframe=False,
    )

    if len(cards) > 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="More than one card found",
        )

    card = cards[0]

    if card.get("runcard_uid") is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model is not associated with a run",
        )

    runcard: RunCard = registries.run.load_card(uid=card.get("runcard_uid"))

    return MetricResponse(metrics=runcard.metrics)


@router.post("/models/compare_metrics", response_model=CompareMetricResponse, name="compare_model_metrics")
def compare_metrics(
    request: Request,
    payload: CompareMetricRequest = Body(...),
) -> CompareMetricResponse:
    """Compare model metrics using `ModelChallenger`"""

    try:
        # Get challenger
        registries: CardRegistries = request.app.state.registries
        challenger_card: ModelCard = registries.model.load_card(uid=payload.challenger_uid)
        model_challenger = ModelChallenger(challenger=challenger_card)

        champions = [CardInfo(uid=champion_uid) for champion_uid in payload.champion_uid]
        battle_report = model_challenger.challenge_champion(
            metric_name=payload.metric_name,
            champions=champions,
            lower_is_better=payload.lower_is_better,
        )

        return CompareMetricResponse(
            challenger_name=challenger_card.name,
            challenger_version=challenger_card.version,
            report=battle_report,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare model metrics. {error}",
        ) from error
