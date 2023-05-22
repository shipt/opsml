# pylint: disable=import-outside-toplevel
"""Module for importing custom ops"""

from opsml.pipelines.types import PipelineSystem


def get_op_builder(pipeline_system: str):
    if pipeline_system == PipelineSystem.VERTEX:
        from opsml.pipelines.container_op.op_builder import VertexOpBuilder

        return VertexOpBuilder
    from opsml.pipelines.container_op.op_builder import KubeflowOpBuilder

    return KubeflowOpBuilder
