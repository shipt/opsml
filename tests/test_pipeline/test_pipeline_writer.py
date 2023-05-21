from opsml.pipelines import PipelineRunner, PipelineSpec

from opsml.pipelines.types import Task


def test_decorator_task(mock_pipeline_task: Task, sklearn_pipeline):
    model, data = sklearn_pipeline

    spec = PipelineSpec(
        project_name="opsml-test",
        cron="0 5 * * *",
        owner="test_owner",
        team="team",
        pipeline_system="vertex",
        user_email="test@shipt.com",
        container_registry="test",
    )

    runner = PipelineRunner(pipeline_spec=spec)

    @runner.ml_task(flavor=mock_pipeline_task.flavor)
    def test_data():
        from opsml.registry import DataCard

        data_card = DataCard(
            data=data,
            name="pipeline_data",
            team="mlops",
            user_email="mlops.com",
        )

        return data_card

    runner.generate_pipeline_code()
