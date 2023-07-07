# pylint: disable=too-many-lines
import os
from typing import Optional, List
import yaml
from pydantic import validator, BaseModel, root_validator
from rich.console import Console
from rich.table import Table
from rich.text import Text
from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.records import ProjectRegistryRecord, RegistryRecord
import yaml


DIR_PATH = os.path.dirname(__file__)
AUDIT_TEMPLATE_PATH = os.path.join(DIR_PATH, "templates/audit_card.yaml")


class Question:
    def __init__(self, purpose: str, question: str):
        self.purpose = purpose
        self.question = question
        self.response = None

    def __repr__(self):
        return f"Question(purpose={self.purpose}, question={self.question}, response={self.response})"


class AuditSection:
    def __init__(self, section_name: str):
        self.section_name = section_name
        self.questions = []

    def add_question(self, purpose: str, question: str):
        self.questions.append(Question(purpose, question))

    def __repr__(self):
        return f"AuditSection(section_name={self.section_name}, questions={self.questions})"


class AuditCard:
    def __init__(self):
        self.sections = {}

    def add_section(self, section_name: str):
        self.sections[section_name] = AuditSection(section_name)

    def add_question_to_section(self, section_name: str, purpose: str, question: str):
        if section_name not in self.sections:
            self.add_section(section_name)
        self.sections[section_name].add_question(purpose, question)

    def collect_responses(self):
        for section in self.sections.values():
            for question in section.questions:
                question.response = input(f"Question: {question.question} \n Purpose: {question.purpose}: \n")

    def to_yaml(self, filename: str):
        data = {}
        for section_name, section in self.sections.items():
            data[section_name] = {
                "questions": [
                    {"purpose": question.purpose, "question": question.question, "response": question.response}
                    for question in section.questions
                ]
            }
        with open(filename, "w") as file:
            yaml.dump(data, file)


if __name__ == "__main__":
    audit_card = AuditCard()

    # Load the YAML file and populate the AuditCard
    with open("opsml/registry/cards/templates/audit.yaml") as file:
        yaml_data = yaml.load(file, Loader=yaml.FullLoader)
        for section_name, section_data in yaml_data.items():
            for question_data in section_data:
                audit_card.add_question_to_section(section_name, question_data["purpose"], question_data["question"])

    # Collect user responses
    audit_card.collect_responses()

    # Output the audit report as YAML file
    audit_card.to_yaml("opsml/registry/cards/templates/audit_responses.yaml")


# create new python class that inherits from ArtifactCard and is called AuditCard


class Question(BaseModel):
    question: str
    purpose: str
    response: Optional[str] = None

    class Config:
        allow_mutation = True


class AuditSections(BaseModel):
    business_understanding: List[Question]
    data_understanding: List[Question]
    data_preparation: List[Question]
    modeling: List[Question]
    evaluation: List[Question]
    deployment_ops: List[Question]
    misc: List[Question]

    @root_validator(pre=True)
    def load_sections(cls, values):
        """Loads audit sections from template"""

        with open(AUDIT_TEMPLATE_PATH, "r") as stream:
            try:
                audit_sections = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise exc
        return audit_sections


class AuditCard(ArtifactCard):
    """
    Card containing audit information
    """

    audit: AuditSections = AuditSections()

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record for a project"""

        return ProjectRegistryRecord(**self.dict())

    @property
    def card_type(self) -> str:
        return CardType.AUDITCARD.value
    
    # create a function that lists questions by section and number and displays them in a rich table
    
    def list_questions(self):
    
        console = Console()
        table = Table(title=f"{registry_name} cards")
        table.add_column("Section", no_wrap=True)
        table.add_column("Number")
        table.add_column("Question", justify="right")
        
        for section in self.audit:
            
        
    
    def answer_question(self, section: str, question: str, response: str):
        """Answers a question in a section"""

        for q in self.audit[section]:
            if q.question == question:
                q.response = response
                return
        raise ValueError(f"Question {question} not found in section {section}")


# class BaseAudit:
#     questions: List[Question]


# class DataUnderstanding(BaseAudit):
#     pass


# class DataPreparation(BaseAudit):
#     pass


# class DataAudit(BaseModel):
#     understanding: DataUnderstanding
#     preparation: DataPreparation


# class ModelAudit(BaseAudit):
#     pass


# class EvaluationAudit(BaseAudit):
#     pass


# class DeploymentAudit(BaseAudit):
#     pass


# class AuditCard(ArtifactCard):
#     """
#     Card containing audit information
#     """

#     data: DataAudit
#     model: ModelAudit
#     evaluation: EvaluationAudit
#     deployment: DeploymentAudit

#     def load(self):
#         """Load section questions from templates

#         Maybe make templates with yaml?

#         i.e.:

#         data:
#             understanding:
#                 - Question
#                   Purpose
#                   Response
#                 - Question
#                   Purpose
#                   Response
#             preparation:
#                 - Question
#                   Purpose
#                   Response
#                 - Question
#                   Purpose
#                   Response
#         model:
#             - Question
#               Purpose
#               Response
#         evaluation:
#             - Question
#               Purpose
#               Response
#         deployment:
#             - Question
#               Purpose
#               Response
#         """

#     def score(self):
#         "Audit score"
