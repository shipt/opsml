from opsml.registry.sql.settings import settings
from opsml.registry.storage.types import ArtifactStorageSpecs
from opsml.registry.cards import ArtifactCard


class CardStorageClient:
    def __init__(self):
        self.storage_client = settings.storage_client

    def set_artifact_storage_spec(self, table_name: str, card: ArtifactCard) -> None:
        """Creates artifact storage info to associate with artifacts"""

        save_path = f"{table_name}/{card.team}/{card.name}/v{card.version}"

        artifact_storage_spec = ArtifactStorageSpecs(save_path=save_path)
        self._update_storage_client_metadata(storage_specdata=artifact_storage_spec)

    def update_storage_client_metadata(self, storage_specdata: ArtifactStorageSpecs):
        """Updates storage metadata"""
        self.storage_client.storage_spec = storage_specdata
