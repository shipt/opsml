# pylint: disable-all
import sys

from mlflow.server.handlers import initialize_backend_stores
from mlflow.utils.server_cli_utils import resolve_default_artifact_root

from opsml.app.core.config import get_mlflow_config, MlFlowConfig
from opsml.helpers.logging import ArtifactLogger

logger = ArtifactLogger.get_logger(__name__)


def initialize_mlflow() -> MlFlowConfig:
    """Initializes the mlflow server.
    This must be ran before HTTP serving begins. It simulates the cli launching the server.
    Raises:
        ValueError: One or more env vars is missing.
    """
    config = get_mlflow_config()
    if config.MLFLOW_SERVER_FILE_STORE is None or len(config.MLFLOW_SERVER_FILE_STORE) == 0:
        raise ValueError("_MLFLOW_SERVER_FILE_STORE env var is invalid")
    if config.MLFLOW_SERVER_ARTIFACT_DESTINATION is None or len(config.MLFLOW_SERVER_ARTIFACT_DESTINATION) == 0:
        raise ValueError("_MLFLOW_SERVER_ARTIFACT_DESTINATION env var is invalid")
    if config.MLFLOW_SERVER_ARTIFACT_ROOT is None or len(config.MLFLOW_SERVER_ARTIFACT_ROOT) == 0:
        raise ValueError("_MLFLOW_SERVER_ARTIFACT_ROOT env var is invalid")

    logger.info("-------------------------------------------------------")
    logger.info("Starting mlflow")
    logger.info("MLFLOW_SERVER_ARTIFACT_DESTINATION: %s", config.MLFLOW_SERVER_ARTIFACT_DESTINATION)
    logger.info("MLFLOW_SERVER_ARTIFACT_ROOT: %s", config.MLFLOW_SERVER_ARTIFACT_ROOT)
    logger.info("MLFLOW_SERVER_FILE_STORE: %s", config.MLFLOW_SERVER_FILE_STORE)
    logger.info("MLFLOW_SERVER_SERVE_ARTIFACTS: %s", config.MLFLOW_SERVER_SERVE_ARTIFACTS)
    logger.info("-------------------------------------------------------")

    # Ensure that both backend_store_uri and default_artifact_uri are set correctly.
    backend_store_uri = config.MLFLOW_SERVER_FILE_STORE
    registry_store_uri = backend_store_uri  # yes, this is correct. the registry store default is the backend_store_uri
    default_artifact_root = config.MLFLOW_SERVER_ARTIFACT_ROOT

    default_artifact_root = resolve_default_artifact_root(True, default_artifact_root, backend_store_uri)
    try:
        initialize_backend_stores(backend_store_uri, registry_store_uri, default_artifact_root)
        return config
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error initializing backend store")
        logger.exception(e)
        sys.exit(1)
