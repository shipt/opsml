import os
from typing import Any, Dict, List, Optional, Tuple, Union
import tempfile
from dataclasses import dataclass

try:
    from kfp.v2.components import load_component_from_file
except ImportError:
    from kfp.components import load_component_from_file

import yaml
from kubernetes.client.models import V1EnvVar

from opsml.pipelines.types import MachineSpec, ContainerOpInputs


CUSTOM_OP_PATH = os.path.join(os.path.dirname(__file__), "custom_component.yaml")
VertexTrainingOp = load_component_from_file(os.path.join(os.path.dirname(__file__), "vertex_component.yaml"))


class KubeflowOpBuilder:
    def __init__(
        self,
        op_inputs: ContainerOpInputs,
        env_vars: List[V1EnvVar],
    ):
        self._container_op = self.load_conainter_op(op_inputs=op_inputs)  # pylint: disable=invalid-name
        self.machine_spec = op_inputs.machine_spec
        self.retry = op_inputs.retry
        self.env_vars = env_vars

    def load_conainter_op(self, op_inputs: ContainerOpInputs) -> Any:  # create type later
        """
        Helper method for loading the base component spec and changing the image.
        Current Kubeflow package does not have a good way to accomplish this through the sdk

        Args:
            op_inputs:
                `ContainerOpInputs`
        Returns:
            `ContainerOp`
        """

        with open(CUSTOM_OP_PATH, encoding="utf8") as op_file:
            data = yaml.safe_load(op_file)
            data["implementation"]["container"]["image"] = op_inputs.image
            data["name"] = op_inputs.name

        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = f"{tmpdirname}/temp_container.yaml"
            with open(file_path, "w", encoding="utf8") as temp_file:
                yaml.dump(data, temp_file)

            container_op = load_component_from_file(file_path)(
                code_uri=op_inputs.code_uri,
                source_dir=op_inputs.source_dir,
                entry_point=op_inputs.entry_point,
                pipelinecard_uid=op_inputs.pipelinecard_uid,
            )

        container_op.display_name = op_inputs.name

        return container_op

    def _set_gpu_config(self):
        gpu_count = int(self.machine_spec.accelerator_count)
        gpu_type = str(self.machine_spec.accelerator_type)

        self._container_op.set_gpu_limit(gpu_count)
        self._container_op.add_node_selector_constraint(
            self.machine_spec.node_selector_constraint,
            gpu_type,
        )

    def _set_machine_config(self):
        self._container_op.set_cpu_limit(str(self.machine_spec.machine_type.cpu))
        self._container_op.set_memory_limit(f"{self.machine_spec.machine_type.memory}G")

        if self.machine_spec.request_gpu:
            self._set_gpu_config()

    def _add_env_vars(self):
        for env_var in self.env_vars:
            self._container_op.add_env_variable(env_var)

    def _no_cache(self):
        self._container_op.execution_options.caching_strategy.max_cache_staleness = "P0D"
        self._container_op.set_caching_options(False)

    def build_op(self):
        self._set_machine_config()
        self._add_env_vars()
        self._no_cache()
        if bool(self.retry):
            self._container_op.set_retry(self.retry)
        return self._container_op


class VertexOpBuilder:
    def __init__(
        self,
        op_inputs: ContainerOpInputs,
        gcp_project_id: str,
        env_vars: List[Dict[str, str]],
        network: Optional[str] = None,
        reserved_ip_ranges: Optional[List[str]] = None,
        service_account: Optional[str] = None,
    ):
        self.machine_spec = self.set_machine_specs(spec=op_inputs.machine_spec)
        command, args = self.create_container_command(op_inputs=op_inputs)

        self.container_spec = self.create_container_spec(
            env_vars=env_vars,
            image=op_inputs.image,
            command=command,
            args=args,
        )

        self.op_inputs = op_inputs
        self.network = network
        self.service_account = service_account
        self.gcp_project_id = gcp_project_id
        self.reserved_ip_ranges = reserved_ip_ranges

    def create_container_command(
        self,
        op_inputs: ContainerOpInputs,
    ) -> Tuple[List[str], List[str]]:
        command = ["sh", "/app/train.sh"]
        args = [
            f"-c {op_inputs.code_uri}",
            f"-s {op_inputs.source_dir}",
            f"-e {op_inputs.entry_point}",
            f"-p {op_inputs.pipelinecard_uid}",
        ]

        return command, args

    def create_container_spec(
        self,
        env_vars: List[Dict[str, str]],
        image: str,
        command: List[str],
        args: List[str],
    ):
        return {
            "env": env_vars,
            "imageUri": image,
            "command": command,
            "args": args,
        }

    def set_machine_specs(self, spec: MachineSpec) -> Dict[str, Union[int, float, str]]:
        machine_spec: Dict[str, Union[int, float, str]] = {}
        machine_spec["machineType"] = str(spec.machine_type.machine_type)
        if bool(spec.accelerator_type):
            machine_spec["acceleratorType"] = str(spec.accelerator_type)
            machine_spec["acceleratorCount"] = int(spec.accelerator_count or 1)

        return machine_spec

    def buil_op(self) -> Any:
        """Builds a custom Vertex training op"""

        custom_op = VertexTrainingOp(
            service_account=self.service_account,
            network=self.network,
            reserved_ip_ranges=self.reserved_ip_ranges,
            project=self.gcp_project_id,
            display_name=self.op_inputs.name,
            worker_pool_specs=[
                {
                    "containerSpec": self.container_spec,
                    "replicaCount": "1",
                    "machineSpec": self.machine_spec,
                }
            ],
        ).set_retry(self.op_inputs.retry)
        custom_op.name = self.op_inputs.name
        a

        return custom_op
