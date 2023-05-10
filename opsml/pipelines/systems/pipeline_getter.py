from opsml_artifacts.helpers.utils import all_subclasses
from opsml_artifacts.helpers import exceptions
from opsml_artifacts.helpers.logging import ArtifactLogger
from opsml_artifacts.pipelines.systems.base import Pipeline
from opsml_artifacts.pipelines.types import (
    PipelineConfig,
    PipelineSystem,
    PipelineHelpers,
)

logger = ArtifactLogger.get_logger(__name__)


def get_pipeline_system(
    pipeline_system: PipelineSystem,
    pipeline_config: PipelineConfig,
    helpers: PipelineHelpers,
) -> Pipeline:

    pipeline = next(
        (
            pipeline_subclass
            for pipeline_subclass in all_subclasses(Pipeline)
            if pipeline_subclass.validate(
                pipeline_system=pipeline_system,
                is_proxy=pipeline_config.params.is_proxy,
            )
        ),
    )

    if pipeline is None:
        raise exceptions.PipelineSystemNotFound

    return pipeline(
        config=pipeline_config,
        helpers=helpers,
    )
