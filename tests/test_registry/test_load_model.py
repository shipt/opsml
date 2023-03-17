from click.testing import CliRunner
from opsml_artifacts.scripts.load_model_card import load_model_card_to_file, ModelLoaderCli
from unittest.mock import patch, MagicMock


def test_cli_class(mock_model_cli_loader, test_model_card, mock_pathlib):
    with patch.multiple(
        "opsml_artifacts.registry.sql.registry.CardRegistry",
        load_card=MagicMock(return_value=test_model_card),
    ):
        loader = mock_model_cli_loader(
            storage_type="local",
            name="driven_drop_off_predictor",
            team="SPMS",
            versions=["2"],
            uid="blah",
        )

        loader.save_to_local_file()


def test_load_model_card_version(mock_model_cli_loader, test_model_card, mock_pathlib):

    with patch.multiple(
        "opsml_artifacts.registry.sql.registry.CardRegistry",
        load_card=MagicMock(return_value=test_model_card),
    ):
        args1 = ["--name", "driven_drop_off_predictor", "--team", "SPMS", "--version", "2"]
        args2 = ["--name", "driven_drop_off_predictor", "--team", "SPMS", "--version", "2", "--version", "3"]
        args3 = ["--name", "driven_drop_off_predictor", "--uid", "blah"]

        for arg_list in [args1, args2, args3]:
            runner = CliRunner()
            result = runner.invoke(load_model_card_to_file, arg_list)
            assert result.exit_code == 0
