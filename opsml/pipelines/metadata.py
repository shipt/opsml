import os
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

from opsml_artifacts.registry import CardRegistry, DataCard, ExperimentCard, ModelCard, PipelineCard
from opsml_artifacts.registry.cards.pipeline_loader import PipelineLoader
from opsml_artifacts.helpers.logging import ArtifactLogger

from opsml_artifacts.helpers.utils import ConfigFileLoader

ArtifactCards = Union[ModelCard, ExperimentCard, DataCard]

logger = ArtifactLogger.get_logger(__name__)


class CardLoader:
    def __init__(self, uid: str):  # type: ignore
        self.uid = uid
        self.card_deck = self._loadcard_uids()
        self.pipeline_registry = CardRegistry(registry_name="pipeline")

    def _loadcard_uids(self) -> Dict[str, Dict[str, str]]:
        loader = PipelineLoader(pipelinecard_uid=self.uid)
        return loader.card_uids

    def load_pipeline_card(self) -> PipelineCard:
        return self.pipeline_registry.load_card(uid=self.uid)

    def load_card_object(self, card: ArtifactCards):

        for attr in (
            "load_data",
            "load_trained_model",
            "load_sample_data",
        ):
            if hasattr(card, attr):
                getattr(card, attr)()

    def load_card(self, registry_name: str, uid: str) -> ArtifactCards:
        registry = CardRegistry(registry_name=registry_name)
        card = registry.load_card(uid=uid)
        self.load_card_object(card=card)
        return card


class CardRegister:
    def get_registry_name(self, card: ArtifactCards):
        return card.__class__.__name__.split("Card")[0].lower()

    def register_card(self, registry_name: str, card: ArtifactCards):
        registry = CardRegistry(registry_name=registry_name)
        registry.register_card(card=card)


class GlobalLoader:
    @staticmethod
    def load_globals(cards_to_load: List[str], card_deck: Dict[str, ArtifactCards], global_vars: Dict[str, Any]):
        for card_name, card in card_deck.items():
            if card_name in cards_to_load:
                global_vars[card_name] = card


class CardUpdater:
    def __init__(self, registry_name: str):
        self.registry_name = registry_name

    def _create_registry(self) -> Type[CardRegistry]:
        return CardRegistry(registry_name=self.registry_name)

    def _load_card(self, registry: Type[CardRegistry], uid: str) -> ArtifactCards:
        return registry.load_card(uid=uid)

    def update_card(self, card: ArtifactCards) -> None:
        raise NotImplementedError

    @staticmethod
    def validate(registry_name: str):
        raise NotImplementedError


class ExperimentUpdater(CardUpdater):
    def update_card(self, card: ArtifactCards) -> None:
        registry = self._create_registry()
        registered_card = self._load_card(registry=registry, uid=card.uid)

        if registered_card.dict() != card.dict():
            registry.update_card(card=card)

    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name == "experiment"


class MetadataTracker:
    def __init__(self):
        """Metadata tracker that is used to track pipeline artifacts

        Args:
            cards_to_load (list): Optional list of cards to load
        """
        pipeline_id = os.getenv("PIPELINEcard_uid").strip()

        logger.info("Loading Pipeline data for %s", pipeline_id)

        self.card_loader = CardLoader(uid=pipeline_id)
        self.card_register = CardRegister()
        self._pipeline_card = self.card_loader.load_pipeline_card()

    @property
    def pipeline_card(self) -> PipelineCard:
        return self._pipeline_card

    def load_config(self, filename: str = "pipeline-config.yaml") -> Dict[Union[str, int], Any]:
        """Loads a pipeline configuration file

        Args:
            Filename: Name of your configuration file. Default is
            "pipeline-config.yaml".

        Returns:
            Configuration file as dictionary
        """
        return ConfigFileLoader(filename=filename).load()

    def save_card_to_pipeline(self, card: ArtifactCards):

        """Registers the current card and updates the current PipelineCard

        Args:
            card (ArtifactCard): ArtifactCard to register

        """
        card_type = self._register_assigned_card(card=card)
        self._update_pipeline_card(card=card, card_name=card.name, card_type=card_type)

    def load_cards_from_pipeline(
        self,
        cards_to_load: Optional[List[str]] = None,
    ) -> Tuple[Any, ...]:
        """Load cards associated with current PipelineCard

        Args:
            cards_to_load (list): Optional list of card names to load
        Returns:
            Tuple of cards
        """
        cards = []
        if cards_to_load is not None:
            cards_to_load = cast(List[str], cards_to_load)
            for card in cards_to_load:
                card_info = self.card_loader.card_deck[card]
                cards.append(self.card_loader.load_card(registry_name=card_info["card_type"], uid=card_info["uid"]))
        return tuple(cards)

    def load_cards_to_global(
        self,
        global_vars: Dict[str, Any],
        cards_to_load: Optional[List[str]] = None,
    ):
        if bool(cards_to_load):
            cards_to_load = cast(List[str], cards_to_load)
            for card in cards_to_load:
                card_info = self.card_loader.card_deck[card]
                global_vars[card] = self.card_loader.load_card(
                    registry_name=card_info["card_type"],
                    uid=card_info["uid"],
                )

    def save_cards(self, assigned_cards: Optional[List[str]], global_vars: Dict[str, Any]):
        if bool(assigned_cards):
            assigned_cards = cast(List[str], assigned_cards)
            for card_name in assigned_cards:
                self._register_and_update(card_name, global_vars[card_name])

        self._update_existing_cards(global_vars)

    def _update_existing_cards(self, global_vars: Dict[str, Any]) -> None:
        if not bool(self.card_loader.card_deck):
            return

        for card_name in self.card_loader.card_deck:
            current_card = global_vars.get(card_name)
            if bool(current_card):

                current_card = cast(ArtifactCards, current_card)
                self._check_and_update_card(current_card)

    def _check_and_update_card(self, current_card: ArtifactCards) -> None:
        registry_name = self.card_register.get_registry_name(current_card)

        updater = next(
            (
                updater
                for updater in CardUpdater.__subclasses__()
                if updater.validate(
                    registry_name=registry_name,
                )
            ),
            None,
        )

        if updater:
            updater(registry_name=registry_name).update_card(card=current_card)

    def _register_and_update(self, card_name: str, card: ArtifactCards):

        card_type = self._register_assigned_card(card=card)
        self._update_pipeline_card(card=card, card_name=card_name, card_type=card_type)

    def _register_assigned_card(self, card: ArtifactCards) -> str:
        """Registers assigned card. Skips if the card already has a versionand uid"""

        registry_name = self.card_register.get_registry_name(card=card)
        if not card.uid:
            self.card_register.register_card(registry_name=registry_name, card=card)
        return registry_name

    def _update_pipeline_card(self, card: ArtifactCards, card_type: str, card_name: str):
        self.pipeline_card.addcard_uid(uid=card.uid, name=card_name, card_type=card_type)
        self.card_loader.pipeline_registry.update_card(card=self.pipeline_card)
