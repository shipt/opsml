import os
from opsml.pipelines import PipelineRunner
from unittest.mock import patch


def test_pipeline_runner_vertex(mock_gcp_vars, mock_gcp_pipeline):
    """Runs local test on pipeline that is already built to run on vertex"""

    from opsml.pipelines.systems.vertex import VertexPipeline

    class MockVertexPipeline(VertexPipeline):
        @property
        def gcp_project(self) -> str:
            return mock_gcp_vars["gcp_project"]

        @property
        def gcp_region(self) -> str:
            return "us-central1"

        @property
        def credentials(self):
            return mock_gcp_vars["gcp_creds"]

        @property
        def storage_uri(self) -> str:
            return "gs://test"

    os.environ["TEST_ENV_VAR"] = "test"
    runner = PipelineRunner(spec_filename="vertex-example-spec.yaml")
    runner.specs.is_proxy = False
    runner._pipeline = MockVertexPipeline(
        specs=runner.specs,
        tasks=runner.tasks,
    )

    assert len(runner.tasks) == 2

    runner.run()
