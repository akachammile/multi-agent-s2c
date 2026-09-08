<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { Eye, EyeOff, LoaderCircle, Plug, RefreshCw, Search } from "@lucide/vue"
import { Modal } from "ant-design-vue"

import deepseekLogo from "@/assets/models/deepseek-color.svg"
import qwenLogo from "@/assets/models/qwen-color.svg"
import glmLogo from "@/assets/models/zhipu-color.svg"
import minimaxLogo from "@/assets/models/minimax-color.svg"
import geminiLogo from "@/assets/models/gemini-color.svg"
import chatgptLogo from "@/assets/models/chatgpt-color.svg"
import ollamaLogo from "@/assets/models/ollama-color.svg"
import vllmLogo from "@/assets/models/vllm-color.svg"
import { useModelSettings } from "@/composables/useModelSettings"
import type { ChatCapability, ModelProviderId } from "@/types/model"

const providers: { id: ModelProviderId; name: string; logo: string }[] = [
  { id: "deepseek", name: "DeepSeek", logo: deepseekLogo },
  { id: "qwen", name: "Qwen", logo: qwenLogo },
  { id: "glm", name: "GLM", logo: glmLogo },
  { id: "minomax", name: "minomax", logo: minimaxLogo },
  { id: "gemini", name: "Gemini", logo: geminiLogo },
  { id: "chatgpt", name: "ChatGPT", logo: chatgptLogo },
  { id: "ollama", name: "Ollama", logo: ollamaLogo },
  { id: "vllm", name: "vLLM", logo: vllmLogo }
]
const capabilityLabels: Record<ChatCapability, string> = {
  chat: "对话", vision: "视觉", reasoning: "推理", tools: "工具", code: "代码", audio: "音频", video: "视频"
}
const { selected, draft, blocked, loading, loadError, busy, candidates, chosen, load, act, confirmModels } = useModelSettings()
const provider = computed(() => providers.find(item => item.id === selected.value)!)
const revealKey = ref(false)
const search = ref("")
const filteredCandidates = computed(() => (candidates.value ?? []).filter(model => model.model_id.toLowerCase().includes(search.value.toLowerCase())))
watch(draft, () => { revealKey.value = false })
watch(candidates, () => { search.value = "" })

function closeCandidates(event: Event) {
  event.stopPropagation()
  candidates.value = null
}
</script>

<template>
  <div class="grid min-h-full min-w-0 grid-cols-1 content-start gap-6 min-[1024px]:grid-cols-[176px_minmax(0,1fr)] min-[1024px]:gap-9">
    <nav class="min-w-0" aria-label="模型供应商">
      <h3 class="m-0 mb-5 text-base font-semibold">Models</h3>
      <div class="flex gap-1 overflow-x-auto pb-1 min-[1024px]:flex-col">
        <button
          v-for="item in providers"
          :key="item.id"
          type="button"
          :aria-pressed="selected === item.id"
          :disabled="busy !== null || candidates !== null"
          class="flex min-h-11 shrink-0 items-center gap-3 rounded-md px-3 text-left text-sm transition-colors hover:bg-graphite/5 focus-visible:outline-2 focus-visible:outline-graphite/50 disabled:opacity-60"
          :class="selected === item.id ? 'bg-graphite/5 font-semibold text-graphite' : 'bg-transparent text-slate'"
          @click="selected = item.id"
        >
          <img :src="item.logo" alt="" class="h-6 w-6 shrink-0 object-contain">
          {{ item.name }}
        </button>
      </div>
    </nav>

    <div class="flex min-w-0 flex-col min-[1024px]:min-h-[490px]" :aria-busy="loading">
      <div class="mb-7 flex min-h-8 items-center justify-between gap-4">
        <h3 class="m-0 flex min-w-0 items-center gap-3 text-lg font-semibold">
          <img :src="provider.logo" alt="" class="h-7 w-7 object-contain">
          {{ provider.name }}
        </h3>
        <label class="flex shrink-0 items-center gap-3 text-sm">
          启用
          <button
            type="button" role="switch" aria-label="启用供应商"
            :aria-checked="draft.is_enabled" :disabled="blocked"
            class="relative h-5 w-9 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-40"
            :class="draft.is_enabled ? 'bg-graphite' : 'bg-graphite/20'"
            @click="draft.is_enabled = !draft.is_enabled"
          >
            <span class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform" :class="{ 'translate-x-4': draft.is_enabled }" />
          </button>
        </label>
      </div>

      <div v-if="loading || loadError" class="mb-4 flex justify-center">
        <LoaderCircle v-if="loading" :size="18" class="animate-spin text-slate" aria-label="加载中" />
        <button v-else type="button" class="flex items-center gap-2 text-sm text-slate" @click="load"><RefreshCw :size="16" />重试</button>
      </div>

      <div class="flex items-center gap-2 rounded-md bg-graphite/[0.025] px-4 py-3 focus-within:ring-1 focus-within:ring-graphite/20">
        <label class="min-w-0 flex-1">
          <span class="mb-1.5 block text-xs text-slate">API Key</span>
          <input
            v-model="draft.key" :type="revealKey ? 'text' : 'password'" :disabled="blocked"
            :placeholder="draft.hasKey ? '••••••••••••••••' : ''"
            autocomplete="off" spellcheck="false" aria-label="API Key"
            class="block w-full min-w-0 bg-transparent text-sm outline-none placeholder:text-slate"
            @input="draft.keyEdited = true"
          >
        </label>
        <button type="button" :aria-label="revealKey ? '隐藏 API Key' : '显示 API Key'" :disabled="blocked" class="grid h-8 w-8 shrink-0 place-items-center rounded text-slate hover:bg-graphite/5 hover:text-graphite disabled:opacity-40" @click="revealKey = !revealKey">
          <component :is="revealKey ? EyeOff : Eye" :size="18" :stroke-width="1.7" />
        </button>
        <button type="button" aria-label="检测模型连接" :disabled="blocked" class="grid h-8 w-8 shrink-0 place-items-center rounded text-slate hover:bg-graphite/5 hover:text-graphite disabled:opacity-40" @click="act('test')">
          <LoaderCircle v-if="busy === 'test'" :size="18" class="animate-spin" />
          <Plug v-else :size="18" :stroke-width="1.7" />
        </button>
      </div>

      <label class="mt-3 block rounded-md bg-graphite/[0.025] px-4 py-3 focus-within:ring-1 focus-within:ring-graphite/20">
        <span class="mb-1.5 block text-xs text-slate">Base URL</span>
        <input v-model="draft.base_url" :disabled="blocked" type="url" autocomplete="off" spellcheck="false" class="block w-full min-w-0 bg-transparent text-sm outline-none">
      </label>

      <div class="mt-7 border-t border-graphite/8 pt-5">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h4 class="m-0 text-sm font-semibold">模型</h4>
          <button type="button" :disabled="blocked" class="flex items-center gap-2 rounded px-2 py-1 text-xs text-slate hover:bg-graphite/5 hover:text-graphite disabled:opacity-40" @click="act('discover')">
            <LoaderCircle v-if="busy === 'discover'" :size="14" class="animate-spin" />获取模型
          </button>
        </div>
        <ul class="m-0 list-none p-0">
          <li v-for="model in draft.models" :key="model.model_id" class="flex min-h-11 min-w-0 items-center gap-3 rounded-md px-2.5 py-2 transition-colors hover:bg-graphite/5">
            <span class="min-w-0 truncate text-sm font-medium" :title="model.model_id">{{ model.model_id }}</span>
            <span class="ml-auto flex shrink-0 items-center gap-1">
              <span v-for="capability in model.capabilities" :key="capability" class="whitespace-nowrap rounded-sm bg-graphite/7 px-1.5 py-0.5 text-[10px] leading-4 text-slate">{{ capabilityLabels[capability] }}</span>
            </span>
          </li>
        </ul>
      </div>

      <div class="mt-auto flex justify-end pt-10">
        <button type="button" :disabled="blocked" class="flex min-h-9 min-w-20 items-center justify-center gap-2 rounded-md bg-graphite px-5 text-sm text-white hover:bg-graphite/85 disabled:opacity-40" @click="act('save')">
          <LoaderCircle v-if="busy === 'save'" :size="15" class="animate-spin" />保存
        </button>
      </div>
    </div>

    <Modal :open="candidates !== null" title="选择聊天模型" ok-text="确定" cancel-text="取消" :z-index="1100" @ok="confirmModels" @cancel="closeCandidates">
      <label class="my-4 flex items-center gap-2 rounded bg-graphite/5 px-3 py-2">
        <Search :size="16" class="shrink-0 text-slate" />
        <input v-model="search" aria-label="搜索模型" placeholder="搜索模型" class="min-w-0 flex-1 bg-transparent text-sm outline-none">
      </label>
      <div class="max-h-80 overflow-y-auto">
        <label v-for="model in filteredCandidates" :key="model.model_id" class="flex cursor-pointer items-center gap-3 rounded px-2 py-2.5 text-sm hover:bg-graphite/5">
          <input v-model="chosen" type="checkbox" :value="model.model_id" class="accent-graphite">
          <span class="min-w-0 break-all">{{ model.model_id }}</span>
        </label>
      </div>
    </Modal>
  </div>
</template>
