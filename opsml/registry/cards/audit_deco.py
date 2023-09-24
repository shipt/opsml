from typing import Optional

from opsml.registry.cards.types import CardType
from opsml.registry.cards import AuditCard


def add_to_auditcard(self, auditcard: Optional[AuditCard] = None, auditcard_uid: Optional[str] = None) -> None:
    """Add card uid to auditcard

    Args:
        auditcard:
            Optional AuditCard to add card uid to
        auditcard_uid:
            Optional uid of AuditCard to add card uid to

    """

    if self.card_type == CardType.AUDITCARD:
        raise ValueError("add_to_auditcard is not implemented for AuditCard")

    if self.uid is None:
        raise ValueError("Card must be registered before adding to auditcard")

    if auditcard_uid is not None:
        from opsml.registry.sql.registry import (  # pylint: disable=cyclic-import
            CardRegistry,
        )

        audit_registry = CardRegistry(registry_name="audit")
        auditcard: AuditCard = audit_registry.load_card(uid=auditcard_uid)
        auditcard.add_card(card=self)
        audit_registry.update_card(card=auditcard)

        if self.card_type in [CardType.DATACARD, CardType.MODELCARD]:
            self.metadata.auditcard_uid = auditcard.uid

        return None

    if auditcard is not None:
        return auditcard.add_card(card=self)


def auditable(cls_):
    setattr(cls_, "add_to_auditcard", add_to_auditcard)
    return cls_
