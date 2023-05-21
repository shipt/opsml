from opsml.pipelines.runner import PipelineRunner
from opsml.pipelines.types import Task


def _test_decorator_task(mock_pipeline_task: Task, sklearn_pipeline):
    model, data = sklearn_pipeline
    runner = PipelineRunner()

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
