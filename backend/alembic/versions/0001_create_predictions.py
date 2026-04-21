from alembic import op
import sqlalchemy as sa

revision = "0001_create_predictions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("predictions")