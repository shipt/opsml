from typing import Dict, List, Any, Optional

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems.base import Pipeline
from opsml.pipelines.utils import stdout_msg
from opsml.registry.sql.settings import settings
from opsml.pipelines.types import (
    PipelineJob,
    PipelineSystem,
    CustomTrainingOp,
    PipelineParams,
)

logger = ArtifactLogger.get_logger(__name__)


class KubeFlowServerPipeline(Pipeline):
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

    @staticmethod
    def run(pipeline_job: PipelineJob) -> None:
        """
        Runs a Kubeflow pipeline

        Args:
            pipeline_job:
                Kubeflow pipeline job

        """
        from kfp import Client

        params: PipelineParams = pipeline_job.job
        client = Client(host=settings.pipeline_host_uri)
        client.create_run_from_pipeline_package(
            pipeline_file=params.pipe_filepath,
            run_name=params.pipe_project_name,
            pipeline_root=params.pipe_storage_root,
            enable_caching=params.cache,
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
            custom_tasks = self._set_dependencies(
                task_name=task.name,
                upstream_tasks=task.upstream_tasks,
                custom_tasks=custom_tasks,
            )

        return custom_tasks

    def _build_tasks(self) -> Dict[str, Any]:
        custom_tasks = self._build_task_spec()

        print(custom_tasks)
        a
        return self._set_task_dependencies(custom_tasks=custom_tasks)

    def build(self) -> None:
        """
        Builds a Vertex Pipeline

        Args:
            pipeline_config:
                Pipeline configuration pydantic model

        Returns:
            Vertex pipeline job
        """

        from kfp.v2 import compiler, dsl

        code_info = self.package_code()

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

        # need to return params because they're used in the 'run' staticmethod
        return PipelineJob(job=self.specs, code_info=code_info)

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
            "Scheduling is not currently supported for kubeflow pipelines %s",
            pipeline_job.code_info.dict(),
        )

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        return pipeline_system == PipelineSystem.KUBEFLOW and is_proxy == False
