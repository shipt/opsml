"""empty message

Revision ID: 2d474549026b
Revises: fd32b1afafd5
Create Date: 2023-09-05 14:04:25.918202

"""
from alembic import op
import sqlalchemy as sa
from opsml.registry.sql.sql_schema import RegistryTableNames
from opsml.helpers.logging import ArtifactLogger

logger = ArtifactLogger.get_logger(__name__)


# revision identifiers, used by Alembic.
revision = "2d474549026b"
down_revision = "fd32b1afafd5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_context().bind
    insp = sa.inspect(bind)
    columns = insp.get_columns(RegistryTableNames.DATA.value)

    if not "uris" in [column["name"] for column in columns]:
        logger.info("Migration Adding uris column to data table")
        with op.batch_alter_table(RegistryTableNames.DATA.value) as batch_op:
            batch_op.add_column(sa.Column("uris", sa.JSON))


def downgrade() -> None:
    logger.info("Dropping uris column from data table")
    with op.batch_alter_table(RegistryTableNames.DATA.value) as batch_op:
        batch_op.drop_column("uris")
