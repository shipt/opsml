# pylint: disable=protected-access
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from opsml.app.routes.pydantic_models import (
    CardRequest,
    CompareMetricRequest,
    CompareMetricResponse,
    MetricRequest,
    MetricResponse,
    RegisterModelRequest,
)
from opsml.helpers.logging import ArtifactLogger
from opsml.model.challenger import ModelChallenger
from opsml.registry import CardInfo, CardRegistries, CardRegistry, ModelCard, RunCard
from opsml.registry.cards.model import ModelMetadata
from opsml.registry.model.registrar import (
    ModelRegistrar,
    RegistrationError,
    RegistrationRequest,
)


logger = ArtifactLogger.get_logger(__name__)

# Constants
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATE_PATH = os.path.abspath(os.path.join(PARENT_DIR, "templates"))


templates = Jinja2Templates(directory=TEMPLATE_PATH)

router = APIRouter()


def get_all_teams(registry: CardRegistry) -> List[str]:
    """Returns a list of all teams in the registry

    Args:
        registry:
            The registry to query
    Returns:
        A list of teams
    """
    return list(set(card["team"] for card in registry.list_cards(as_dataframe=False)))


def get_team_model_names(registry: CardRegistry, team: str) -> List[str]:
    """Returns a list of model names for a given team

    Args:
        registry:
            The registry to query
        team:
            The team to query
    Returns:
        A list of model names
    """
    return list(
        set(card["name"] for card in registry.list_cards(team=team, as_dataframe=False)),
    )


def get_model_versions(registry: CardRegistry, model: str, team: str) -> List[str]:
    """Returns a list of model versions for a given team and model

    Args:
        registry:
            The registry to query
        model:
            The model to query
    Returns:
        A list of model versions
    """

    return [card["version"] for card in registry.list_cards(name=model, team=team, as_dataframe=False)]


@router.get("/models/list/")
async def model_homepage(request: Request, team: Optional[str] = None):
    """UI home for listing models in model registry

    Args:
        request:
            The incoming HTTP request.
    Returns:
        200 if the request is successful. The body will contain a JSON string
        with the list of models.
    """
    registry: CardRegistry = request.app.state.registries.model
    all_teams = get_all_teams(registry)

    team = team or all_teams[0]
    model_names = get_team_model_names(registry, team)

    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "all_teams": all_teams,
            "selected_team": team,
            "models": model_names,
        },
    )


@router.get("/models/versions/")
async def model_versions_page(request: Request, model: Optional[str] = None):
    if model is None:
        return RedirectResponse(url="/opsml/models/list/")

    registry: CardRegistry = request.app.state.registries.model
    models = registry.list_cards(name=model, as_dataframe=False)
    runs = list(set(model["runcard_uid"] for model in models))

    if len(runs) >= 0:
        run = request.app.state.registries.run.list_cards(uid=runs[0], as_dataframe=False)
        project_id = run[0]["project_id"]
    else:
        project_id = None

    if project_id is not None:
        project_num = request.app.state.mlflow_client.get_experiment_by_name(name=project_id).experiment_id
    else:
        project_num = None

    return templates.TemplateResponse(
        "model_version.html",
        {
            "request": request,
            "versions": models,
            "selected_model": model,
            "project_num": project_num,
        },
    )


@router.get("/models/metadata/")
async def list_model(
    request: Request,
    uid: Optional[str] = None,
    version: Optional[str] = None,
    model: Optional[str] = None,
    team: Optional[str] = None,
):
    teams = get_all_teams(request.app.state.registries.model)
    if all(attr is None for attr in [uid, version, model, team]):
        return templates.TemplateResponse(
            "metadata.html",
            {
                "request": request,
                "teams": teams,
                "metadata": None,
                "models": None,
                "selected_team": None,
                "selected_model": None,
            },
        )

    elif team is not None and all(attr is None for attr in [version, model]):
        models = get_team_model_names(request.app.state.registries.model, team)
        return templates.TemplateResponse(
            "metadata.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "metadata": None,
                "models": models,
                "selected_model": model,
            },
        )

    elif team is not None and model is not None and version is None:
        versions = get_model_versions(request.app.state.registries.model, model, team)
        models = get_team_model_names(request.app.state.registries.model, team)

        return templates.TemplateResponse(
            "metadata.html",
            {
                "request": request,
                "teams": [team],
                "selected_team": team,
                "metadata": None,
                "models": models,
                "selected_model": model,
                "versions": versions,
            },
        )

    elif all(attr is not None for attr in [version, model, team]) or uid is not None:
        metadata = post_model_metadata(
            request=request,
            payload=CardRequest(name=model, team=team, version=version, uid=uid),
        )

        versions = get_model_versions(request.app.state.registries.model, metadata.model_name, metadata.model_team)
        models = get_team_model_names(request.app.state.registries.model, metadata.model_team)

        max_dim = 0
        if metadata.data_schema.model_data_schema.data_type == "NUMPY_ARRAY":
            features = metadata.data_schema.model_data_schema.input_features
            inputs = features.get("inputs")
            if inputs is not None:
                max_dim = max(features.get("inputs").shape)

        # capping amount of sample data shown
        if max_dim > 200:
            metadata.sample_data = {"inputs": "Sample data is too large to load in ui"}

        return templates.TemplateResponse(
            "metadata.html",
            {
                "request": request,
                "teams": [team],
                "selected_team": team,
                "metadata": metadata,
                "models": models,
                "selected_model": model,
                "versions": versions,
            },
        )

    return RedirectResponse(url="/opsml/models/metadata/")


@router.post("/models/register", name="model_register")
def post_model_register(request: Request, payload: RegisterModelRequest) -> str:
    """Registers a model to a known GCS location.

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
    metadata = post_model_metadata(request, CardRequest(name=payload.name, version=payload.version))

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
