from opsml.pipelines.base_runner import Task, BaseRunner
import pytest


def test_add_task(mock_pipeline_task: Task):
    runner = BaseRunner()

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
    assert runner.relationships[mock_pipeline_task.name][0] == f"{mock_pipeline_task.name}_2"

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
    runner = BaseRunner()

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
