"""Module for PipelineRunner Interface"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.request_helpers import ApiRoutes
from opsml.pipelines.base_runner import PipelineRunnerBase
from opsml.pipelines.package import PipelinePackager
from opsml.pipelines.spec import PipelineSpec, PipelineWriterMetadata
from opsml.pipelines.systems.pipeline_getter import get_pipeline_system
from opsml.pipelines.types import PipelineSystem
from opsml.pipelines.utils import stdout_msg
from opsml.pipelines.writer import PipelineWriter
from opsml.registry.sql.settings import settings

logger = ArtifactLogger.get_logger(__name__)


@dataclass
class PipelineHelpers:
    """
    Pipeline helper class
    """

    writer: PipelineWriter
    packager: PipelinePackager


class PipelineRunner(PipelineRunnerBase):
    def __init__(
        self,
        spec_filename: Optional[str] = None,
        pipeline_spec: Optional[PipelineSpec] = None,
        requirements: Optional[str] = None,
    ):
        """
        Interface for building a machine learning pipeline.

        Args:
            spec_filename:
                Optional filename for spec file
            pipeline_spec:
                Optional `PipelineSpec`
            requirements:
                Requirement file name. Name values can be "requirements.txt" (or specific *.txt name) or "poetry.lock"

        """
        super().__init__(
            spec_filename=spec_filename,
            pipeline_spec=pipeline_spec,
            requirements=requirements,
        )

        # gather helpers
        self._helpers = self._set_pipeline_helpers(requirements=requirements)

        # Get pipeline system
        self._pipeline = get_pipeline_system(specs=self.specs, tasks=self.tasks)

    @property
    def task_dict(self) -> List[Dict[str, Any]]:
        return [task.dict(exclude={"func"}) for task in self.tasks]

    @property
    def is_proxy(self) -> bool:
        if self.specs.is_proxy and settings.request_client is not None:
            return True
        return False

    def _set_pipeline_helpers(self, requirements: Optional[str]) -> PipelineHelpers:
        """
        Sets up needed classes for building pieces of the pipeline

        Args:
            requirements:
                Name of requirements file

        Returns:
            `PipelineHelpers`

        """
        packager = PipelinePackager(specs=self.specs)

        # writer is used for decorator-style pipelines
        pipe_meta = PipelineWriterMetadata(
            run_id=self.specs.pipeline_metadata.run_id,
            project=self.specs.project_name,
            pipeline_tasks=self.tasks,
            specs=self.specs,
        )

        writer = PipelineWriter(pipeline_metadata=pipe_meta)

        return PipelineHelpers(writer=writer, packager=packager)

    def generate_pipeline_code(self) -> Optional[str]:
        """
        If creating a pipeline through the decorator style, this method
        will auto-generate the pipeline template for you.
        """

        if self.is_decorated:
            return self._helpers.writer.write_pipeline()
        return None

    def _submit_pipeline_job_to_api(self):
        response = settings.request_client.post_request(
            route=ApiRoutes.SUBMIT_PIPELINE,
            json={
                "specs": self.specs.dict(),
                "tasks": self.task_dict,
            },
        )

        logger.info(response.json().get("response"))

    def _build_and_run(self, schedule: bool):
        if self.is_proxy and self.specs.pipeline_system != PipelineSystem.LOCAL:
            return self._submit_pipeline_job_to_api()

        self._pipeline.build()
        self._pipeline.run()

        # schedule
        if schedule:
            self._pipeline.schedule()
        return self._pipeline.delete_files()

    def run(self, schedule: bool = False) -> None:
        """
        Will run the machine learning pipeline.

        Args:
            schedule:
                Required. Whether to schedule a pipeline. If True, the cron will be extracted from the
                pipeline_config.yaml file (low-level) or PipelineSpec (low-level).
                local (bool): Whether to run the pipeline locally

        Returns:
            `PipelineJob`
        """

        stdout_msg("Building pipeline")

        self._helpers.packager.package_code(writer=self._helpers.writer)
        self._build_and_run(schedule=schedule)
