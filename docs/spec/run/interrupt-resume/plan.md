# Resume 输入与流式执行补齐

计划版本：v0.3.0

状态：待用户确认；仅完成设计，尚未修改生产代码。

## 范围与选择

落实 RUN-HIL-001 至 RUN-HIL-011 的多问题恢复闭环。保留现有恢复 URL、父子 Run、
ARQ 和 SSE 架构。输入统一为 `thread_metadata.resume.answers`，替换旧字符串 answer。
Thread Service 使用显式参数 `resume_input` 接收已校验回答。
中断只发生在主 Agent，恢复入口不接收 agent_slug，直接从现有 manager 获取 LeaderAgent。
本轮只支持现有 ask_user 的每题单选；自由文本需要另行明确工具题型与校验合同。

按 ponytail-review 检查复杂度：复用既有 `_stream_agent_event_chunks`、上下文构建与消息保存函数；
两个入口分别组织流程并保留自己的 chunk builder，不增加公共执行器、策略类、新表或兼容分支。
不改动当前工作区其他功能的未提交修改。

## 1. 请求与持久化（RUN-HIL-001 至 004、009 至 011）

`ChatAskUserComponent.vue` 按问题 ID 收集回答，`ChatView.vue:submitResume` 构造：

```json
{
  "thread_id": "thread-1",
  "thread_metadata": {
    "request_id": "resume-request-1",
    "resume": {
      "answers": {"database": "postgresql", "environment": "local"}
    }
  }
}
```

`server/service/agent_run_service.py:create_resume_agent_run_service` 在原有父 Run 锁与
身份校验内按 questions 校验回答。只接受完整 ID 集合和各题合法 value，不修剪或转换选项值。
同 request_id、同回答返回已有子 Run；同键不同回答或其他重复提交返回 409。
新 Resume Run 沿用父 Run 的 agent_id、thread_id、uid 和 model 配置，保存 answers，
trigger_message_id 仍为空；新 Run ID 入队。父 Run 保持 interrupted。
模型继承是复制父 Run 持久化配置，不保证恢复期间外部模型服务配置保持不变。

`web/src/types/chat.ts`、事件解析与线程详情恢复同步采用 questions；组件全答后一次提交，
运行切换仍使用现有 useAgentRun。父 Run ID 变化时清空回答。

## 2. Worker 显式传递恢复输入（RUN-HIL-007）

`server/worker.py:process_agent_run` 保留 run_type 分支：

```python
stream_thread_events = resume_agent_response(
    resume_input=metadata["resume"]["answers"],
    thread_id=thread_id,
    runtime_metadata=metadata,
    current_user=user,
    db=db,
)
```

恢复分支不读取普通消息。持久化输入缺失时走 Worker 原有失败收口。

## 3. 恢复入口（RUN-HIL-005、007、008）

`server/service/thread_service.py:resume_agent_response` 目标签名：

```python
async def resume_agent_response(
    *, resume_input: dict[str, str], thread_id: str,
    runtime_metadata: dict, current_user: AuthenticatedUser, db: AsyncSession,
) -> AsyncIterator[bytes]:
    ...
```

执行顺序：

1. 校验 thread_id 和当前 Run 身份；不得为恢复生成新 thread_id。
2. `agent_manager.get_agent("LeaderAgent")` 获取主 Agent，构造当前 Run 的 runtime context；
   使用现有 `_require_thread` 校验当前用户的顶层会话，不再调用依赖 agent_item 的
   `_build_agent_runtime` / `_check_conv_status`。父 Run 与 Thread 的匹配仍由创建恢复 Run 的
   Service 校验。初始化错误也进入恢复入口的 error 处理。
3. 用同 thread_id、uid 读取 checkpoint，确认存在待恢复中断；不存在则报错，不退回普通输入。
4. 调用 `stream_message_by_resume(Command(resume=resume_input), runtime_context=...)`。
5. 消费 `_stream_agent_event_chunks`，传入独立 builder 和 accumulated_msg，逐块 yield。
6. 流结束后调用一次 `save_message_from_langgraph_state`。
7. 检测再次中断：有则 yield interrupted 后 return；没有则 yield finished。
8. 异常时沿用普通入口的累计输出保存机制，以独立数据库会话调用 save_interrupt_message；
   保存失败记录日志且仍输出原始 error，不发送 finished。取消交由 Worker 处理。

普通入口仅修正同一收尾合同：删除重复保存、保存失败后停止成功路径、中断后 return。
不改变其 HumanMessage 输入方式。

## 4. 中断和停止状态（RUN-HIL-005、006、009）

当前 handler 产生 ask_human/pending_interrupt，而 Worker 消费 interrupted/interrupt，二者不一致。
`check_agent_interrupt_handler` 按 spec 变为返回 payload 或 None 的异步函数，直接读取
StateSnapshot.interrupts；构建问题仍用 build_agent_interrupt_message。
builder 输出纯问题 payload，不夹带内部 status；无效/空问题不生成默认答案或问题。
只接受单个 ask_user interrupt，多个独立 interrupt 明确失败。

两个入口在完成一次消息保存后执行同样的控制流；下面示例属于 resume_agent_response：

```python
interrupt_payload = await check_agent_interrupt_handler(
    agent_instance=agent_instance, context=agent_context,
)
if interrupt_payload is not None:
    yield make_agent_resume_event(status="interrupted", interrupt=interrupt_payload)
    return
yield make_agent_resume_event(status="finished", runtime_metadata=runtime_metadata)
```

`process_agent_run` 继续拥有终态落库和对外 interaction_required/end 发布。
去除无停止信号时默认 completed 的分支；未取消的无停止信号流按现有协议错误路径 failed。
保留 RUN-HIL-006 既有 changed-only 发布、case 内二次 end 与 terminal_flag 规则。

## 5. 验证与实施边界

实施前按 docs/development.md 选择本仓库验证命令。必要覆盖：

- Service：两题合法回答、漏答/多答/非法选项、越权、错线程、重复恢复和幂等冲突。
- Thread Service：Command 收到原字典、相同 checkpoint 身份、事件转换累计输出、消息只保存一次。
- 真实内存 checkpoint：ask_user 暂停后用两题回答恢复，原工具返回答案并继续输出；再次提问仍能暂停。
- 收尾：再次中断无 finished；初始化/执行/保存失败输出 error；缺失 checkpoint 失败；取消沿用现有状态。
- Worker：恢复分支不读取 HumanMessage；没有停止信号不得 completed。
- 消息持久化：重读父消息不重复落库，也不改写为 Resume Run 的输出归属。
- 前端：两题独立选中、未答完禁用提交、显示 label/提交 value、切换新 Run 及刷新恢复待回答问题。

生产实施涉及 Thread Service、Run Service、Worker、相关前端类型/解析/组件与已有测试。
本计划不拆 implementation 文件。当前仅验证文档差异；设计不能作为运行时验证证据。
