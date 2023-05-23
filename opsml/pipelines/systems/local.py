from graphlib import TopologicalSorter
from typing import List

from opsml.helpers import utils
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems.base import Pipeline
from opsml.pipelines.types import PipelineSystem
from opsml.pipelines.utils import stdout_msg

logger = ArtifactLogger.get_logger(__name__)


def _execute_subprocess(command: str) -> None:
    """
    Executes suprocess using Popen. Prints shell output.

    Args:
        command:
            Command to execute
    """

    import subprocess  # pylint: disable=import-outside-toplevel

    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
    ) as process:
        for stdout_line in process.stdout:  # type:ignore
            logger.info(stdout_line)

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, process.args)


class LocalPipeline(Pipeline):
    @property
    def run_order(self) -> List[str]:
        """Parses tasks upstream dependencies and determines run"""
        relationships = {}
        for current_task in self.tasks:
            relationships[current_task.entry_point] = {
                task.entry_point for task in self.tasks if task.name in current_task.upstream_tasks
            }

        sorter = TopologicalSorter(relationships)
        return list(sorter.static_order())

    def schedule(self):
        """
        Schedules a pipelines.
        """
        logger.info("Scheduling is not supported for local pipelines")

    def build(self) -> None:
        """
        Builds a LocalPipeline

        Args:
            pipeline_config:
                Pipeline configuration pydantic model

        Returns:
            `PipelineJobModel`

        """
        return None

    def run(self) -> None:
        """
        Runs a Local Pipeline
        """

        pipelinecard_uid = self.pipelinecard_card.uid
        tasks = self.run_order
        dir_path = self.specs.code_uri

        # running tasks sequentially
        for task in tasks:
            file_path = utils.FindPath.find_filepath(name=task, path=dir_path)
            command = f"export PIPELINEcard_uid={pipelinecard_uid}; " f"poetry run python {file_path};"
            _execute_subprocess(command=command)
        stdout_msg("Local pipeline completed successfully!")

    @staticmethod
    def validate(pipeline_system: PipelineSystem) -> bool:
        return pipeline_system == PipelineSystem.LOCAL
