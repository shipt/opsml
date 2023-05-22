from opsml.pipelines import PipelineRunner
from unittest.mock import patch


def test_submit_pipeline(
    mock_gcp_vars,
    mock_packager,
    mock_gcp_pipelinejob,
    mock_gcp_scheduler,
    test_gcp_app,
):
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

    from unittest.mock import patch

    with patch(
        "opsml.pipelines.systems.vertex.VertexPipeline",
        MockVertexPipeline,
    ) as mock_vertex_pipeline:
        runner = PipelineRunner(spec_filename="vertex-example-spec.yaml")
        response = test_gcp_app.post(
            url="opsml/submit_pipeline",
            json={
                "specs": runner.specs.dict(),
                "tasks": runner.task_dict,
                "schedule": False,
            },
        )

        assert response.status_code == 200
