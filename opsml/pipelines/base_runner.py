from functools import wraps
from typing import Any, Callable, List, Optional
from opsml.helpers.logging import ArtifactLogger

from opsml.pipelines.types import CodeInfo, MachineType, TaskArgs
from opsml.pipelines.spec import PipelineSpec

logger = ArtifactLogger.get_logger(__name__)


class BaseRunner:
    def __init__(
        self,
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
        self.spec = spec
        self.requirements = requirements

    def add_task(self):
        ...

    def ml_task(
        self,
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
                machine_meta = MachineType(
                    memory=memory,
                    cpu=cpu,
                    machine_type=machine_type,
                )
                task_args = TaskArgs(
                    machine_type=machine_meta,
                    flavor=flavor,
                    number_vms=number_vms,
                    gpu_count=gpu_count,
                    gpu_type=gpu_type,
                    custom_image=custom_image,
                    entry_point=f"{func.__name__}.py",
                    name=func.__name__,
                )
                return task_args, func

            return wrapper

        return task

    def sql_task(self):
        ...
