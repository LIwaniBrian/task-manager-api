"""Rename task table and add due_date."""

from alembic import op
import sqlalchemy as sa


revision = "427b9692fb5b"
down_revision = "a1c1047d1d78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the existing table instead of deleting its records.
    op.rename_table("task", "tasks")

    # Rename the existing index to match the new table name.
    op.drop_index("ix_task_id", table_name="tasks")
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)

    # Add the new optional due_date column.
    op.add_column(
        "tasks",
        sa.Column("due_date", sa.String(), nullable=True)
    )


def downgrade() -> None:
    # Remove due_date.
    op.drop_column("tasks", "due_date")

    # Restore the original index and table name.
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.create_index("ix_task_id", "tasks", ["id"], unique=False)
    op.rename_table("tasks", "task")
