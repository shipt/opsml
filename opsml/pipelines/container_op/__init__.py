"""Module for importing custom ops"""

from opsml_artifacts.helpers.types import PipelineSystem


def get_op_builder(pipeline_system: PipelineSystem):
    if pipeline_system == PipelineSystem.VERTEX:
        from opsml_artifacts.pipelines.container_op.kubeflow_container import VertexOpBuilder

        return VertexOpBuilder
    from opsml_artifacts.pipelines.container_op.kubeflow_container import KubeflowOpBuilder

    return KubeflowOpBuilder
