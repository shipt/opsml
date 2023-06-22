# pylint: disable=too-many-lines

from typing import Optional, List

from pydantic import validator, BaseModel

from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.records import ProjectRegistryRecord, RegistryRecord


class Question(BaseModel):
    question: str
    purpose: str
    response: Optional[str] = None


class BaseAudit:
    questions: List[Question]


class DataUnderstanding(BaseAudit):
    pass


class DataPreparation(BaseAudit):
    pass


class DataAudit(BaseModel):
    understanding: DataUnderstanding
    preparation: DataPreparation


class ModelAudit(BaseAudit):
    pass


class EvaluationAudit(BaseAudit):
    pass


class DeploymentAudit(BaseAudit):
    pass


class AuditCard(ArtifactCard):
    """
    Card containing audit information
    """

    data: DataAudit
    model: ModelAudit
    evaluation: EvaluationAudit
    deployment: DeploymentAudit

    def load(self):
        """Load section questions from templates

        Maybe make templates with yaml?

        i.e.:

        data:
            understanding:
                - Question
                  Purpose
                  Response
                - Question
                  Purpose
                  Response
            preparation:
                - Question
                  Purpose
                  Response
                - Question
                  Purpose
                  Response
        model:
            - Question
              Purpose
              Response
        evaluation:
            - Question
              Purpose
              Response
        deployment:
            - Question
              Purpose
              Response
        """

    def score(self):
        "Audit score"
