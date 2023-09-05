# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse
from opsml.app.routes.utils import error_to_500, get_runcard_from_model, list_team_name_info, get_model_versions
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
from opsml.registry import CardInfo, CardRegistries, CardRegistry, ModelCard, RunCard, AuditCard
from opsml.registry.cards.audit import AuditSections
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


@router.get("/audit/")
@error_to_500
async def audit_list_homepage(
    request: Request,
    team: Optional[str] = None,
    model: Optional[str] = None,
    version: Optional[str] = None,
    uid: Optional[str] = None,
):
    """UI home for listing models in model registry

    Args:
        request:
            The incoming HTTP request.
    Returns:
        200 if the request is successful. The body will contain a JSON string
        with the list of models.
    """
    teams = request.app.state.registries.model.list_teams()
    if all(attr is None for attr in [uid, version, model, team]):
        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "models": None,
                "selected_team": None,
                "selected_model": None,
                "version": None,
            },
        )

    elif team is not None and all(attr is None for attr in [version, model]):
        models = request.app.state.registries.model.list_card_names(team=team)
        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": models,
                "versions": None,
                "selected_model": None,
                "version": None,
                "audit_report": None,
            },
        )

    elif team is not None and model is not None and version is None:
        versions = get_model_versions(request.app.state.registries.model, model, team)
        models = request.app.state.registries.model.list_card_names(team=team)

        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": models,
                "selected_model": model,
                "versions": versions,
                "version": None,
                "audit_report": None,
            },
        )

    elif all(attr is not None for attr in [version, model, team]) or uid is not None:
        versions = get_model_versions(request.app.state.registries.model, model, team)
        models = request.app.state.registries.model.list_card_names(team=team)
        model_record = request.app.state.registries.model.list_cards(
            name=model,
            version=version,
            uid=uid,
        )[0]

        auditcard_uid = model_record.get("auditcard_uid")

        if auditcard_uid is None:
            audit_report = {
                "name": None,
                "team": None,
                "user_email": None,
                "version": None,
                "uid": None,
                "audit": AuditSections().model_dump(),
            }

        audit_report = {
            "name": None,
            "team": None,
            "user_email": None,
            "version": None,
            "uid": None,
            "audit": AuditSections().model_dump(),
        }

        # create sql query that can search auditcards by associated modelcard uid
        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": models,
                "selected_model": model,
                "versions": versions,
                "version": version,
                "audit_report": audit_report,
            },
        )

    return RedirectResponse(url="/opsml/audit/")
