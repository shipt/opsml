"""Module for pipeline data models"""

import re
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from opsml_artifacts.registry.cards.types import CardName

env_pattern = re.compile(r".*?\${(.*?)}.*?")


@dataclass
class ParserOutput:
    cards_to_save: Optional[str] = None
    cards_to_load: Optional[str] = None
    func_body: Optional[str] = None
    func_def: Optional[str] = None


@dataclass
class FuncMetadata:
    name: str
    assigned_vars: str
    text: str
    definition: str
    input_vars: str


class SigTypeHints(str, Enum):
    STEP = "Step"
    ARTIFACT_CARD = "ArtifactCard"


SIG_TYPES = list(SigTypeHints)


ARTIFACT_CARD_TYPES = list(CardName)
