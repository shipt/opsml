from typing import Dict
from opsml.registry import AuditCard, CardRegistry
import pytest


def test_audit_card(
    db_registries: Dict[str, CardRegistry],
):
    audit_registry = db_registries["audit"]
    card = AuditCard(name="audit_card", team="team", user_email="test")

    assert card.business[1].response is None
    card.answer_question(section="business", question_nbr=1, response="response")
    assert card.business[1].response is not None

    # test listing all sections
    card.list_questions()

    # test listing specific section
    card.list_questions(section="business")

    assert card.card_type == "audit"

    audit_registry.register_card(card=card)


def test_audit_card_failure():
    card = AuditCard(name="audit_card", team="team", user_email="test")

    with pytest.raises(ValueError):
        card._get_section("not_a_section")

    with pytest.raises(KeyError):
        card.answer_question(section="business", question_nbr=100, response="response")
