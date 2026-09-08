# Plan: Model Provider Management
计划版本：v0.1.0

状态：已完成 service / repository、数据库迁移、缓存与连接参数解析。
接入范围为可用于 Chat 的单模态和多模态模型。

## 1. 最小实现与文件范围

按 ponytail-review 检查方案：一张供应商表、一个具体仓储、现有 Service 文件中的直接函数；
使用现有 Pydantic、SQLAlchemy、httpx 和 Redis。无需 AbstractRepository、协议插件注册器、
模型实例池、额外后台刷新 Worker 或第二张模型表。

| 落点 | 变更 |
| --- | --- |
| `src/database/models.py` | 增加 `ModelProvider` 实体，JSON 保存模型条目和请求头 |
| `migrate/versions/` | 按现有 revision 链增加 `model_provider` 建表迁移 |
| `src/database/repositories/model_repository.py` | 增加 `ModelRepository(session)`，只做 SQL 与 flush |
| `src/database/repositories/__init__.py` | 导出具体仓储 |
| `server/entities/model.py` | 定义供应商输入/输出、含 model_type 的启用模型、连接参数和测试结果及校验 |
| `server/service/model_service.py` | 增加 CRUD、远程列表、连接测试、公开启用目录和内部连接解析函数 |
| `src/model/model_cache.py` | 增加独立公开目录缓存的 get/set/delete 方法，不查询数据库 |
| `test/test_model_service.py` | 使用 mock 验证 HTTP、缓存、校验及解析边界 |
| `test/test_model_repository.py` | 验证唯一性、CRUD 与模型列表替换的实际持久化语义 |

实体随当前项目的 metadata 建表入口注册；已有 `migrate/versions/`，实施时核对 revision head，
增加有序建表迁移并保持与新建数据库的 metadata 一致，不重建迁移框架。

## 2. 数据与调用示例

目标：`server/entities/model.py::ModelProviderCreate`，创建输入示例（不含真实密钥）：

```json
{
  "provider_id": "siliconflow",
  "name": "SiliconFlow",
  "protocol": "openai_compatible",
  "base_url": "https://provider.example/v1",
  "api_key": "example-only",
  "extra_headers": {},
  "is_enabled": true,
  "enabled_models": [
    {"model_id": "org/chat-model", "model_type": "qwen", "body_overrides": {"temperature": 0.2}},
    {"model_id": "org/multimodal-chat-model", "model_type": "qwen", "body_overrides": {}}
  ]
}
```

目标：`server/entities/model.py::EnabledModel` 与 `ModelConnection` 使用同一模型类型枚举：
`deepseek | qwen | glm | minomax | gemini | chatgpt | ollama | vllm`。
`ollama:qwen3:8b` 的模型条目使用 `model_type="ollama"`；vLLM 部署使用 `model_type="vllm"`。
两者按本地部署处理，地址和认证由供应商配置决定。类型不自动改写协议或远程模型 ID。
按 ponytail-review 的最小实现约束，只增加一个类型字段及枚举，不新增类型注册表或本地供应商子类。
移除能力枚举与能力分派；连接测试只实现聊天端点，单模态和多模态共用管理、缓存与解析方法。

目标：`server/service/model_service.py::update_provider`，MODEL-PROVIDER-001/005：

```text
验证完整配置 -> repository.update + flush -> db.commit
  -> 删除 model:providers:v1 -> repository.list -> 重建脱敏目录 -> SET + TTL
数据库错误 -> rollback -> 抛出业务错误
Redis 错误 -> 已保存配置 + cache_refreshed=false，不声称数据库回滚
```

目标：`server/service/model_service.py::resolve_runtime_model`，MODEL-PROVIDER-006：

```text
resolve_runtime_model(db, "ollama:qwen3:8b")
  -> split(':', 1)
  -> repository.get("ollama")
  -> 检查 is_enabled 与 enabled_models 中的 model_id=qwen3:8b
  -> 返回包含 model_type="ollama" 的 ModelConnection，交给上层运行时调用者使用
```

现有 `list_models()` 和 `src/model/model_tool.py` 维持 Chat 能力合同；本轮新服务的
`list_enabled_models()` 只服务数据库管理能力，名称明确区分两者。
管理入口不接受 ORM 对象直接作为 API 响应；更新输入省略 API Key 时保留，显式空字符串时清除。

## 3. 验证

对应 `tasks.md` 顺序实现，运行 `python -m unittest test.test_model_service test.test_model_repository`。
覆盖八种类型的保存/读取、未知类型拒绝、本地部署空密钥和内网地址，以及类型/协议独立性。
覆盖单模态和多模态聊天模型配置、明确非 Chat 的发现候选过滤，以及聊天探测失败的脱敏输出。
另执行现有 `test.test_model_cache` 确认 Chat 目录未回归、相关 Python 编译检查和 `git diff --check`。
生产数据库、真实密钥、远程推理及容器部署不在默认验证范围。

## 4. 实施结果

- 新迁移为 `migrate/versions/0008_model_provider.py`，接续 `0007_message_persistence`。
- Service 入口为 `create_provider`、`update_provider`、`delete_provider`、`get_provider`、
  `list_providers`、`list_enabled_models`、`rebuild_model_cache`、`discover_models`、
  `test_model_connection`、`resolve_runtime_model`。
- 24 项 unittest 通过；仓储与迁移使用真实 SQLite，AsyncSession 调用通过 mock 桥接同步 Session，
  远程接口使用 httpx MockTransport，Redis 使用内存测试替身。未验证真实 PostgreSQL/Redis/供应商。
- 定向 Ruff、Python 编译及 diff 空白检查通过。
- 按仓库规则尝试重建 Worker 镜像，但当前环境没有可用的 `docker` 命令；未构建或部署容器。
- 生产数据库迁移尚未执行。
