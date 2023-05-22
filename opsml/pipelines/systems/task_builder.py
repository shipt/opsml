"""Code for building Tasks and Pipelines"""

from typing import Any, Dict, List, Optional

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.container_op import get_op_builder
from opsml.pipelines.spec import PipelineBaseSpecHolder, VertexSpecHolder
from opsml.pipelines.systems.images import ContainerImageRegistry
from opsml.pipelines.types import (
    ContainerOpInputs,
    MachineSpec,
    MachineType,
    PipelineSystem,
    Task,
)

logger = ArtifactLogger.get_logger(__name__)


class TaskBuilder:
    def __init__(
        self,
        specs: PipelineBaseSpecHolder,
        pipeline_system: PipelineSystem,
    ):
        """
        Base builder class

        Args:
            params:
                Pipeline params class
            pipeline_system:
                Pipeline system
        """
        self.image_client = ContainerImageRegistry(container_registry=specs.container_registry)
        self.op_builder = get_op_builder(pipeline_system=pipeline_system)

    def get_task_image(self, task_args: Task) -> str:
        if task_args.custom_image is None:
            return self.image_client.get_image_uri(str(task_args.flavor))
        return task_args.custom_image

    def set_machine_type(
        self,
        machine_type: MachineType,
        gpu_type: Optional[str] = None,
        gpu_count: Optional[int] = None,
    ) -> MachineSpec:
        return MachineSpec(
            machine_type=machine_type,
            accelerator_count=gpu_count,
            accelerator_type=gpu_type,
        )

    def get_op_inputs(
        self,
        specs: PipelineBaseSpecHolder,
        entry_point: str,
        name: str,
        image: str,
        machine_spec: MachineSpec,
        retry: Optional[int] = None,
    ) -> ContainerOpInputs:
        """
        Sets the input args for building the container op for a given task

        Args:
            specs:
                Pipeline specification
            entry_point:
                Entry point for task
            name:
                Name of task
            image:
                Image uri
            machine_spec:
                Machine specification for the current task
            retry:
                Number of retries for the current task


        Returns:
            `ContainerOpInputs`
        """
        return ContainerOpInputs(
            name=name,
            code_uri=str(specs.code_uri),
            source_dir=str(specs.source_dir),
            pipelinecard_uid=str(specs.pipelinecard_uid),
            entry_point=str(entry_point),
            image=image,
            machine_spec=machine_spec,
            retry=retry,
        )

    def build(
        self,
        task_args: Task,
        env_vars: Dict[str, Any],
        specs: PipelineBaseSpecHolder,
    ):
        raise NotImplementedError

    @staticmethod
    def validate(pipeline_system: PipelineSystem) -> bool:
        raise NotImplementedError


# pass everything
class LocalTaskBuilder(TaskBuilder):
    def build(
        self,
        task_args: Task,
        env_vars: Dict[str, Any],
        specs: PipelineBaseSpecHolder,
    ):
        pass

    @staticmethod
    def validate(pipeline_system: PipelineSystem) -> bool:
        return pipeline_system == PipelineSystem.LOCAL


class VertexTaskBuilder(TaskBuilder):
    def set_env_vars(self, env_vars: Dict[str, Any]) -> List[Dict[str, str]]:
        env_vars_list: List[Dict[str, str]] = []
        for key, value in env_vars.items():
            env_vars_list.append({"name": key.upper(), "value": str(value)})
        return env_vars_list

    def build(
        self,
        task_args: Task,
        env_vars: Dict[str, Any],
        specs: VertexSpecHolder,
    ) -> Any:
        """Builds a Vertex task
        Args:
            Task_args (Task): Pydantic model of task args
            env_vars (Params): Pydantic model of pipeline params
        Returns:
            Vertex custom training job
        """

        image_uri = self.get_task_image(task_args=task_args)

        machine_spec = self.set_machine_type(
            machine_type=MachineType(
                memory=task_args.memory,
                cpu=task_args.cpu,
                machine_type=task_args.machine_type,
            ),
            gpu_count=task_args.gpu_count,
            gpu_type=task_args.gpu_type,
        )
        env_vars_list = self.set_env_vars(env_vars=env_vars)

        op_inputs = self.get_op_inputs(
            specs=specs,
            entry_point=task_args.entry_point,
            name=task_args.name,
            image=image_uri,
            machine_spec=machine_spec,
            retry=task_args.retry,
        )

        op_builder = self.op_builder(
            op_inputs=op_inputs,
            network=specs.network,
            reserved_ip_ranges=specs.reserved_ip_ranges,
            service_account=specs.service_account,
            gcp_project_id=specs.gcp_project,
            env_vars=env_vars_list,
        )

        return op_builder.buil_op()

    @staticmethod
    def validate(pipeline_system: PipelineSystem) -> bool:
        return pipeline_system == PipelineSystem.VERTEX


class KubeflowTaskBuilder(TaskBuilder):
    """Builds custom container ops that is compatible with Vertex and KubeFlow"""

    def set_machine_type(
        self,
        machine_type: MachineType,
        gpu_type: Optional[str] = None,
        gpu_count: Optional[int] = None,
    ) -> MachineSpec:
        return MachineSpec(
            machine_type=machine_type,
            accelerator_count=gpu_count,
            accelerator_type=gpu_type,
        )

    def set_env_vars(self, env_vars: Dict[str, Any]) -> List[Any]:
        from kubernetes.client.models import V1EnvVar

        env_vars_list: List[V1EnvVar] = []

        for key, value in env_vars.items():
            env_vars_list.append(V1EnvVar(name=key.upper(), value=str(value)))

        return env_vars_list

    def get_task_image(self, task_args: Task) -> str:
        if task_args.custom_image is None:
            return self.image_client.get_image_uri(str(task_args.flavor))
        return task_args.custom_image

    def build(
        self,
        task_args: Task,
        env_vars: Dict[str, Any],
        specs: PipelineBaseSpecHolder,
    ) -> Any:
        """Builds a KubeFlow task

        Args:
            Task_args (Task): Pydantic model of task args
            env_vars (Dict): Dictionary of environment vars (name, value pairs)
            params (PipelineParams): Pydantic model of pipeline params

        Returns:
            KubeFlow custom training job

        """

        # set job vars
        image_uri = self.get_task_image(task_args=task_args)

        machine_spec = self.set_machine_type(
            machine_type=MachineType(
                memory=task_args.memory,
                cpu=task_args.cpu,
                machine_type=task_args.machine_type,
            ),
            gpu_count=task_args.gpu_count,
            gpu_type=task_args.gpu_type,
        )

        container_env_vars = self.set_env_vars(env_vars=env_vars)

        op_inputs = self.get_op_inputs(
            specs=specs,
            entry_point=task_args.entry_point,
            name=task_args.name,
            image=image_uri,
            machine_spec=machine_spec,
            retry=task_args.retry,
        )

        custom_job_task = self.op_builder(
            op_inputs=op_inputs,
            env_vars=container_env_vars,
        )

        return custom_job_task.build_task()

    @staticmethod
    def validate(pipeline_system: PipelineSystem) -> bool:
        return pipeline_system == PipelineSystem.KUBEFLOW


def get_task_builder(
    specs: PipelineBaseSpecHolder,
    pipeline_system: PipelineSystem,
) -> TaskBuilder:
    """
    Gets task builder based on provided pipeline system

    Args:
        pipeline_system:
            Pipeline system to use

    Return
        TaskBuilder
    """

    task_builder = next(
        builder
        for builder in TaskBuilder.__subclasses__()
        if builder.validate(
            pipeline_system=pipeline_system,
        )
    )

    return task_builder(
        specs=specs,
        pipeline_system=pipeline_system,
    )
