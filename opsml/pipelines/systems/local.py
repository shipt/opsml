from graphlib import TopologicalSorter
from typing import Dict, List, Union


from opsml_artifacts.helpers.logging import ArtifactLogger
from opsml_artifacts.pipelines.systems.base import Pipeline
from opsml_artifacts.helpers import utils
from opsml_artifacts.helpers.cli_utils import stdout_msg

from opsml_artifacts.pipelines.types import TaskArgs, PipelineJob, PipelineSystem, CodeInfo

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
    def package_code(self) -> CodeInfo:

        """Packages code for a local pipeline run"""

        code_info = self.helpers.packager.package_local(
            params=self.params,
            writer=self.helpers.writer,
        )

        for name, value in code_info:
            setattr(self.params, name, value)

        return code_info

    @staticmethod
    def get_run_order(resources: Dict[str, TaskArgs]) -> List[str]:
        relationships = {}
        for _, args in resources.items():
            relationships[args.entry_point] = {
                resources[parent].entry_point for parent in args.depends_on  # type: ignore
            }

        sorter = TopologicalSorter(relationships)
        return list(sorter.static_order())

    @staticmethod
    def schedule(pipeline_job: PipelineJob):
        """
        Schedules a pipelines.

        Args:
            pipeline_params:
                Pydantic class of pipeline params
            code_info:
                Pydantic class containing package metadata
        """
        logger.info(
            "Scheduling is not currently supported for local pipelines %s",
            pipeline_job.code_info.dict(),
        )

    def build(self) -> PipelineJob:

        """
        Builds a LocalPipeline

        Args:
            pipeline_config:
                Pipeline configuration pydantic model

        Returns:
            `PipelineJobModel`

        """
        if self.params.decorated:
            code_info = self.package_code()
            job: Dict[str, Union[str, List[str]]] = {}
            job["run_order"] = self._get_run_order(resources=self.config.resources)
            job["pipelinecard_uid"] = self.params.pipelinecard_uid
            job["dir_path"] = self.params.code_uri
            return PipelineJob(job=job, code_info=code_info)

        raise ValueError("""Local mode is only supported for decoraged pipelines at the moment""")

    @staticmethod
    def run(pipeline_job: PipelineJob) -> None:

        """
        Runs a Local Pipeline

        Args:
            pipeline_job:
                Vertex pipeline job

        """

        pipelinecard_uid = pipeline_job.job["pipelinecard_uid"]
        tasks = pipeline_job.job["run_order"]
        dir_path = pipeline_job.job["dir_path"]

        # running tasks sequentially
        for task in tasks:
            file_path = utils.FindPath.find_filepath(name=task, path=dir_path)
            command = f"export PIPELINEcard_uid={pipelinecard_uid}; " f"poetry run python {file_path};"
            _execute_subprocess(command=command)

        stdout_msg("Local pipeline completed successfully!")

        Pipeline.delete_files()

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        return pipeline_system == PipelineSystem.LOCAL and is_proxy == False
