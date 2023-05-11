"""Module for PipelineRunner Interface"""

from typing import Any, Callable, List, Optional, cast
from dataclasses import dataclass
from functools import wraps
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


class PipelineRunner:
    def __init__(
        self,
        tasks: List[Callable[..., Any]],
        requirements: Optional[str] = None,
        spec: Optional[PipelineSpec] = None,
    ):
        """
        Interface for building a machine learning pipeline using Vertex and Airflow (eventually).

        Args:
            task_list:
                List of pipeline task funcs defined in pipeline_runner.py.
            requirements:
                Requirement file name. Name values can be "requirements.txt" (or specific *.txt name) or "poetry.lock"
            spec:
                Optional PipelineSpec. This is required for decorator-based training

        """
        # tasks
        self.tasks = Tasks(task_list=tasks)

        # Create params
        self.params = PipelineParamCreator(spec=spec).params
        self.params.decorated = self.tasks

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
        spec = self.params.dict(include=INCLUDE_PARAMS)

        planner = PipelinePlanner(params=self.params, tasks=self.tasks)
        packager = PipelinePackager(config=spec, requirements_file=requirements)

        pipe_meta = PipelineWriterMetadata(
            run_id=self.params.run_id,
            project=self.params.project_name,
            pipeline_resources=planner.pipeline_plan.resources,
            pipeline_tasks=planner.pipeline_plan.tasks,
            config=spec,
        )

        writer = PipelineWriter(
            pipeline_metadata=pipe_meta,
            additional_dir=cast(str, self.params.additional_dir),
            runner_filename=self.params.source_file,
        )

        return PipelineHelpers(
            planner=planner,
            writer=writer,
            packager=packager,
        )

    def visualize_pipeline(
        self,
        save_diagram: bool = False,
        filename: Optional[str] = None,
        file_format: Optional[str] = None,
    ) -> None:
        """
        Visualizes the current pipeline,

        ***WARNING***

        This method relies on graphviz. You must have the proper graphviz bindings installed
        in order to visualize the image.

        See:
            https://formulae.brew.sh/formula/graphviz
            https://graphviz.org/download/

        Args:
            save_diagram:
                Whether to save the pipeline diagram or not
            filename:
                Filename to save image to
            file_format:
                Format for saved file. (png, pdf)

        """
        visualizer, func_names = self.helpers.planner.get_visualizer()

        if save_diagram:
            visualizer.graphviz(filter=func_names).render(
                filename=filename,
                format=file_format,
            )

        return visualizer.graphviz(filter=func_names)

    def generate_pipeline_code(self) -> Optional[str]:
        """
        If creating a pipeline through the decorator style, this method
        will auto-generate the pipeline template for you.
        """

        if self.tasks.decorated:
            return self.helpers.writer.write_pipeline()
        return None

    def run(self, schedule: bool = False) -> PipelineJobModel:
        """
        Will run the machine learning pipeline outlined in the
        pipeline_runner.py file or generated from decorated functions.

         Args:
            schedule:
                Required. Whether to schedule a pipeline. If True, the cron will be extracted from the
                pipeline_config.yaml file (low-level) or PipelineSpec (low-level).
                local (bool): Whether to run the pipeline locally
        """

        stdout_msg("Building pipeline")

        pipeline_config = PipelineConfig(
            resources=self.helpers.planner.pipeline_plan.resources,
            params=self.params,
            env_vars=self.params.env_vars,
        )

        # Get pipeline system
        pipeline: Pipeline = get_pipeline_system(
            pipeline_system=self.params.pipeline_system,
            pipeline_config=pipeline_config,
        )

        pipeline_job = pipeline.build()
        pipeline.run(pipeline_job=pipeline_job)

        if schedule:
            pipeline.schedule(pipeline_job=pipeline_job)

        # clean up
        pipeline.delete_files()

        return pipeline_job


# you should be able to add tasks to pipeline runner directly
# no need to create a "task list"


@dataclass
class Task:
    name: str
    entry_point: str
    number_instances: int = 1
    flavor: str
    memory: int = 16
    cpu: int = 2
    retry: int = 0
    custom_image: Optional[str]
    machine_type: Optional[str]


class BaseRunner:
    def __init__(self):
        self.tasks = []

    def add_task(
        self,
        name: str,
        entry_point: str,
        flavor: str,
        number_instances: int = 1,
        memory: int = 16,
        cpu: int = 2,
        retry: int = 0,
        gpu_count: int = 0,
        gpu_type: Optional[str] = None,
        custom_image: Optional[str] = None,
        machine_type: Optional[str] = None,
        upstream_tasks: Optional[List[Tasks]] = None,
        **kwargs,
    ):
        """
        Adds a task to the current pipeline. This is used for non-decorator-based pipeline
        building.

        Args:
            name:
                Name of pipeline task
            entry_point:
                Name of python or sql file to run
            flavor:
                Flavor of pipeline task (e.g. sklearn, snowflake)
            number_instances:
                Number compute instances to use. Defaults to 1
            memory:
                How much memory to attach to each compute resource. Defaults to 16 GB
            cpu:
                How much cpu to allocate for each compute resource. Default to 2
            gpu_count:
                Number of gpus to asign to each compute resource
            gpu_type:
                Type of gpu to use
            retry:
                How many times to retry the task if it fails. Defaults to 0
            custom_image:
                Optional argument for providing a custom docker image. This will override "flavor"
            machine_type:
                Optional argument to name a a compute resource by name (e.g. vertex would use n1-standard-4).
                This will override cpu and memory arguments
            upstream_tasks:
                Optional list of upstream tasks that this task depends on.
        """

        print(**kwargs)

    def ml_task(
        memory: Optional[int] = None,
        cpu: Optional[int] = None,
        flavor: Optional[str] = None,
        number_vms: Optional[int] = 1,
        gpu_type: Optional[str] = None,
        gpu_count: Optional[int] = None,
        custom_image: Optional[str] = None,
        machine_type: Optional[str] = None,
    ):
        """
        Decorator for building machine learning pipeline asks out of a python function.

        Args:
            memory:
                Amount of memory to request for the task
            cpu:
                Amount of cpu to request for the task
            flavor:
                Docker image type to use
            number_vms:
                Number of vms to use with task (current 1 is supported)
            gpu_type:
                Type of gpu to use
            gpu_count:
                Number of gpus to assign to task
            custom_image:
                Custom docker image to use if not using any "flavor"
            machine_type:
        """

        def task(func):
            """Decorator for func"""

            @wraps(func)
            def wrapper(*args, **kwargs):
                task_args = Task(
                    name=func.__name__,
                    entry_point=f"{func.__name__}.py",
                    flavor=flavor,
                    memory=memory,
                    cpu=cpu,
                    number_vms=number_vms,
                    gpu_count=gpu_count,
                    gpu_type=gpu_type,
                    custom_image=custom_image,
                    machine_type=machine_type,
                )

                return task_args, func

            return wrapper

        return task

    def sql_task(self):
        ...


class PipelineRunner:
    def __init__(
        self,
        tasks: List[Callable[..., Any]],
        requirements: Optional[str] = None,
        spec: Optional[PipelineSpec] = None,
    ):
        """
        Interface for building a machine learning pipeline using Vertex and Airflow (eventually).

        Args:
            task_list:
                List of pipeline task funcs defined in pipeline_runner.py.
            requirements:
                Requirement file name. Name values can be "requirements.txt" (or specific *.txt name) or "poetry.lock"
            spec:
                Optional PipelineSpec. This is required for decorator-based training

        """
        # tasks
        self.tasks = Tasks(task_list=tasks)
