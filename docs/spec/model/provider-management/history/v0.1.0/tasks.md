# Tasks: Model Provider Management

- [x] T1（MODEL-PROVIDER-001/002）：供应商实体、具体仓储、单/多模态聊天模型、八种 model_type、本地部署语义与输入输出校验。
- [x] T2（MODEL-PROVIDER-001/005）：CRUD 服务、提交/回滚及公开目录缓存刷新和降级。
- [x] T3（MODEL-PROVIDER-003/004）：远程模型发现、非 Chat 候选过滤及显式聊天连接测试。
- [x] T4（MODEL-PROVIDER-006）：按组合 ID 查询聊天模型的内部完整连接配置。
- [x] T5：持久化/HTTP mock/缓存/密钥输出边界测试、现有 Chat 缓存回归和静态检查。

24 项测试通过。真实服务与数据库迁移未执行；Worker 镜像重建受当前环境缺少 Docker 限制。
