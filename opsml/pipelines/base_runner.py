from typing import List, Optional, Callable, Any, Union
from opsml.pipelines.types import Task
from opsml.pipelines.spec import PipelineSpecCreator, PipelineSpec
from opsml.helpers.logging import ArtifactLogger


logger = ArtifactLogger.get_logger(__name__)


class PipelineRunnerBase:
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

        self.tasks: List[Task] = []  # list of Tasks
        self.relationships = {}  # dictionary of child (key) parent(list values)
        self.specs = PipelineSpecCreator(
            spec_filename=spec_filename,
            spec=pipeline_spec,
        ).specs

        # for declarative pipelines in spec
        if self.specs.pipeline is not None:
            self._extract_tasks()

        self.requirements = requirements

    @property
    def is_decorated(self) -> bool:
        return any(task.decorated for task in self.tasks)

    def _extract_tasks(self):
        for name, kwargs in self.specs.pipeline.tasks.items():
            self.add_task(name=name, **kwargs)

    def _set_upstream_task(self, current_task: str, upstream_tasks: List[Union[Task, str]]) -> None:
        """
        Sets upstream and downstream tasks for pipelines

        Args:
            downstream_task:
                Name of downstream task
            upstream_tasks:
                List of upstream tasks

        """

        for upstream_task in upstream_tasks:
            if isinstance(upstream_task, Task):
                upstream_name = upstream_task.name
            else:
                upstream_name = upstream_task

            if self.relationships.get(current_task) is not None:
                self.relationships[current_task].append(upstream_name)
            else:
                self.relationships[current_task] = [upstream_name]

    def add_task(
        self,
        name: str,
        entry_point: str,
        number_instances: int = 1,
        memory: int = 16,
        cpu: int = 2,
        retry: int = 0,
        gpu_count: int = 0,
        flavor: Optional[str] = None,
        gpu_type: Optional[str] = None,
        custom_image: Optional[str] = None,
        machine_type: Optional[str] = None,
        upstream_tasks: Optional[List[Union[Task, str]]] = None,
        func: Optional[Callable[[Any], Any]] = None,
    ) -> Task:
        """
        Adds a task to the current pipeline.

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
                Optional name specification for compute (e.g. vertex would use n1-standard-4).
                This will override cpu and memory arguments
            upstream_tasks:
                Optional list of upstream tasks that this task depends on.
            func:
                Argument is only used with decorator-based tasks
        """

        task = Task.parse_obj(locals())

        if bool(upstream_tasks):
            self._set_upstream_task(
                current_task=name,
                upstream_tasks=upstream_tasks,
            )

        self.tasks.append(task)

        return task

    def ml_task(
        self,
        memory: int = 16,
        cpu: int = 2,
        number_instances: int = 1,
        flavor: Optional[str] = None,
        gpu_type: Optional[str] = None,
        gpu_count: Optional[int] = None,
        custom_image: Optional[str] = None,
        machine_type: Optional[str] = None,
        upstream_tasks: Optional[List[Task]] = None,
    ) -> None:
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
                Optional name specification for compute (e.g. vertex would use n1-standard-4).
                This will override cpu and memory arguments
            upstream_tasks:
                Optional list of upstream tasks that this task depends on.
        """

        def task(func) -> None:
            """Decorator for func"""

            self.add_task(
                name=func.__name__,
                entry_point=f"{func.__name__}.py",
                flavor=flavor,
                memory=memory,
                cpu=cpu,
                number_instances=number_instances,
                gpu_count=gpu_count,
                gpu_type=gpu_type,
                custom_image=custom_image,
                machine_type=machine_type,
                func=func,
                upstream_tasks=upstream_tasks,
            )

        return task
