# Resume 实施任务

状态：待用户确认。计划见 plan.md v0.3.0。

- [ ] T1（RUN-HIL-001 至 004）：Run Service 接收 answers、校验问题和选项、继承运行身份及模型，覆盖幂等恢复。
- [ ] T2（RUN-HIL-005、007、008）：补齐 resume_agent_response 和显式 resume_input，去掉 agent_slug 参数并直接获取主 Agent；统一中断载荷及两入口收尾，验证 checkpoint 恢复和消息保存。
- [ ] T3（RUN-HIL-006、007、009）：Worker 传入回答字典，去除无停止信号默认成功，验证终态和取消。
- [ ] T4（RUN-HIL-009 至 011）：前端类型、事件/详情解析、问题组件和提交适配 questions/answers，验证多题提交与刷新恢复。
- [ ] T5（RUN-HIL-001 至 011）：完成计划所列集成与浏览器验证，记录实际证据；通过后归档本版本 plan/tasks。
