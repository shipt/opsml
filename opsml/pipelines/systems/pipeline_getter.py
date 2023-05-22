from typing import List, Type, cast

from opsml.helpers import exceptions
from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import all_subclasses
from opsml.pipelines.spec import PipelineBaseSpecHolder
from opsml.pipelines.systems import Pipeline
from opsml.pipelines.types import Task

logger = ArtifactLogger.get_logger(__name__)


def get_pipeline_system(specs: PipelineBaseSpecHolder, tasks: List[Task]) -> Pipeline:
    pipeline_system = next(
        (
            pipeline_subclass
            for pipeline_subclass in all_subclasses(Pipeline)
            if pipeline_subclass.validate(
                pipeline_system=specs.pipeline_system,
                is_proxy=specs.is_proxy,
            )
        ),
    )
    if pipeline_system is None:
        raise exceptions.PipelineSystemNotFound

    return cast(Pipeline, pipeline_system(specs=specs, tasks=tasks))
