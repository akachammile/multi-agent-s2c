"""增加平台聊天模型供应商配置。"""

import sqlalchemy as sa
from alembic import op

revision = "0008_model_provider"
down_revision = "0007_message_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_provider",
        sa.Column("provider_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("protocol", sa.String(32), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("extra_headers", sa.JSON(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("enabled_models", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("model_provider")
