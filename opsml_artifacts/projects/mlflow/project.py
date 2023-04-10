# pylint: disable=invalid-envvar-value
import os
from contextlib import contextmanager
from typing import Iterator, Optional, cast

from mlflow.artifacts import download_artifacts
from mlflow.entities.run_data import RunData

# helpers
from opsml_artifacts.helpers.logging import ArtifactLogger
from opsml_artifacts.helpers.types import OpsmlUri
from opsml_artifacts.projects.base.project import OpsmlProject
from opsml_artifacts.projects.base.types import MlflowProjectInfo
from opsml_artifacts.projects.mlflow._active_run import MlflowActiveRun
from opsml_artifacts.projects.mlflow._run_manager import _MlflowRunManager

# porjects
from opsml_artifacts.projects.mlflow.mlflow_utils import (
    get_mlflow_client,
    get_project_id,
)

logger = ArtifactLogger.get_logger(__name__)


class MlflowProject(OpsmlProject):
    def __init__(self, info: MlflowProjectInfo):
        """
        Instantiates an mlflow project which log cards, metrics and params to
        the opsml registry and mlflow via a "run" object.

        If info.run_id is set, that run_id will be loaded as read only. In read
        only mode, you can retrieve cards, metrics, and params, however you
        cannot write new data. If you wish to record data/create a new run, you will
        need to enter the run context.

        Example:

            project: MlFlowProject = get_project(
                MlFlowProjectInfo(
                    name="test-project",
                    team="devops-ml",
                    # If run_id is omitted, a new run is created.
                    run_id="123ab123kaj8u8naskdfh813",
                )
            )
            # the project is in "read only" mode. all read operations will work
            for k, v in project.params:
                logger.info("%s = %s", k, v)

            # creating a project run
            with project.run() as run:
                # Now that the run context is entered, it's in read/write mode
                # You can write cards, params, and metrics to the project.
                run.log_param(key="my_param", value="12.34")

        Args:
            info:
                Run information. if a run_id is given, that run is set
                as the project's current run.
        """

        tracking_uri = info.tracking_uri or os.getenv(OpsmlUri.TRACKING_URI)

        # dont want to expose mlflow client in project interface
        mlflow_client = get_mlflow_client(tracking_uri=tracking_uri)
        self._project_id = get_project_id(
            project_id=info.project_id,
            mlflow_client=mlflow_client,
        )

        # Set the run manager
        self._run_mgr = _MlflowRunManager(
            run_id=info.run_id,
            project_id=self._project_id,
            mlflow_client=mlflow_client,
            project_info=info,
        )

    @property
    def run_data(self) -> RunData:
        return self._run_mgr.mlflow_client.get_run(self.run_id).data

    @contextmanager
    def run(self, run_name: Optional[str] = None) -> Iterator[MlflowActiveRun]:
        """
        Starts mlflow run for project

        Args:
            run_name:
                Optional run name
        """

        self._run_mgr.start_run(run_name=run_name)

        yield cast(MlflowActiveRun, self._run_mgr.active_run)

        self._run_mgr.end_run()

    def download_artifacts(
        self,
        artifact_path: Optional[str] = None,
        local_path: Optional[str] = None,
    ) -> str:
        """
        Download an artifact or artifacts associated with a run_id

        Args:
            artifact_path:
                Optional path that contains artifact(s) to download
            local_path:
                Local path (directory) to download artifacts to

        Returns:
            Artifact path
        """
        return download_artifacts(
            run_id=self.run_id,
            artifact_path=artifact_path,
            dst_path=local_path,
            tracking_uri=self._run_mgr.mlflow_client.tracking_uri,
        )

    def list_artifacts(self) -> dict[str, float]:
        """List artifacts for the current run"""
        return self._run_mgr.mlflow_client.list_artifacts(
            run_id=self.run_id,
        )

    @property
    def metrics(self) -> dict[str, float]:
        return self.run_data.metrics

    @property
    def params(self) -> dict[str, str]:
        return self.run_data.params

    @property
    def tags(self) -> dict[str, str]:
        return self.run_data.tags
