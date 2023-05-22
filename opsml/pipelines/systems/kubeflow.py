# pylint: disable=import-outside-toplevel
from typing import Any, Dict, List, Optional

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems.base import Pipeline
from opsml.pipelines.types import CustomTrainingOp, PipelineSystem
from opsml.pipelines.utils import stdout_msg
from opsml.registry.sql.settings import settings

logger = ArtifactLogger.get_logger(__name__)


class KubeFlowPipeline(Pipeline):
    def _set_dependencies(
        self,
        task_name: str,
        custom_tasks: Dict[str, CustomTrainingOp],
        upstream_tasks: List[Optional[str]],
    ):
        """
        Sets dependencies for a task

        Args:
            task_name:
                Name of task in pipeline
            custom_tasks:
                Dictionary of custom training tasks in the pipeline
            dependencies:
                List of task dependencies

        Returns:
            Modified custom_tasks
        """

        if len(upstream_tasks) > 0:
            for upstream_task in upstream_tasks:
                custom_tasks[task_name].after(  # type: ignore
                    custom_tasks[upstream_task],
                )

        return custom_tasks

    def run(self) -> None:
        """
        Runs a Kubeflow pipeline

        Args:
            pipeline_job:
                Kubeflow pipeline job

        """
        from kfp import Client

        storage_root = self.specs.pipeline_metadata.storage_root
        filename = self.specs.pipeline_metadata.filename

        client = Client(host=settings.pipeline_host_uri)
        client.create_run_from_pipeline_package(
            pipeline_file=f"{storage_root}/{filename}",
            run_name=self.specs.project_name,
            pipeline_root=storage_root,
            enable_caching=self.specs.cache,
        )

        stdout_msg("Pipeline Submitted!")

    def _build_task_spec(self) -> Dict[str, Any]:
        custom_tasks = {}

        for task in self.tasks:
            stdout_msg(f"Building pipeline task: {task.name}")
            custom_tasks[task.name] = self._task_builder.build(
                task_args=task,
                env_vars=self.env_vars,
                specs=self.specs,
            )

        return custom_tasks

    def _set_task_dependencies(self, custom_tasks: Dict[str, Any]) -> Dict[str, Any]:
        # set dependencies
        for task in self.tasks:
            if task.upstream_tasks is not None:
                custom_tasks = self._set_dependencies(
                    task_name=task.name,
                    upstream_tasks=task.upstream_tasks,
                    custom_tasks=custom_tasks,
                )

        return custom_tasks

    def _build_tasks(self) -> Dict[str, Any]:
        custom_tasks = self._build_task_spec()

        return self._set_task_dependencies(custom_tasks=custom_tasks)

    def build(self) -> None:
        """
        Builds Kubeflow/Vertex tasks

        Args:
            pipeline_config:
                Pipeline configuration pydantic model

        Returns:
            Vertex pipeline job
        """

        from kfp.v2 import compiler, dsl

        @dsl.pipeline(
            pipeline_root=self.specs.pipeline_metadata.storage_root,
            name=self.specs.project_name,
        )
        def pipeline():
            self._build_tasks()

        compiler.Compiler().compile(
            pipeline_func=pipeline,
            package_path=self.specs.pipeline_metadata.filename,
        )

    def schedule(self):
        """
        Schedules a pipelines.

        Args:
            pipeline_params:
                Pydantic class of pipeline params
            code_info:
                Pydantic class containing package metadata
        """
        logger.info(
            "Scheduling is not currently supported for kubeflow pipelines %s",
        )

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        return pipeline_system == PipelineSystem.KUBEFLOW
