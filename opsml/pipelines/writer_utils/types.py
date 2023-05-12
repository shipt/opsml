"""Module for pipeline data models"""

import re
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass
from opsml.registry.cards.types import CardType

env_pattern = re.compile(r".*?\${(.*?)}.*?")


@dataclass
class ParserOutput:
    cards_to_save: Optional[List[str]] = None
    func_body: Optional[str] = None
    func_def: Optional[str] = None


@dataclass
class FuncMetadata:
    name: str
    assigned_vars: Optional[List[str]] = None
    text: str
    definition: str


class SigTypeHints(str, Enum):
    STEP = "Step"
    ARTIFACT_CARD = "ArtifactCard"


SIG_TYPES = list(SigTypeHints)


ARTIFACT_CARD_TYPES = list(CardType)
