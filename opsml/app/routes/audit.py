# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
from typing import Dict, Optional
import datetime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse
from opsml.app.routes.utils import error_to_500, get_names_teams_versions
from opsml.app.routes.pydantic_models import CommentSaveRequest
from opsml.helpers.logging import ArtifactLogger
from opsml.registry import CardRegistries, AuditCard
from opsml.registry.cards.audit import AuditSections
from opsml.registry.cards.types import Comment


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
    if all(attr is None for attr in [uid, version, model, team]):
        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": request.app.state.registries.model.list_teams(),
                "models": None,
                "selected_team": None,
                "selected_model": None,
                "version": None,
                "audit_report": None,
            },
        )

    elif team is not None and all(attr is None for attr in [version, model]):
        teams = request.app.state.registries.model.list_teams()
        model_names = request.app.state.registries.model.list_card_names(team=team)
        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": model_names,
                "versions": None,
                "selected_model": None,
                "version": None,
                "audit_report": None,
            },
        )

    elif team is not None and model is not None and version is None:
        model_names, teams, versions = get_names_teams_versions(
            registry=request.app.state.registries.model,
            name=model,
            team=team,
        )

        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": model_names,
                "selected_model": model,
                "versions": versions,
                "version": None,
                "audit_report": None,
            },
        )

    elif all(attr is not None for attr in [version, model, team]) or uid is not None:
        model_names, teams, versions = get_names_teams_versions(
            registry=request.app.state.registries.model,
            name=model,
            team=team,
        )
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
                "timestamp": None,
                "comments": [],
            }

        else:
            audit_card: AuditCard = request.app.state.registries.audit.load_card(uid=auditcard_uid)
            audit_report = {
                "name": audit_card.name,
                "team": audit_card.team,
                "user_email": audit_card.user_email,
                "version": audit_card.version,
                "uid": audit_card.uid,
                "status": audit_card.approved,
                "audit": audit_card.audit.model_dump(),
                "timestamp": None,
                "comments": audit_card.comments,
            }

        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "teams": teams,
                "selected_team": team,
                "models": model_names,
                "selected_model": model,
                "versions": versions,
                "version": version,
                "audit_report": audit_report,
            },
        )

    return RedirectResponse(url="/opsml/audit/")


class AuditFormParser:
    def __init__(self, audit_form_dict: Dict[str, str], registries: CardRegistries):
        """Instantiates parse for audit form data

        Args:
            audit_dict:
                Dictionary of audit form data
            registries:
                `CardRegistries`
        """
        self.audit_form_dict = audit_form_dict
        self.registries = registries

    def _add_auditcard_to_modelcard(self, auditcard_uid: str) -> None:
        """Adds registered AuditCard uid to ModelCard

        Args:
            auditcard_uid:
                AuditCard uid to add to ModelCard
        """
        model_record = self.registries.model.list_cards(
            name=self.audit_form_dict["selected_model_name"],
            version=self.audit_form_dict["selected_model_version"],
        )[0]

        model_record["auditcard_uid"] = auditcard_uid
        self.registries.model._registry.update_card_record(card=model_record)

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
            return self.registries.audit.update_card(card=audit_card)
        self.registries.audit.register_card(card=audit_card)
        self._add_auditcard_to_modelcard(auditcard_uid=audit_card.uid)

    def get_audit_card(self) -> AuditCard:
        """Gets or creates AuditCard to use with Form data

        Returns:
            `AuditCard`
        """
        if self.audit_form_dict["uid"] is not None:
            # check first
            records = self.registries.audit.list_cards(uid=self.audit_form_dict["uid"])

            if bool(records):
                audit_card: AuditCard = self.registries.audit.load_card(uid=self.audit_form_dict["uid"])

            else:
                logger.info("Invalid uid specified, defaulting to new AuditCard")
                audit_card = AuditCard(
                    name=self.audit_form_dict["name"],
                    team=self.audit_form_dict["team"],
                    user_email=self.audit_form_dict["email"],
                )
        else:
            audit_card = AuditCard(
                name=self.audit_form_dict["name"],
                team=self.audit_form_dict["team"],
                user_email=self.audit_form_dict["email"],
            )

        return audit_card

    def parse_form_sections(self, audit_card: AuditCard) -> AuditCard:
        """Parses form data into AuditCard

        Args:
            audit_card:
                `AuditCard`

        Returns:
            `AuditCard`
        """
        audit_section = audit_card.audit.model_dump()
        for question_key, response in self.audit_form_dict.items():
            if bool(re.search(r"\d", question_key)) and response is not None:
                splits = question_key.split("_")
                section = "_".join(splits[:-1])
                number = int(splits[-1])  # this will always be an int
                audit_section[section][number]["response"] = response

        # recreate section
        audit_card.audit = AuditSections(**audit_section)
        return audit_card

    def parse_form(self) -> AuditCard:
        """Parses form data into AuditCard"""

        audit_card = self.get_audit_card()
        audit_card = self.parse_form_sections(audit_card=audit_card)
        self.register_update_audit_card(audit_card=audit_card)

        return audit_card


@router.post("/audit/save")
@error_to_500
async def save_audit_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    team: str = Form(...),
    uid: Optional[str] = Form(None),
    selected_model_name: str = Form(...),
    selected_model_team: str = Form(...),
    selected_model_version: str = Form(...),
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
    audit_card: Optional[AuditCard] = None,
):
    # collect all function arguments into a dictionary

    # base attr needed for html
    model_names, teams, versions = get_names_teams_versions(
        registry=request.app.state.registries.model,
        name=selected_model_name,
        team=selected_model_team,
    )

    parser = AuditFormParser(
        audit_form_dict=locals(),
        registries=request.app.state.registries,
    )
    audit_card = parser.parse_form()

    audit_report = {
        "name": audit_card.name,
        "team": audit_card.team,
        "user_email": audit_card.user_email,
        "version": audit_card.version,
        "uid": audit_card.uid,
        "status": audit_card.approved,
        "audit": audit_card.audit.model_dump(),
        "timestamp": str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M")),
        "comments": audit_card.comments,
    }

    return templates.TemplateResponse(
        "audit.html",
        {
            "request": request,
            "teams": teams,
            "selected_team": selected_model_team,
            "models": model_names,
            "selected_model": selected_model_name,
            "versions": versions,
            "version": selected_model_version,
            "audit_report": audit_report,
        },
    )


@router.post("/audit/comment/save", response_model=CommentSaveRequest)
@error_to_500
async def save_audit_comment(request: Request, comment: CommentSaveRequest = Depends(CommentSaveRequest)):
    """Save comment to AuditCard

    Args:
        request:
            The incoming HTTP request.
        comment:
            `CommentSaveRequest`
    """
    audit_card: AuditCard = request.app.state.registries.audit.load_card(uid=comment.uid)

    print("before")
    print(audit_card.comments)

    # most recent first
    audit_card.add_comment(
        name=comment.comment_name,
        comment=comment.comment_text,
    )

    model_names, teams, versions = get_names_teams_versions(
        registry=request.app.state.registries.model,
        name=comment.selected_model_name,
        team=comment.selected_model_team,
    )
    audit_card: AuditCard = request.app.state.registries.audit.load_card(uid=comment.uid)

    print("after update")
    print(audit_card.comments)

    audit_report = {
        "name": audit_card.name,
        "team": audit_card.team,
        "user_email": audit_card.user_email,
        "version": audit_card.version,
        "uid": audit_card.uid,
        "status": audit_card.approved,
        "audit": audit_card.audit.model_dump(),
        "timestamp": str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M")),
        "comments": audit_card.comments,
    }

    return templates.TemplateResponse(
        "audit.html",
        {
            "request": request,
            "teams": teams,
            "selected_team": comment.selected_model_team,
            "models": model_names,
            "selected_model": comment.selected_model_name,
            "versions": versions,
            "version": comment.selected_model_version,
            "audit_report": audit_report,
        },
    )
