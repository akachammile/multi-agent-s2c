"""模型配置按用户隔离；旧记录必须显式确认归属。"""

import json

import sqlalchemy as sa
from alembic import context, op

revision = "0009_model_provider_user"
down_revision = "0008_model_provider"
branch_labels = None
depends_on = None

_NAMING = {"pk": "pk_%(table_name)s"}


def upgrade() -> None:
    connection = op.get_bind()
    providers = set(connection.execute(sa.text("SELECT provider_id FROM model_provider")).scalars())
    owners = {}
    if providers:
        raw = context.get_x_argument(as_dictionary=True).get("model_provider_owners")
        try:
            owners = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            raise RuntimeError("旧模型配置归属映射无效，原数据未修改") from None
        if not isinstance(owners, dict) or set(owners) != providers or any(type(value) is not int or value <= 0 for value in owners.values()):
            raise RuntimeError("旧全局模型配置缺少完整用户归属映射；请确认归属后通过 -x model_provider_owners 提供，原数据未修改")
        users = set(connection.execute(sa.text('SELECT id FROM "user"')).scalars())
        if not set(owners.values()) <= users:
            raise RuntimeError("模型配置归属用户不存在，原数据未修改")

    pk_name = sa.inspect(connection).get_pk_constraint("model_provider")["name"] or "pk_model_provider"
    op.add_column("model_provider", sa.Column("user_id", sa.Integer(), nullable=True))
    for provider_id, user_id in owners.items():
        connection.execute(sa.text("UPDATE model_provider SET user_id=:user_id WHERE provider_id=:provider_id"), {"user_id": user_id, "provider_id": provider_id})
    with op.batch_alter_table("model_provider", naming_convention=_NAMING) as batch:
        batch.drop_constraint(pk_name, type_="primary")
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch.create_primary_key("pk_model_provider", ["user_id", "provider_id"])
        batch.create_foreign_key("fk_model_provider_user_id", "user", ["user_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    connection = op.get_bind()
    duplicate = connection.execute(sa.text("SELECT provider_id FROM model_provider GROUP BY provider_id HAVING COUNT(*) > 1 LIMIT 1")).first()
    if duplicate:
        raise RuntimeError("多个用户存在同名供应商，不能安全降级为全局配置；原数据未修改")
    with op.batch_alter_table("model_provider", naming_convention=_NAMING) as batch:
        batch.drop_constraint("fk_model_provider_user_id", type_="foreignkey")
        batch.drop_constraint("pk_model_provider", type_="primary")
        batch.drop_column("user_id")
        batch.create_primary_key("pk_model_provider", ["provider_id"])
