# pylint: disable=no-self-argument
"""Module for pipeline data models"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field, validator

from opsml.helpers import exceptions
from opsml.helpers.logging import ArtifactLogger

logger = ArtifactLogger.get_logger(__name__)


class CustomTrainingOp(Protocol):
    ...


logger = ArtifactLogger.get_logger(__name__)


class PipelineSystem(str, Enum):
    VERTEX = "vertex"
    LOCAL = "local"
    KUBEFLOW = "kubeflow"


INCLUDE_ARGS = {
    "project_name",
    "cron",
    "owner",
    "additional_dir",
    "team",
    "pipeline_system",
    "user_email",
    "pipeline",
    "pipeline_metadata",
    "container_registry",
}


@dataclass
class RequirementPath:
    req_path: str
    toml_path: str


@dataclass
class CodeInfo:
    """
    Code info associated with a pipeline.
    Code_uri is the storage location of the code.
    Source_dir is the source directory for the pipeline.
    """

    code_uri: str
    source_dir: str


class VertexGPUs(str, Enum):
    NVIDIA_TESLA_A100 = "NVIDIA_TESLA_A100"
    NVIDIA_TESLA_K80 = "NVIDIA_TESLA_K80"
    NVIDIA_TESLA_P4 = "NVIDIA_TESLA_P4"
    NVIDIA_TESLA_P100 = "NVIDIA_TESLA_P100"
    NVIDIA_TESLA_T4 = "NVIDIA_TESLA_T4"
    NVIDIA_TESLA_V100 = "NVIDIA_TESLA_V100"


@dataclass
class MachineType:
    memory: Optional[int] = None
    cpu: Optional[int] = None
    machine_type: Optional[str] = None


class Task(BaseModel):
    """Model the contains expected parameters for a pipeline task"""

    entry_point: str = Field(..., description="Entry point for pipeline task")
    name: str = Field(..., description="Task name")
    flavor: Optional[str] = Field(None, description="Environment to run task in")
    number_instances: int = Field(1, description="Number of compute vms to allocate for the specified task")
    memory: int = Field(16, description="Memory to assign to compute resource")
    cpu: int = Field(2, description="CPU to assign to compute resource")

    gpu_count: Optional[int] = Field(None, description="Number of gpus to use")
    gpu_type: Optional[str] = Field(None, description="Type of gpu to use")
    custom_image: Optional[str] = Field(None, description="Custom docker image to use if specified")
    machine_type: Optional[str] = Field(
        None, description="Optional compute resource name (e.g. vertex would use n1-standard-4). Overrides cpu/memory"
    )

    retry: int = Field(0, description="Number of retries in case of task failure")
    decorated: bool = Field(False, description="Whether task refers to decorated function")
    upstream_tasks: List[Optional[str]] = Field([], description="List of upstream tasks")
    func: Optional[Callable[[Any], Any]] = Field(None, description="Decorated function")

    class Config:
        allow_mutation = True

    @validator("upstream_tasks", allow_reuse=True, pre=True)
    def set_upstream_tasks(cls, upstream_tasks):
        """
        Sets upstream and downstream tasks for pipelines

        Args:
            downstream_task:
                Name of downstream task
            upstream_tasks:
                List of upstream tasks

        """

        tasks = []
        if bool(upstream_tasks):
            for upstream_task in upstream_tasks:
                if isinstance(upstream_task, Task):
                    upstream_name = upstream_task.name
                else:
                    upstream_name = upstream_task
                tasks.append(upstream_name)
        return tasks

    @validator("entry_point", allow_reuse=True)
    def entry_point_valid(cls, entry_point, values):
        """entry_point validator"""

        if entry_point is None:
            raise exceptions.MissingKwarg(
                f"""No entry point was provided for {values["name"]}. Please check trip_runner.py
                """
            )
        return entry_point

    @validator("gpu_type", allow_reuse=True)
    def gpu_type_valid(cls, gpu_type, values):
        """gpu_type validator"""

        if gpu_type is not None:
            try:
                VertexGPUs(gpu_type)
            except ValueError as error:
                raise exceptions.InvalidComputeResource(
                    f"""Specified gpu type is not supported in vertex pipelines (task: {values["name"]}).
                    Supported gpu types include {[gpu.value for gpu in VertexGPUs]}.
                    {error}"""  # noqa
                )

            # check gpu count based on type
            if values.get("gpu_count") is None:
                logger.warning(
                    """No gpu count specified for %s although gpu_type was set. Defaulting to 1.""",
                    values["name"],  # noqa
                )
                values["gpu_count"] = 1

        return gpu_type

    @validator("flavor", allow_reuse=True)
    def flavor_custom_image_assigned(cls, flavor, values):
        """Checks flavor and custom image"""

        if not any(bool(arg) for arg in [flavor, values.get("custom_image")]):
            raise ValueError("Either flavor or custom image must be specified for a task")

        return flavor

    @validator("func", allow_reuse=True)
    def check_decorated(cls, func, values):
        """Checks if func is assigned"""

        if func is not None:
            values["decorated"] = True
        return func


class PipelinePlan(BaseModel):
    tasks: List[Callable[..., Any]]
    resources: Dict[str, Task]


@dataclass
class PipelineJob:
    """Pipeline job model

    Args:
        job:
            PipelineJob
        code_info:
            `CodeInfo` associated with pipeline job

    """

    job: Any
    code_info: CodeInfo


class MachineSpec(BaseModel):
    """Model for creating kubeflow machine spec"""

    machine_type: MachineType
    accelerator_type: Optional[str]
    accelerator_count: Optional[int]
    node_selector_constraint: str = "cloud.google.com/gke-accelerator"
    request_gpu: bool = False

    class Config:
        arbitrary_types_allowed = True

    @validator("request_gpu", allow_reuse=True)
    def set_gpu_flg(cls, request_gpu, values):  # pylint: disable=no-self-argument
        if bool(values["accelerator_type"]):
            return True
        return request_gpu

    @validator("accelerator_count", allow_reuse=True)
    def set_gpu_count(cls, accelerator_count, values):  # pylint: disable=no-self-argument
        if bool(values["accelerator_type"]):
            if not bool(accelerator_count):
                return 1
        return accelerator_count


@dataclass
class ContainerOpInputs:
    name: str
    code_uri: str
    source_dir: str
    entry_point: str
    pipelinecard_uid: str
    image: str
    machine_spec: MachineSpec
    retry: Optional[int] = None


@dataclass
class PathInfo:
    filepath: Optional[str]
    dir_name: Optional[str]


class PipelinePlanner(Protocol):
    ...


class PipelineWriter(Protocol):
    ...
