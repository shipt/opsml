from opsml.helpers.utils import all_subclasses
from opsml.helpers import exceptions
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems import Pipeline
from opsml.pipelines.spec import PipelineBaseSpecs
from opsml.pipelines.types import PipelineHelpers

logger = ArtifactLogger.get_logger(__name__)


def get_pipeline_system(
    specs: PipelineBaseSpecs,
    helpers: PipelineHelpers,
) -> Pipeline:

    pipeline = next(
        (
            pipeline_subclass
            for pipeline_subclass in all_subclasses(Pipeline)
            if pipeline_subclass.validate(
                pipeline_system=specs.pipeline_system,
                is_proxy=specs.is_proxy,
            )
        ),
    )

    if pipeline is None:
        raise exceptions.PipelineSystemNotFound

    return pipeline(
        specs=specs,
        helpers=helpers,
    )
