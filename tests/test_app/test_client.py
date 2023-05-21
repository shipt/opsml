import pytest
from pytest_lazyfixture import lazy_fixture
from unittest.mock import patch, MagicMock
import pandas as pd
from pydantic import ValidationError
from opsml.registry import DataCard, ModelCard, RunCard, PipelineCard
from opsml.pipelines.runner import PipelineRunner
import uuid
import tenacity
import json


def test_submit_pipeline(
    test_app,
    mock_local_storage_with_gcs,
    mock_packager,
    mock_gcp_pipelinejob,
    mock_gcp_scheduler,
):
    runner = PipelineRunner(spec_filename="vertex-example-spec.yaml")
    response = test_app.post(
        url="opsml/submit_pipeline",
        json={
            "specs": runner.specs.dict(),
            "tasks": runner.task_dict,
            "schedule": True,
        },
    )

    assert response.status_code == 200
