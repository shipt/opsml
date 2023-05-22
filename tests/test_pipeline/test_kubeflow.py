import os
from opsml.pipelines import PipelineRunner


def test_pipeline_runner_kubeflow(mock_packager, mock_kubeflow_client):
    """Runs local test on pipeline that is already built to run on vertex"""

    os.environ["TEST_ENV_VAR"] = "test"
    os.environ["OPSML_PIPELINE_HOST_URI"] = "fake_kubeflow_uri"

    runner = PipelineRunner(spec_filename="kubeflow-example-spec.yaml")
    runner.specs.is_proxy = False
    assert len(runner.tasks) == 2

    runner.run()
