from unittest.mock import patch, MagicMock
from opsml.registry.sql.connectors.connector import LocalSQLConnection
from opsml.registry.sql.migration.migrate import run_alembic_migrations
from sqlalchemy.engine.reflection import Inspector


def test_migrations(mock_local_engine, experiment_table_to_migrate):
    with patch.multiple(
        "opsml.registry.sql.connectors.connector.LocalSQLConnection",
        get_engine=MagicMock(return_value=mock_local_engine),
    ) as engine_mock:
        local_client = LocalSQLConnection(tracking_uri="sqlite://")
        engine = local_client.get_engine()

        experiment_table_to_migrate.__table__.create(bind=engine, checkfirst=True)

        tables = Inspector.from_engine(engine).get_table_names()
        assert "OPSML_EXPERIMENT_REGISTRY" in tables

        # should switch name to "OPSML_RUN_REGISTRY"
        run_alembic_migrations()

        # need to instantiate again
        tables = Inspector.from_engine(engine).get_table_names()

        assert "OPSML_EXPERIMENT_REGISTRY" not in tables
        assert "OPSML_RUN_REGISTRY" in tables
