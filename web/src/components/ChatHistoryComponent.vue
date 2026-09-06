<script setup lang="ts">
import { ref, watch } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"
import { ChevronDown, MoreHorizontal } from "@lucide/vue"
import { Dropdown as ADropdown, Menu as AMenu, MenuItem as AMenuItem, Modal as AModal, Input as AInput } from "ant-design-vue"

import { deleteThread, listThreads, renameThread } from "@/api/agent"
import type { ThreadSummaryResponse } from "@/types/chat"

const route = useRoute()
const router = useRouter()
const expanded = ref(true)
const threads = ref<ThreadSummaryResponse[]>([])
const cursor = ref<string | null>(null)
const loading = ref(false)
const error = ref("")
const selected = ref<ThreadSummaryResponse | null>(null)
const action = ref<"rename" | "delete">("rename")
const title = ref("")
const saving = ref(false)
const actionError = ref("")
let requestVersion = 0

const load = async (more = false) => {
  if (more && (loading.value || !cursor.value)) return
  const version = ++requestVersion
  loading.value = true
  error.value = ""
  try {
    const result = await listThreads({ limit: 50, cursor: more ? cursor.value ?? undefined : undefined })
    if (version !== requestVersion) return
    threads.value = more ? [...threads.value, ...result.items.filter(item => !threads.value.some(existing => existing.thread_id === item.thread_id))] : result.items
    cursor.value = result.has_more ? result.next_cursor : null
  } catch (cause) {
    if (version === requestVersion) error.value = cause instanceof Error ? cause.message : "对话加载失败"
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

watch(() => route.params.threadId, () => { void load() }, { immediate: true })

const openAction = (thread: ThreadSummaryResponse, nextAction: "rename" | "delete") => {
  selected.value = thread
  action.value = nextAction
  title.value = thread.title
  actionError.value = ""
}

const submit = async () => {
  const thread = selected.value
  if (!thread || saving.value || (action.value === "rename" && !title.value.trim())) return
  saving.value = true
  actionError.value = ""
  try {
    if (action.value === "rename") {
      const updated = await renameThread(thread.thread_id, title.value.trim())
      threads.value = threads.value.map(item => item.thread_id === thread.thread_id ? updated : item)
    } else {
      await deleteThread(thread.thread_id)
      threads.value = threads.value.filter(item => item.thread_id !== thread.thread_id)
      if (route.params.threadId === thread.thread_id) await router.push({ name: "chat" })
    }
    selected.value = null
  } catch (cause) {
    actionError.value = cause instanceof Error ? cause.message : "操作失败，请重试"
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="flex min-h-0 flex-1 flex-col px-1.5 pt-3 pb-2" aria-label="对话历史">
    <button
      type="button"
      class="flex shrink-0 items-center gap-1.5 rounded-sm px-2.5 py-2 text-xs font-medium text-slate hover:bg-graphite/5 focus-visible:outline-2"
      :aria-expanded="expanded"
      aria-controls="sidebar-chat-history"
      @click="expanded = !expanded"
    >
      Chat
      <ChevronDown :size="13" :class="{ '-rotate-90': !expanded }" aria-hidden="true" />
    </button>
    <div v-show="expanded" id="sidebar-chat-history" class="min-h-0 flex-1 overflow-y-auto overscroll-contain [scrollbar-width:thin]" :aria-busy="loading">
      <div
        v-for="thread in threads"
        :key="thread.thread_id"
        class="group flex min-w-0 items-center rounded-sm hover:bg-graphite/5"
        :class="{ 'bg-graphite/8': route.params.threadId === thread.thread_id }"
      >
        <RouterLink
          :to="{ name: 'conversation', params: { threadId: thread.thread_id } }"
          class="min-w-0 flex-1 truncate rounded-sm px-2.5 py-2 text-sm focus-visible:outline-2"
          :title="thread.title"
          :aria-current="route.params.threadId === thread.thread_id ? 'page' : undefined"
        >
          {{ thread.title }}
        </RouterLink>
        <ADropdown :trigger="['click']" placement="bottomRight">
          <button type="button" class="mr-1 grid size-8 shrink-0 place-items-center rounded-sm text-slate hover:bg-graphite/8 focus-visible:outline-2" :aria-label="`对话操作：${thread.title}`">
            <MoreHorizontal :size="16" aria-hidden="true" />
          </button>
          <template #overlay>
            <AMenu>
              <AMenuItem key="rename" @click="openAction(thread, 'rename')">重命名</AMenuItem>
              <AMenuItem key="delete" danger @click="openAction(thread, 'delete')">删除对话</AMenuItem>
            </AMenu>
          </template>
        </ADropdown>
      </div>
      <p v-if="error" role="alert" class="px-2.5 py-2 text-xs text-danger">{{ error }}</p>
      <button v-if="error" type="button" class="px-2.5 py-2 text-xs hover:underline" @click="load(Boolean(cursor))">重试</button>
      <p v-else-if="loading" role="status" class="px-2.5 py-2 text-xs text-slate">加载中…</p>
      <p v-else-if="!threads.length" class="px-2.5 py-2 text-xs text-slate">暂无对话</p>
      <button v-if="cursor && !loading && !error" type="button" class="w-full rounded-sm px-2.5 py-2 text-left text-xs text-slate hover:bg-graphite/5" @click="load(true)">加载更多</button>
    </div>
  </section>
  <AModal
    :open="selected !== null"
    :title="action === 'rename' ? '重命名对话' : '删除对话'"
    :ok-text="action === 'rename' ? '保存' : '删除'"
    cancel-text="取消"
    :confirm-loading="saving"
    :closable="!saving"
    :mask-closable="!saving"
    :keyboard="!saving"
    :cancel-button-props="{ disabled: saving }"
    :ok-button-props="{ danger: action === 'delete', disabled: action === 'rename' && !title.trim() }"
    @cancel="selected = null"
    @ok="submit"
  >
    <AInput v-if="action === 'rename'" v-model:value="title" aria-label="对话标题" :disabled="saving" @press-enter="submit" />
    <p v-else class="break-words">确定删除「{{ selected?.title }}」吗？删除后该对话将从历史列表中移除。</p>
    <p v-if="actionError" role="alert" class="mt-2 text-sm text-danger">{{ actionError }}</p>
  </AModal>
</template>
