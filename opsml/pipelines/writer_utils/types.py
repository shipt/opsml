"""Module for pipeline data models"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from opsml.registry.cards.types import CardType

env_pattern = re.compile(r".*?\${(.*?)}.*?")


@dataclass
class ParserOutput:
    cards_to_save: Optional[List[Optional[str]]] = None
    func_body: Optional[str] = None
    func_def: Optional[str] = None

    @property
    def body_text(self):
        if self.func_body is not None:
            return self.func_body
        raise ValueError("No func body")

    @property
    def signature_text(self):
        if self.func_def is not None:
            return self.func_def
        raise ValueError("No function signature")

    @property
    def cards(self) -> List[Optional[str]]:
        if self.cards_to_save is not None:
            return self.cards_to_save
        raise ValueError("No Cards found")


@dataclass
class FuncMetadata:
    name: str
    text: str
    definition: str
    assigned_cards: List[Optional[str]]


class SigTypeHints(str, Enum):
    STEP = "Step"
    ARTIFACT_CARD = "ArtifactCard"


SIG_TYPES = list(SigTypeHints)


ARTIFACT_CARD_TYPES = list(CardType)
