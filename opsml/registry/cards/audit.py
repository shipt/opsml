# mypy: disable-error-code="call-arg"
# pylint: disable=too-many-lines

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, model_validator, ConfigDict
from rich.console import Console
from rich.table import Table

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType, CardVersion, Comment, AuditCardMetadata
from opsml.registry.sql.records import AuditRegistryRecord, RegistryRecord


logger = ArtifactLogger.get_logger()
DIR_PATH = os.path.dirname(__file__)
AUDIT_TEMPLATE_PATH = os.path.join(DIR_PATH, "templates/audit_card.yaml")
AUDIT_TEMPLATE_HTML_FILE = "templates/report-copy.html"


# create new python class that inherits from ArtifactCard and is called AuditCard
class Question(BaseModel):
    question: str
    purpose: str
    response: Optional[str] = None

    model_config = ConfigDict(frozen=False)


class AuditSections(BaseModel):
    business_understanding: Dict[int, Question]
    data_understanding: Dict[int, Question]
    data_preparation: Dict[int, Question]
    modeling: Dict[int, Question]
    evaluation: Dict[int, Question]
    deployment_ops: Dict[int, Question]
    misc: Dict[int, Question]

    @model_validator(mode="before")
    def load_sections(cls, values):
        """Loads audit sections from template if no values are provided"""

        if any(values):
            return values
        return cls.load_yaml_template()

    @staticmethod
    def load_yaml_template() -> Dict[str, Dict[int, Dict[str, str]]]:
        with open(AUDIT_TEMPLATE_PATH, "r", encoding="utf-8") as stream:
            try:
                audit_sections = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise exc
        return audit_sections


class AuditQuestionTable:
    """Helper class for creating a rich table to be used with an AuditCard"""

    def __init__(self) -> None:
        self.table = self.create_table()

    def create_table(self):
        table = Table(title="Audit Questions")
        table.add_column("Section", no_wrap=True)
        table.add_column("Number")
        table.add_column("Question")
        table.add_column("Answered", justify="right")
        return table

    def add_row(self, section_name: str, nbr: int, question: Question):
        self.table.add_row(
            section_name,
            str(nbr),
            question.question,
            "Yes" if question.response else "No",
        )

    def add_section(self):
        self.table.add_section()

    def print_table(self):
        console = Console()
        console.print(self.table)


class AuditCard(ArtifactCard):
    """
    Creates an AuditCard for storing audit-related information about a
    machine learning project.

    Args:
        name:
            What to name the AuditCard
        team:
            Team that this card is associated with
        user_email:
            Email to associate with the AuditCard
        audit:
            AuditSections object containing the audit questions and responses
        audit_uri:
            URI to the audit report
        approved:
            Whether the audit has been approved
    """

    audit: AuditSections = AuditSections()
    approved: bool = False
    comments: List[Comment] = []
    metadata: AuditCardMetadata = AuditCardMetadata()

    def add_comment(self, name: str, comment: str) -> None:
        """Adds comment to AuditCard

        Args:
            name:
                Name of person making comment
            comment:
                Comment to add

        """
        comment_model = Comment(name=name, comment=comment)

        if any(comment_model == _comment for _comment in self.comments):
            return  # Exit early if comment already exists

        self.comments.insert(0, comment_model)

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record for a audit"""

        return AuditRegistryRecord(**self.model_dump())

    def add_card(self, card: ArtifactCard) -> None:
        """
        Adds a card uid to the appropriate card uid list for tracking

        Args:
            card:
                Card to add to AuditCard
        """
        from opsml.registry.sql.registry import (  # pylint: disable=cyclic-import
            AuditCardRegistry,
        )
        from opsml.registry.sql.sql_schema import (  # pylint: disable=cyclic-import
            RegistryTableNames,
        )

        if card.card_type.lower() not in [
            CardType.DATACARD.value,
            CardType.MODELCARD.value,
            CardType.RUNCARD.value,
        ]:
            raise ValueError(f"Invalid card type {card.card_type}. Valid card types are: data, model or run")

        audit_registry = AuditCardRegistry(RegistryTableNames.AUDIT.value)

        if card.card_type.lower() == CardType.DATACARD.value:
            if card.uid is None:
                raise ValueError(
                    f"""Card uid must be provided for {card.card_type}. 
                    Uid must be registered prior to adding to AuditCard."""
                )

            if audit_registry.validate_uid(card.uid, RegistryTableNames.DATA.value):
                self.metadata.datacards.append(
                    CardVersion(
                        name=card.name,
                        version=card.version,
                        card_type=card.card_type,
                    )
                )
                return

        elif card.card_type.lower() == CardType.MODELCARD:
            if card.uid is None:
                raise ValueError(
                    f"""Card uid must be provided for {card.card_type}. 
                    Uid must be registered prior to adding to AuditCard."""
                )
            if audit_registry.validate_uid(card.uid, RegistryTableNames.MODEL.value):
                self.metadata.modelcards.append(
                    CardVersion(
                        name=card.name,
                        version=card.version,
                        card_type=card.card_type,
                    )
                )
                return

        elif card.card_type.lower() == CardType.RUNCARD:
            # RunCard does not get a validation because registration will occur at end of run
            self.metadata.runcards.append(
                CardVersion(
                    name=card.name,
                    version=card.version,
                    card_type=card.card_type,
                )
            )
            return  # Exit early

    @property
    def business(self) -> Dict[int, Question]:
        return self.audit.business_understanding

    @property
    def data_understanding(self) -> Dict[int, Question]:
        return self.audit.data_understanding

    @property
    def data_preparation(self) -> Dict[int, Question]:
        return self.audit.data_preparation

    @property
    def modeling(self) -> Dict[int, Question]:
        return self.audit.modeling

    @property
    def evaluation(self) -> Dict[int, Question]:
        return self.audit.evaluation

    @property
    def deployment(self) -> Dict[int, Question]:
        return self.audit.deployment_ops

    @property
    def misc(self) -> Dict[int, Question]:
        return self.audit.misc

    def list_questions(self, section: Optional[str] = None) -> None:
        """Lists all Audit Card questions in a rich table

        Args:
            section:
                Section name. Can be one of: business, data_understanding, data_preparation, modeling,
                evaluation or misc
        """

        table = AuditQuestionTable()

        if section is not None:
            questions = self._get_section(section)
            for nbr, question in questions.items():
                table.add_row(section_name=section, nbr=nbr, question=question)

        else:
            for _section in self.audit:
                section_name, questions = _section
                for nbr, question in questions.items():
                    table.add_row(section_name=section_name, nbr=nbr, question=question)

                table.add_section()

        table.print_table()

    def _get_section(self, section: str) -> Dict[int, Question]:
        """Gets a section from the audit card

        Args:
            section:
                Section name. Can be one of: business, data_understanding, data_preparation, modeling,
                evaluation or misc
        Returns:
            Dict[int, Question]: A dictionary of questions
        """

        if not hasattr(self, section):
            raise ValueError(
                f"""Section {section} not found. Accepted values are: business, data_understanding,
                data_preparation, modeling, evaluation, deployment or misc"""
            )
        _section: Dict[int, Question] = getattr(self, section)
        return _section

    def answer_question(self, section: str, question_nbr: int, response: str) -> None:
        """Answers a question in a section

        Args:
            section:
                Section name. Can be one of: business, data_understanding, data_preparation, modeling, evaluation,
                deployment or misc
            question_nbr:
                Question number
            response:
                Response to the question

        """

        _section: Dict[int, Question] = self._get_section(section)

        try:
            _section[question_nbr].response = response
        except KeyError as exc:
            logger.error("Question {} not found in section {}", question_nbr, section)
            raise exc

    def create_report(self, save_path: str) -> None:
        from jinja2 import FileSystemLoader, Environment

        template_env = Environment(
            loader=FileSystemLoader(searchpath=DIR_PATH),
        )
        template_env.get_template(AUDIT_TEMPLATE_HTML_FILE)

    @property
    def card_type(self) -> str:
        return CardType.AUDITCARD.value
