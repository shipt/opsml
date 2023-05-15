"""Module for importing custom ops"""

from opsml.pipelines.types import PipelineSystem


def get_op_builder(pipeline_system: PipelineSystem):
    if pipeline_system == PipelineSystem.VERTEX:
        from opsml.pipelines.container_op.kubeflow_container import VertexOpBuilder

        return VertexOpBuilder
    from opsml.pipelines.container_op.kubeflow_container import KubeflowOpBuilder

    return KubeflowOpBuilder
