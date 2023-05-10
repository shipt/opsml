"""Module for decorator"""

from functools import wraps
from typing import Optional

from opsml.registry import CardRegistry, PipelineCard
from opsml.helpers.logging import ArtifactLogger

from opsml.pipelines.types import CodeInfo, MachineType, TaskArgs

logger = ArtifactLogger.get_logger(__name__)


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
            Optional name for machine type to use (used with Vertex)
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


def sql_task(filename: str):
    """
    Decorator for running a sql task

    Args:
        filename:
            Name of sql file to run. Must end with ".sql"
    """

    def task(func):
        """Decorator for func"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            machine_type = MachineType()
            task_args = TaskArgs(
                machine_type=machine_type,
                flavor="snowflake",
                number_vms=1,
                entry_point=filename,
                name=func.__name__,
            )

            return task_args, func

        return wrapper

    return task


def create_pipeline_card(func):
    """Decorator for creating PipelineCard and assigning uid to pipeline params"""

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> CodeInfo:
        code_info: CodeInfo = func(self, *args, **kwargs)
        params = kwargs["params"]

        registry: CardRegistry = CardRegistry(registry_name="pipeline")

        pipeline_card = PipelineCard(
            name=params.project_name,
            team=params.team,
            user_email=params.user_email,
            pipeline_code_uri=code_info.code_uri,
        )
        registry.register_card(card=pipeline_card)
        params.pipelinecard_uid = pipeline_card.uid

        return code_info

    return wrapper
