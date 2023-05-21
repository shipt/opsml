from opsml.pipelines.base_runner import Task, PipelineRunnerBase
from opsml.pipelines.runner import PipelineRunner, PipelineSpec
import os
import pytest


def test_add_task(mock_pipeline_task: Task):
    runner = PipelineRunnerBase()

    first_task = runner.add_task(
        name=mock_pipeline_task.name,
        entry_point=mock_pipeline_task.entry_point,
        flavor=mock_pipeline_task.flavor,
    )

    runner.add_task(
        name=f"{mock_pipeline_task.name}_2",
        entry_point=mock_pipeline_task.entry_point,
        flavor=mock_pipeline_task.flavor,
        upstream_tasks=[first_task],
    )

    assert len(runner.tasks) == 2
    runner.tasks[1].upstream_tasks[0] == mock_pipeline_task.name

    with pytest.raises(ValueError):
        runner.add_task(
            name=mock_pipeline_task.name,
            entry_point=mock_pipeline_task.entry_point,
            flavor=None,
        )


def test_decorator_task(
    mock_pipeline_task: Task,
    mock_sql_pipeline_task: Task,
):
    runner = PipelineRunnerBase()

    @runner.ml_task(flavor=mock_pipeline_task.flavor)
    def test_task():
        return 0

    @runner.ml_task(
        flavor=mock_pipeline_task.flavor,
        upstream_tasks=["test_task"],
    )
    def test_task2():
        return 1

    assert len(runner.tasks) == 2

    # these should work
    assert runner.tasks[0].func() == 0
    assert runner.tasks[1].func() == 1

    # add sql task
    # should be able to mix and match different styles
    runner.add_task(
        name=mock_sql_pipeline_task.name,
        entry_point=mock_sql_pipeline_task.entry_point,
        flavor=mock_sql_pipeline_task.flavor,
    )

    assert len(runner.tasks) == 3


def test_config_load():
    os.environ["TEST_ENV_VAR"] = "test"
    runner = PipelineRunnerBase(spec_filename="pipeline.yaml")

    assert len(runner.tasks) == 3
    assert runner.specs.pipeline.env_vars["test_env_var"] == "test"


def test_pipeline_runner_local_spec():
    """Tests local pipeline run from pipeline built with decorators"""

    spec = PipelineSpec(
        project_name="opsml-test",
        cron="0 5 * * *",
        owner="test_owner",
        team="team",
        pipeline_system="local",
        user_email="test@shipt.com",
        container_registry="test",
    )

    runner = PipelineRunner(pipeline_spec=spec)
    runner.specs.source_file = "local-spec.yaml"
    runner.specs.is_proxy = False

    @runner.ml_task(flavor="sklearn")
    def test_task():
        print("test_1")

    @runner.ml_task(
        flavor="sklearn",
        upstream_tasks=["test_task"],
    )
    def test_task2():
        print("test_2")

    runner.run()


def test_pipeline_runner_local_with_spec():
    """Runs local test on pipeline that is already built to run on vertex"""

    os.environ["TEST_ENV_VAR"] = "test"
    runner = PipelineRunner(spec_filename="vertex-example-spec.yaml")
    runner.specs.is_proxy = False

    assert len(runner.tasks) == 2
    runner.specs.pipeline_system = "local"

    runner.run()
