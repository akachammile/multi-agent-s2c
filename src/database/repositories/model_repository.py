"""模型供应商持久化；事务提交由 Service 负责。"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ModelProvider


class ModelRepository:
    def __init__(self, session: AsyncSession, user_id: int):
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("必须提供有效的用户 ID")
        self.session = session
        self.user_id = user_id

    async def get_provider_by_id(self, provider_id: str) -> ModelProvider | None:
        result = await self.session.execute(select(ModelProvider).where(ModelProvider.user_id == self.user_id, ModelProvider.provider_id == provider_id).execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    async def list_providers(self, *, enabled_only: bool = False) -> list[ModelProvider]:
        query = select(ModelProvider).where(ModelProvider.user_id == self.user_id).order_by(ModelProvider.provider_id)
        if enabled_only:
            query = query.where(ModelProvider.is_enabled.is_(True))
        result = await self.session.execute(query.execution_options(populate_existing=True))
        return list(result.scalars().all())

    async def create_provider(self, **values: Any) -> ModelProvider:
        provider = ModelProvider(user_id=self.user_id, **values)
        self.session.add(provider)
        await self.session.flush()
        return provider

    async def update_provider(self, provider: ModelProvider, **values: Any) -> ModelProvider:
        if provider.user_id != self.user_id or {"user_id", "provider_id"} & values.keys():
            raise ValueError("不可修改其他用户配置或配置标识")
        for field, value in values.items():
            setattr(provider, field, value)
        await self.session.flush()
        return provider

    async def delete_provider(self, provider: ModelProvider) -> None:
        if provider.user_id != self.user_id:
            raise ValueError("不可删除其他用户配置")
        await self.session.delete(provider)
        await self.session.flush()
