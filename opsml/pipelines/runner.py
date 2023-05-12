"""Module for PipelineRunner Interface"""

from typing import Any, Callable, List, Optional, cast
from dataclasses import dataclass
from opsml.pipelines.base_runner import PipelineRunnerBase
from opsml.pipelines.utils import stdout_msg
from opsml.pipelines.package import PipelinePackager
from opsml.pipelines.types import (
    PipelineWriterMetadata,
    PipelineConfig,
    PipelineJobModel,
    PipelineHelpers,
)
from opsml.pipelines.systems.pipeline_getter import get_pipeline_system, Pipeline
from opsml.pipelines.planner import PipelinePlanner
from opsml.pipelines.spec import PipelineSpec, PipelineParamCreator
from opsml.pipelines.types import (
    Tasks,
    INCLUDE_PARAMS,
)
from opsml.pipelines.writer import PipelineWriter


@dataclass
class PipelineHelpers:
    """
    Pipeline helper class
    """

    planner: PipelinePlanner
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
        self.helpers = self._set_pipeline_helpers(requirements=requirements)

    def _set_pipeline_helpers(self, requirements: Optional[str]) -> PipelineHelpers:
        """
        Sets up needed classes for building pieces of the pipeline

        Args:
            requirements:
                Name of requirements file

        Returns:
            `PipelineHelpers`

        """
        specs = self.specs.dict(include=INCLUDE_PARAMS)

        # planner = PipelinePlanner(specs=self.specs, tasks=self.tasks)
        packager = PipelinePackager(specs=specs, requirements_file=requirements)

        pipe_meta = PipelineWriterMetadata(
            run_id=self.specs.run_id,
            project=self.specs.project_name,
            pipeline_tasks=self.tasks,
            config=specs,
        )

        writer = PipelineWriter(
            pipeline_metadata=pipe_meta,
            additional_dir=cast(str, self.specs.additional_dir),
            runner_filename=self.specs.source_file,
        )

        return PipelineHelpers(writer=writer, packager=packager)

    def generate_pipeline_code(self) -> Optional[str]:
        """
        If creating a pipeline through the decorator style, this method
        will auto-generate the pipeline template for you.
        """

        if self.is_decorated:
            return self.helpers.writer.write_pipeline()
        return None


# class _PipelineRunner:
#    def __init__(
#        self,
#        tasks: List[Callable[..., Any]],
#        requirements: Optional[str] = None,
#        spec: Optional[PipelineSpec] = None,
#    ):
#        """
#        Interface for building a machine learning pipeline using Vertex and Airflow (eventually).
#
#        Args:
#            task_list:
#                List of pipeline task funcs defined in pipeline_runner.py.
#            requirements:
#                Requirement file name. Name values can be "requirements.txt" (or specific *.txt name) or "poetry.lock"
#            spec:
#                Optional PipelineSpec. This is required for decorator-based training
#
#        """
#        # tasks
#        self.tasks = Tasks(task_list=tasks)
#
#        # Create params
#        self.params = PipelineParamCreator(spec=spec).params
#        self.params.decorated = self.tasks
#
#        # gather helpers
#        self.helpers = self._set_pipeline_helpers(requirements=requirements)
#
#    def _set_pipeline_helpers(self, requirements: Optional[str]) -> PipelineHelpers:
#        """
#        Sets up needed classes for building pieces of the pipeline
#
#        Args:
#            requirements:
#                Name of requirements file
#
#        Returns:
#            `PipelineHelpers`
#
#        """
#        spec = self.params.dict(include=INCLUDE_PARAMS)
#
#        planner = PipelinePlanner(params=self.params, tasks=self.tasks)
#        packager = PipelinePackager(config=spec, requirements_file=requirements)
#
#        pipe_meta = PipelineWriterMetadata(
#            run_id=self.params.run_id,
#            project=self.params.project_name,
#            pipeline_resources=planner.pipeline_plan.resources,
#            pipeline_tasks=planner.pipeline_plan.tasks,
#            config=spec,
#        )
#
#        writer = PipelineWriter(
#            pipeline_metadata=pipe_meta,
#            additional_dir=cast(str, self.params.additional_dir),
#            runner_filename=self.params.source_file,
#        )
#
#        return PipelineHelpers(
#            planner=planner,
#            writer=writer,
#            packager=packager,
#        )
#
#    def visualize_pipeline(
#        self,
#        save_diagram: bool = False,
#        filename: Optional[str] = None,
#        file_format: Optional[str] = None,
#    ) -> None:
#        """
#        Visualizes the current pipeline,
#
#        ***WARNING***
#
#        This method relies on graphviz. You must have the proper graphviz bindings installed
#        in order to visualize the image.
#
#        See:
#            https://formulae.brew.sh/formula/graphviz
#            https://graphviz.org/download/
#
#        Args:
#            save_diagram:
#                Whether to save the pipeline diagram or not
#            filename:
#                Filename to save image to
#            file_format:
#                Format for saved file. (png, pdf)
#
#        """
#        visualizer, func_names = self.helpers.planner.get_visualizer()
#
#        if save_diagram:
#            visualizer.graphviz(filter=func_names).render(
#                filename=filename,
#                format=file_format,
#            )
#
#        return visualizer.graphviz(filter=func_names)
#
#    def generate_pipeline_code(self) -> Optional[str]:
#        """
#        If creating a pipeline through the decorator style, this method
#        will auto-generate the pipeline template for you.
#        """
#
#        if self.tasks.decorated:
#            return self.helpers.writer.write_pipeline()
#        return None
#
#    def run(self, schedule: bool = False) -> PipelineJobModel:
#        """
#        Will run the machine learning pipeline outlined in the
#        pipeline_runner.py file or generated from decorated functions.
#
#         Args:
#            schedule:
#                Required. Whether to schedule a pipeline. If True, the cron will be extracted from the
#                pipeline_config.yaml file (low-level) or PipelineSpec (low-level).
#                local (bool): Whether to run the pipeline locally
#        """
#
#        stdout_msg("Building pipeline")
#
#        pipeline_config = PipelineConfig(
#            resources=self.helpers.planner.pipeline_plan.resources,
#            params=self.params,
#            env_vars=self.params.env_vars,
#        )
#
#        # Get pipeline system
#        pipeline: Pipeline = get_pipeline_system(
#            pipeline_system=self.params.pipeline_system,
#            pipeline_config=pipeline_config,
#        )
#
#        pipeline_job = pipeline.build()
#        pipeline.run(pipeline_job=pipeline_job)
#
#        if schedule:
#            pipeline.schedule(pipeline_job=pipeline_job)
#
#        # clean up
#        pipeline.delete_files()
#
#        return pipeline_job
#
#
## you should be able to add tasks to pipeline runner directly
## no need to create a "task list"
#
#
# class PipelineRunner:
#    def __init__(
#        self,
#        tasks: List[Callable[..., Any]],
#        requirements: Optional[str] = None,
#        spec: Optional[PipelineSpec] = None,
#    ):
#        """
#        Interface for building a machine learning pipeline using Vertex and Airflow (eventually).
#
#        Args:
#            task_list:
#                List of pipeline task funcs defined in pipeline_runner.py.
#            requirements:
#                Requirement file name. Name values can be "requirements.txt" (or specific *.txt name) or "poetry.lock"
#            spec:
#                Optional PipelineSpec. This is required for decorator-based training
#
#        """
#        # tasks
#        self.tasks = Tasks(task_list=tasks)
#
