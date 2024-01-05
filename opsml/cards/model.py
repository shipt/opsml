# pylint: disable=too-many-lines
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import ConfigDict, SerializeAsAny, field_validator

from opsml.cards.base import ArtifactCard
from opsml.helpers.logging import ArtifactLogger
from opsml.model.interfaces import ModelInterface
from opsml.types import CardType, ModelCardMetadata, ModelMetadata

logger = ArtifactLogger.get_logger()


class ModelCard(ArtifactCard):
    """Create a ModelCard from your trained machine learning model.
    This Card is used in conjunction with the ModelCardCreator class.

    Args:
        name:
            Name for the model specific to your current project
        team:
            Team that this model is associated with
        user_email:
            Email to associate with card
        interface:
            Trained model interface. Can be one of SklearnModel, TensorFlowModel, PyTorchModel
            LightningModel, LGBModel, XGBoostModel, HuggingFaceModel
        uid:
            Unique id (assigned if card has been registered)
        version:
            Current version (assigned if card has been registered)
        datacard_uid:
            Uid of the DataCard associated with training the model
        to_onnx:
            Whether to convert the model to onnx or not
        metadata:
            `ModelCardMetadata` associated with the model
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=("protect_",),
        validate_assignment=True,
    )

    interface: SerializeAsAny[ModelInterface]
    datacard_uid: Optional[str] = None
    to_onnx: bool = False
    metadata: ModelCardMetadata = ModelCardMetadata()

    @field_validator("datacard_uid", mode="before")
    @classmethod
    def check_uid(cls, datacard_uid: Optional[str] = None):
        if datacard_uid is None:
            return datacard_uid

        try:
            UUID(datacard_uid, version=4)  # we use uuid4
            return datacard_uid

        except ValueError:
            raise ValueError("Datacard uid is not a valid uuid")

    def load_model(self, **kwargs: Dict[str, Any]) -> None:
        """Loads model, preprocessor and sample data to interface"""
        from opsml.cards.card_loader import ModelCardLoader

        ModelCardLoader(self).load_model(**kwargs)

    def load_onnx_model(self, **kwargs: Dict[str, Any]) -> None:
        """Loads onnx model to interface"""
        from opsml.cards.card_loader import ModelCardLoader

        ModelCardLoader(self).load_onnx_model(**kwargs)

    def create_registry_record(self) -> Dict[str, Any]:
        """Creates a registry record from the current ModelCard"""

        exclude_vars = {"interface": {"model", "preprocessor", "sample_data", "onnx_model"}}
        dumped_model = self.model_dump(exclude=exclude_vars)

        return dumped_model

    @property
    def model(self) -> Any:
        """Quick access to model from interface"""
        return self.interface.model

    @property
    def sample_data(self) -> Any:
        """Quick access to sample data from interface"""
        return self.interface.sample_data

    @property
    def preprocessor(self) -> Any:
        """Quick access to preprocessor from interface"""
        return self.interface.preprocessor

    @property
    def model_metadata(self) -> ModelMetadata:
        """Loads `ModelMetadata` class"""

        from opsml.cards.card_loader import ModelCardLoader

        return ModelCardLoader(self).load_model_metadata()

    @property
    def card_type(self) -> str:
        return CardType.MODELCARD.value