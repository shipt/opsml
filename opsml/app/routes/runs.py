# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import tempfile

# pylint: disable=protected-access
from pathlib import Path
from typing import Any, Dict

import joblib
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, status

from opsml import CardRegistry, RunCard
from opsml.app.core.dependencies import swap_opsml_root

# from opsml.app.routes.utils import error_to_500
from opsml.helpers.logging import ArtifactLogger
from opsml.storage.client import StorageClientBase
from opsml.types import SaveName, RegistryTableNames

logger = ArtifactLogger.get_logger()

# Constants
TEMPLATE_PATH = Path(__file__).parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_PATH)

router = APIRouter()


@router.get("/runs/graphics", name="graphic_uris")
async def get_graphic_uris(request: Request, run_uid: str) -> Dict[str, str]:
    """Method for generating presigned urls for graphics page

    Args:
        request:
            The incoming HTTP request.
        run_uid:
            The uid of the run.

    Returns:
        Dict[str, str]: A dictionary of artifact names and their corresponding presigned urls.
    """
    uris = {}

    storage_client: StorageClientBase = request.app.state.storage_client
    run_registry: CardRegistry = request.app.state.registries.run
    storage_root = request.app.state.storage_root

    card: RunCard = run_registry.load_card(uid=run_uid)

    for name, artifact in card.artifact_uris.items():
        remote_path = Path(artifact.remote_path)
        suffix = remote_path.suffix
        if suffix in [".png", ".jpg", ".jpeg", ".tiff", ".gif", ".bmp", ".svg"]:
            remote_path = swap_opsml_root(request, remote_path)

            # get remote path relative to storage root
            remote_path = remote_path.relative_to(storage_root)
            uris[name] = storage_client.generate_presigned_url(remote_path, expiration=600)

    return uris


@router.get("/runs/graphs", name="graphs")
async def get_graph_plots(request: Request, runcard_uri: str) -> Dict[str, Any]:
    """Method for loading plots for a run

    Args:
        request:
            The incoming HTTP request.
        run_uid:
            The uid of the run.

    Returns:
        Dict[str, str]: A dictionary of plot names and their corresponding plots.
    """
    storage_client: StorageClientBase = request.app.state.storage_client
    storage_root = request.app.state.storage_root

    loaded_graphs: Dict[str, Any] = {}
    uri = Path(f"{storage_root}/{RegistryTableNames.RUN.value}/{runcard_uri}")

    graph_path = uri / SaveName.GRAPHS.value

    path_exists = storage_client.exists(graph_path)

    # skip if path does not exist
    if not path_exists:
        return loaded_graphs

    paths = storage_client.ls(graph_path)

    logger.debug("Found {} graphs in {}", paths, graph_path)
    if paths:
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                for path in paths:
                    rpath = graph_path / Path(path).name
                    lpath = Path(tmp_dir) / rpath.name

                    storage_client.get(rpath, lpath)
                    graph: Dict[str, Any] = joblib.load(lpath)
                    loaded_graphs[graph["name"]] = graph

            return loaded_graphs
        except Exception as error:
            logger.error(f"Failed to load graphs: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}") from error
