# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
from typing import Any, Dict, List, Optional, Union
from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Request, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse
from opsml.app.routes.utils import error_to_500, get_runcard_from_model, list_team_name_info, get_model_versions
from opsml.app.routes.pydantic_models import AuditSaveRequest
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
                "audit_report": None,
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
                "uid": "",
                "status": False,
                "audit": AuditSections().model_dump(),
            }

        audit_report = {
            "name": None,
            "team": None,
            "user_email": None,
            "version": None,
            "uid": None,
            "status": False,
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


class AuditFormParser:
    def __init__(self, audit_dict: Dict[str, str], audit_registry: CardRegistry):
        """Instantiates parse for audit form data

        Args:
            audit_dict:
                Dictionary of audit form data
            audit_registry:
                AuditCard registry
        """
        self.audit_dict = audit_dict
        self.registry = audit_registry
        self.section_template = AuditSections.load_yaml_template()

    def _pop_audit_attr(self) -> Dict[str, str]:
        """Pops attributes associated with audit form data

        Args:
            audit_dict:
                Dictionary of audit form data

        Returns:
            Dictionary of audit form data with attributes popped
        """
        for attr in ["request", "team", "name", "email", "uid"]:
            self.audit_dict.pop(attr)

    def register_update_audit_card(self, audit_card: AuditCard) -> None:
        """Register or update an AuditCard. This will always use server-side registration,
        as the auditcard_uid is created/updated via form data

        Args:
            registry:
                CardRegistry
            audit_card:
                `AuditCard`

        Returns:
            None
        """
        # register/update audit
        if audit_card.uid is not None:
            return self.registry.update_card(card=audit_card)
        return self.registry.register_card(card=audit_card)

    def get_audit_card(self) -> AuditCard:
        """Gets or creates AuditCard to use with Form data

        Returns:
            `AuditCard`
        """
        if self.audit_dict["uid"] is not None:
            # check first
            records = self.registry.list_cards(uid=self.audit_dict["uid"])

            if bool(records):
                audit_card: AuditCard = self.registry.load_card(uid=self.audit_dict["uid"])

                # update section template
                self.section_template = audit_card.audit.model_dump()

            else:
                logger.info("Invalid uid specified, defaulting to new AuditCard")
                audit_card = AuditCard(
                    name=self.audit_dict["name"],
                    team=self.audit_dict["team"],
                    user_email=self.audit_dict["email"],
                )
        else:
            audit_card = AuditCard(
                name=self.audit_dict["name"],
                team=self.audit_dict["team"],
                user_email=self.audit_dict["email"],
            )

        # pop base attr
        self._pop_audit_attr()
        return audit_card

    def parse_form_sections(self):
        for question_key, response in self.audit_dict.items():
            if response is not None:
                splits = question_key.split("_")
                section = "_".join(splits[:-1])
                number = int(splits[-1])  # this will always be an int
                self.section_template[section][number]["response"] = response

    def parse_form(self):
        audit_card = self.get_audit_card()
        self.parse_form_sections()
        audit_card.audit = AuditSections(**self.section_template)
        self.register_update_audit_card(audit_card=audit_card)


@router.post("/audit/save")
@error_to_500
async def audit_list_homepage(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    team: str = Form(...),
    uid: Optional[str] = Form(None),
    business_understanding_1: Optional[str] = Form(None),
    business_understanding_2: Optional[str] = Form(None),
    business_understanding_3: Optional[str] = Form(None),
    business_understanding_4: Optional[str] = Form(None),
    business_understanding_5: Optional[str] = Form(None),
    business_understanding_6: Optional[str] = Form(None),
    business_understanding_7: Optional[str] = Form(None),
    business_understanding_8: Optional[str] = Form(None),
    business_understanding_9: Optional[str] = Form(None),
    business_understanding_10: Optional[str] = Form(None),
    data_understanding_1: Optional[str] = Form(None),
    data_understanding_2: Optional[str] = Form(None),
    data_understanding_3: Optional[str] = Form(None),
    data_understanding_4: Optional[str] = Form(None),
    data_understanding_5: Optional[str] = Form(None),
    data_understanding_6: Optional[str] = Form(None),
    data_understanding_7: Optional[str] = Form(None),
    data_understanding_8: Optional[str] = Form(None),
    data_understanding_9: Optional[str] = Form(None),
    data_preparation_1: Optional[str] = Form(None),
    data_preparation_2: Optional[str] = Form(None),
    data_preparation_3: Optional[str] = Form(None),
    data_preparation_4: Optional[str] = Form(None),
    data_preparation_5: Optional[str] = Form(None),
    data_preparation_6: Optional[str] = Form(None),
    data_preparation_7: Optional[str] = Form(None),
    data_preparation_8: Optional[str] = Form(None),
    data_preparation_9: Optional[str] = Form(None),
    data_preparation_10: Optional[str] = Form(None),
    modeling_1: Optional[str] = Form(None),
    modeling_2: Optional[str] = Form(None),
    modeling_3: Optional[str] = Form(None),
    modeling_4: Optional[str] = Form(None),
    modeling_5: Optional[str] = Form(None),
    modeling_6: Optional[str] = Form(None),
    modeling_7: Optional[str] = Form(None),
    modeling_8: Optional[str] = Form(None),
    modeling_9: Optional[str] = Form(None),
    modeling_10: Optional[str] = Form(None),
    modeling_11: Optional[str] = Form(None),
    modeling_12: Optional[str] = Form(None),
    evaluation_1: Optional[str] = Form(None),
    evaluation_2: Optional[str] = Form(None),
    evaluation_3: Optional[str] = Form(None),
    evaluation_4: Optional[str] = Form(None),
    evaluation_5: Optional[str] = Form(None),
    deployment_ops_1: Optional[str] = Form(None),
    deployment_ops_2: Optional[str] = Form(None),
    deployment_ops_3: Optional[str] = Form(None),
    deployment_ops_4: Optional[str] = Form(None),
    deployment_ops_5: Optional[str] = Form(None),
    deployment_ops_6: Optional[str] = Form(None),
    deployment_ops_7: Optional[str] = Form(None),
    deployment_ops_8: Optional[str] = Form(None),
    deployment_ops_9: Optional[str] = Form(None),
    deployment_ops_10: Optional[str] = Form(None),
    deployment_ops_11: Optional[str] = Form(None),
    deployment_ops_12: Optional[str] = Form(None),
    deployment_ops_13: Optional[str] = Form(None),
    deployment_ops_14: Optional[str] = Form(None),
    deployment_ops_15: Optional[str] = Form(None),
    deployment_ops_16: Optional[str] = Form(None),
    deployment_ops_17: Optional[str] = Form(None),
    deployment_ops_18: Optional[str] = Form(None),
    deployment_ops_19: Optional[str] = Form(None),
    deployment_ops_20: Optional[str] = Form(None),
    deployment_ops_21: Optional[str] = Form(None),
    deployment_ops_22: Optional[str] = Form(None),
    misc_1: Optional[str] = Form(None),
    misc_2: Optional[str] = Form(None),
    misc_3: Optional[str] = Form(None),
    misc_4: Optional[str] = Form(None),
    misc_5: Optional[str] = Form(None),
    misc_6: Optional[str] = Form(None),
    misc_7: Optional[str] = Form(None),
    misc_8: Optional[str] = Form(None),
    misc_9: Optional[str] = Form(None),
    misc_10: Optional[str] = Form(None),
):
    # collect all function arguments into a dictionary
    audit_dict = locals()
    parser = AuditFormParser(
        audit_dict=audit_dict,
        audit_registry=request.app.state.registries.audit,
    )

    audit_card = parser.parse_form()

    return
