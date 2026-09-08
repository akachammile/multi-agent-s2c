"""已确认用户归属后的模型密钥与私有请求头加密。"""

import json

import sqlalchemy as sa
from alembic import op

from src.database.credential_types import decrypt_credential, encrypt_credential

revision = "0010_model_credentials"
down_revision = "0009_model_provider_user"
branch_labels = None
depends_on = None


def _convert(encrypt: bool) -> None:
    table = sa.table("model_provider", sa.column("user_id", sa.Integer()), sa.column("provider_id", sa.String()), sa.column("api_key", sa.Text()), sa.column("extra_headers", sa.JSON()))
    connection = op.get_bind()
    changes = []
    for row in connection.execute(sa.select(table)).mappings():
        key, headers = row["api_key"], row["extra_headers"]
        if encrypt:
            key = encrypt_credential(key) if key else ""
            headers = encrypt_credential(json.dumps(headers)) if headers else {}
        else:
            key = decrypt_credential(key) if key else ""
            headers = json.loads(decrypt_credential(headers)) if headers else {}
        changes.append((row["user_id"], row["provider_id"], key, headers))
    # 先确认所有记录都可转换，缺密钥或解密失败时不改动原数据。
    for user_id, provider_id, key, headers in changes:
        connection.execute(table.update().where(table.c.user_id == user_id, table.c.provider_id == provider_id).values(api_key=key, extra_headers=headers))


def upgrade() -> None:
    _convert(True)


def downgrade() -> None:
    _convert(False)
