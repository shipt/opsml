from typing import List

from opsml.helpers.utils import all_subclasses
from opsml.helpers import exceptions
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems import Pipeline

logger = ArtifactLogger.get_logger(__name__)


def get_pipeline_system(is_proxy: bool, pipeline_system: str) -> Pipeline:
    pipeline = next(
        (
            pipeline_subclass
            for pipeline_subclass in all_subclasses(Pipeline)
            if pipeline_subclass.validate(
                pipeline_system=pipeline_system,
                is_proxy=is_proxy,
            )
        ),
    )

    if pipeline is None:
        raise exceptions.PipelineSystemNotFound

    return pipeline
