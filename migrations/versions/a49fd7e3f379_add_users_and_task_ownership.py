"""add users and task ownership

Revision ID: a49fd7e3f379
Revises: 427b9692fb5b
Create Date: 2026-10-31 13:49:54.209411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a49fd7e3f379'
down_revision: Union[str, Sequence[str], None] = '427b9692fb5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column("owner_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_tasks_owner_id_users",
            "users",
            ["owner_id"],
            ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint(
            "fk_tasks_owner_id_users",
            type_="foreignkey"
        )
        batch_op.drop_column("owner_id")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
