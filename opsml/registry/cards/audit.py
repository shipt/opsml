# mypy: disable-error-code="call-arg"
# pylint: disable=too-many-lines

import os
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, root_validator
from rich.console import Console
from rich.table import Table

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.records import AuditRegistryCard, RegistryCard

logger = ArtifactLogger.get_logger(__name__)
DIR_PATH = os.path.dirname(__file__)
AUDIT_TEMPLATE_PATH = os.path.join(DIR_PATH, "templates/audit_card.yaml")

# class Question:
#    def __init__(self, purpose: str, question: str):
#        self.purpose = purpose
#        self.question = question
#        self.response = None
#
#    def __repr__(self):
#        return f"Question(purpose={self.purpose}, question={self.question}, response={self.response})"
#
#
# class AuditSection:
#    def __init__(self, section_name: str):
#        self.section_name = section_name
#        self.questions = []
#
#    def add_question(self, purpose: str, question: str):
#        self.questions.append(Question(purpose, question))
#
#    def __repr__(self):
#        return f"AuditSection(section_name={self.section_name}, questions={self.questions})"
#
#
# class AuditCard:
#    def __init__(self):
#        self.sections = {}
#
#    def add_section(self, section_name: str):
#        self.sections[section_name] = AuditSection(section_name)
#
#    def add_question_to_section(self, section_name: str, purpose: str, question: str):
#        if section_name not in self.sections:
#            self.add_section(section_name)
#        self.sections[section_name].add_question(purpose, question)
#
#    def collect_responses(self):
#        for section in self.sections.values():
#            for question in section.questions:
#                question.response = input(f"Question: {question.question} \n Purpose: {question.purpose}: \n")
#
#    def to_yaml(self, filename: str):
#        data = {}
#        for section_name, section in self.sections.items():
#            data[section_name] = {
#                "questions": [
#                    {"purpose": question.purpose, "question": question.question, "response": question.response}
#                    for question in section.questions
#                ]
#            }
#        with open(filename, "w") as file:
#            yaml.dump(data, file)
#
#
# if __name__ == "__main__":
#    audit_card = AuditCard()
#
#    # Load the YAML file and populate the AuditCard
#    with open("opsml/registry/cards/templates/audit.yaml") as file:
#        yaml_data = yaml.load(file, Loader=yaml.FullLoader)
#        for section_name, section_data in yaml_data.items():
#            for question_data in section_data:
#                audit_card.add_question_to_section(section_name, question_data["purpose"], question_data["question"])
#
#    # Collect user responses
#    audit_card.collect_responses()
#
#    # Output the audit report as YAML file
#    audit_card.to_yaml("opsml/registry/cards/templates/audit_responses.yaml")


# create new python class that inherits from ArtifactCard and is called AuditCard
class Question(BaseModel):
    question: str
    purpose: str
    response: Optional[str] = None

    class Config:
        allow_mutation = True


class AuditSections(BaseModel):
    business_understanding: Dict[int, Question]
    data_understanding: Dict[int, Question]
    data_preparation: Dict[int, Question]
    modeling: Dict[int, Question]
    evaluation: Dict[int, Question]
    deployment_ops: Dict[int, Question]
    misc: Dict[int, Question]

    @root_validator(pre=True)
    def load_sections(cls, values):
        """Loads audit sections from template"""

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
    audit_uri: Optional[str] = None
    datacard_uids: List[str] = []
    modelcard_uids: List[str] = []
    runcard_uids: List[str] = []
    approved: bool = False

    def create_registry_record(self) -> RegistryCard:
        """Creates a registry record for a audit"""

        return AuditRegistryCard(**self.dict())

    def add_card_uid(self, card_type: str, uid: str) -> None:
        """
        Adds a card uid to the appropriate card uid list for tracking

        Args:
            card_type:
                ArtifactCard class name
            uid:
                Uid of registered ArtifactCard
        """
        from opsml.registry.sql.registry import (  # pylint: disable=cyclic-import
            AuditCardRegistry,
        )
        from opsml.registry.sql.sql_schema import (  # pylint: disable=cyclic-import
            RegistryTableNames,
        )

        audit_registry = AuditCardRegistry(RegistryTableNames.AUDIT.value)

        if card_type == CardType.DATACARD:
            if audit_registry.validate_uid(uid, RegistryTableNames.DATA.value):
                self.datacard_uids = [uid, *self.datacard_uids]
                return  # Exit early

        elif card_type == CardType.MODELCARD:
            if audit_registry.validate_uid(uid, RegistryTableNames.MODEL.value):
                self.modelcard_uids = [uid, *self.modelcard_uids]
                return  # Exit early

        elif card_type == CardType.RUNCARD:
            # RunCard does not get a validation because registration will occur at end of run
            self.runcard_uids = [uid, *self.runcard_uids]
            return  # Exit early

        raise ValueError(f"Invalid uid {uid} for {card_type}. Uid must be registered prior to adding to AuditCard.")

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

    @property
    def card_type(self) -> str:
        return CardType.AUDITCARD.value

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
            logger.error("Question %s not found in section %s", question_nbr, section)
            raise exc
