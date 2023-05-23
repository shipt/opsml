from opsml.pipelines import PipelineRunner
from unittest.mock import patch


def test_submit_pipeline(test_app, mock_packager, mock_kubeflow_client, db_registries):
    runner = PipelineRunner(spec_filename="kubeflow-example-spec.yaml")
    response = test_app.post(
        url="opsml/submit_pipeline",
        json={
            "specs": runner.specs.dict(),
            "tasks": runner.task_dict,
            "schedule": False,
        },
    )

    assert response.status_code == 200
