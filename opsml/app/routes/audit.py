# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import csv
import codecs
import tempfile
from typing import Dict, Optional, List, Union, Tuple, Any
import datetime
from fastapi.responses import FileResponse
from fastapi import APIRouter, Request, Depends, UploadFile, BackgroundTasks, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse
from opsml.app.routes.utils import error_to_500, get_names_teams_versions
from opsml.app.routes.pydantic_models import CommentSaveRequest, AuditFormRequest
from opsml.helpers.logging import ArtifactLogger
from opsml.registry import CardRegistries, AuditCard
from opsml.registry.cards.audit import AuditSections, Comment


logger = ArtifactLogger.get_logger(__name__)

# Constants
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATE_PATH = os.path.abspath(os.path.join(PARENT_DIR, "templates"))
AUDIT_FILE = "audit_file.csv"

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
            "include/audit/audit.html",
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
            "include/audit/audit.html",
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
            "include/audit/audit.html",
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
                "uid": None,
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
            "include/audit/audit.html",
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
async def save_audit_form(request: Request, form: AuditFormRequest = Depends(AuditFormRequest)):
    # collect all function arguments into a dictionary

    # base attr needed for html
    model_names, teams, versions = get_names_teams_versions(
        registry=request.app.state.registries.model,
        name=form.selected_model_name,
        team=form.selected_model_team,
    )

    parser = AuditFormParser(
        audit_form_dict=form.model_dump(),
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
        "include/audit/audit.html",
        {
            "request": request,
            "teams": teams,
            "selected_team": form.selected_model_team,
            "models": model_names,
            "selected_model": form.selected_model_name,
            "versions": versions,
            "version": form.selected_model_version,
            "audit_report": audit_report,
        },
    )


@router.post("/audit/comment/save")
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

    request.app.state.registries.audit.update_card(card=audit_card)

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
        "include/audit/audit.html",
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


@router.post("/audit/upload")
@error_to_500
async def upload_audit_data(
    request: Request,
    background_tasks: BackgroundTasks,
    form: AuditFormRequest = Depends(AuditFormRequest),
):
    """Uploads audit data form file. If an audit_uid is provided, only the audit section will be updated."""
    data = form.audit_file.file
    csv_reader = csv.DictReader(codecs.iterdecode(data, "utf-8"))
    background_tasks.add_task(data.close)
    records = list(csv_reader)
    audit_sections = AuditSections().model_dump()

    for record in records:
        section = record["topic"]
        number = int(record["number"])
        audit_sections[section][number]["response"] = record["response"]

    if form.uid is not None:
        audit_card: AuditCard = request.app.state.registries.audit.load_card(uid=form.uid)
        audit_report = {
            "name": audit_card.name,
            "team": audit_card.team,
            "user_email": audit_card.user_email,
            "version": audit_card.version,
            "uid": audit_card.uid,
            "status": audit_card.approved,
            "audit": audit_sections,  # using updated section
            "timestamp": str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M")),
            "comments": audit_card.comments,
        }
    else:
        audit_report = {
            "name": form.name,
            "team": form.team,
            "user_email": form.email,
            "version": form.version,
            "uid": form.uid,
            "status": form.status,
            "audit": audit_sections,
            "timestamp": str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M")),
            "comments": [],
        }

    # base attr needed for html
    model_names, teams, versions = get_names_teams_versions(
        registry=request.app.state.registries.model,
        name=form.selected_model_name,
        team=form.selected_model_team,
    )

    return templates.TemplateResponse(
        "include/audit/audit.html",
        {
            "request": request,
            "teams": teams,
            "selected_team": form.selected_model_team,
            "models": model_names,
            "selected_model": form.selected_model_name,
            "versions": versions,
            "version": form.selected_model_version,
            "audit_report": audit_report,
        },
    )


def remove_file(path: str) -> None:
    """Removes file from disk"""
    os.unlink(path)


def write_audit_to_csv(
    audit_records: List[Dict[str, Optional[Union[str, int]]]],
    field_names: List[str],
) -> Tuple[FileResponse, str]:
    """Writes audit data to csv and returns FileResponse

    Args:
        audit_records:
            List of audit records
        field_names:
            List of field names for csv header

    Returns:
        FileResponse
    """
    csv_file, path = tempfile.mkstemp(suffix=".csv")
    with open(file=path, mode="w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(audit_records)
    response = FileResponse(AUDIT_FILE, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=audit_file.csv"

    return response, path


@router.post("/audit/download", response_class=FileResponse)
@error_to_500
async def download_audit_data(
    request: Request,
    background_tasks: BackgroundTasks,
    form: AuditFormRequest = Depends(AuditFormRequest),
):
    """Downloads Audit Form data to csv"""

    field_names = ["topic", "number", "question", "purpose", "response"]

    parser = AuditFormParser(
        audit_form_dict=form.model_dump(),
        registries=request.app.state.registries,
    )
    audit_card = parser.parse_form()

    # unnest audit section into list of dicts and save to csv
    audit_section = audit_card.audit.model_dump()
    audit_records = []

    for section, questions in audit_section.items():
        for question_nbr, question in questions.items():
            audit_records.append(
                {
                    "topic": section,
                    "number": question_nbr,
                    "question": question["question"],
                    "purpose": question["purpose"],
                    "response": question["response"],
                }
            )

    response, path = write_audit_to_csv(
        audit_records=audit_records,
        field_names=field_names,
    )

    background_tasks.add_task(remove_file, path)

    return response
