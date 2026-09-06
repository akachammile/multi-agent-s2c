<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import deepseekLogo from "@/assets/models/deepseek-color.svg"
import qwenLogo from "@/assets/models/qwen-color.svg"
import minimaxLogo from "@/assets/models/minimax-color.svg"
import geminiLogo from "@/assets/models/gemini-color.svg"
import openaiLogo from "@/assets/models/openai.svg"
import zhipuLogo from "@/assets/models/zhipu-color.svg"
import type { ChatModelOption } from "@/types/model"

const props = withDefaults(defineProps<{
  modelValue: string
  models: ChatModelOption[]
  loading?: boolean
  disabled?: boolean
  placement?: "top" | "bottom"
}>(), { loading: false, disabled: false, placement: "top" })

const emit = defineEmits<{ "update:modelValue": [modelId: string] }>()
const families = [
  { id: "qwen", name: "千问", logo: qwenLogo },
  { id: "deepseek", name: "DeepSeek", logo: deepseekLogo },
  { id: "minimax", name: "MiniMax", logo: minimaxLogo },
  { id: "gemini", name: "Gemini", logo: geminiLogo },
  { id: "openai", name: "OpenAI", logo: openaiLogo },
  { id: "zhipu", name: "智谱", logo: zhipuLogo }
]
const container = ref<HTMLDivElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const dial = ref<SVGSVGElement | null>(null)
const open = ref(false)
const listOpen = ref(false)
const modelList = ref<HTMLDivElement | null>(null)
const index = ref<number | null>(null)

const family = computed(() => index.value === null ? null : families[index.value]!)
const belongsTo = (model: ChatModelOption, id: string) => model.icon === id
  || (id === "minimax" && model.name.toLowerCase().startsWith("minimax"))
  || (id === "zhipu" && /^(glm|chatglm)/i.test(model.name))
const familyModels = computed(() => props.models.filter(model => family.value && belongsTo(model, family.value.id)))
const selectedModel = computed(() => props.models.find(model => model.id === props.modelValue))
const selectedFamily = computed(() => selectedModel.value ? families.find(item => belongsTo(selectedModel.value!, item.id)) : undefined)
const controlDisabled = computed(() => props.disabled || props.loading || !props.models.some(model => families.some(item => item.id === model.icon)))
const point = (angle: number, radius: number) => ({
  x: 100 + Math.cos(angle * Math.PI / 180) * radius,
  y: 100 + Math.sin(angle * Math.PI / 180) * radius
})
const sectors = families.map((item, position) => {
  const start = point(position * 60 - 120, 98)
  const end = point(position * 60 - 60, 98)
  const icon = point(position * 60 - 90, 64)
  return { ...item, path: `M100 100 L${start.x} ${start.y} A98 98 0 0 1 ${end.x} ${end.y} Z`, x: icon.x - 13, y: icon.y - 13 }
})
const showModels = async (position: number) => {
  index.value = position
  listOpen.value = true
  await nextTick()
  modelList.value?.focus()
}
const back = async () => {
  listOpen.value = false
  await nextTick()
  dial.value?.focus()
  index.value = null
}
const close = (restoreFocus = false) => {
  open.value = false
  if (restoreFocus) void nextTick(() => trigger.value?.focus())
}
const toggle = async () => {
  if (controlDisabled.value) return
  if (open.value) return close()
  index.value = null
  listOpen.value = false
  open.value = true
  await nextTick()
  dial.value?.focus()
}

const selectModel = (model: ChatModelOption) => {
  if (!model.is_available || controlDisabled.value) return
  emit("update:modelValue", model.id)
  close(true)
}
const onKeydown = (event: KeyboardEvent) => {
  if (["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(event.key)) {
    event.preventDefault()
    const direction = event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 : -1
    index.value = index.value === null ? 0 : (index.value + direction + families.length) % families.length
  } else if ((event.key === "Enter" || event.key === " ") && event.target === dial.value && index.value !== null) {
    event.preventDefault()
    void showModels(index.value)
  }
}
const onBlur = () => { if (open.value) close() }
const onOutside = (event: Event) => {
  if (open.value && !container.value?.contains(event.target as Node)) close()
}
const onEscape = (event: KeyboardEvent) => {
  if (open.value && event.key === "Escape") { event.preventDefault(); close(true) }
}
watch([controlDisabled, () => props.models], () => { if (open.value) close() })
onMounted(() => {
  window.addEventListener("blur", onBlur)
  window.addEventListener("pointerdown", onOutside)
  window.addEventListener("focusin", onOutside)
  window.addEventListener("keydown", onEscape)
})
onBeforeUnmount(() => {
  window.removeEventListener("blur", onBlur)
  window.removeEventListener("pointerdown", onOutside)
  window.removeEventListener("focusin", onOutside)
  window.removeEventListener("keydown", onEscape)
})
</script>

<template>
  <div ref="container" class="model-selector relative min-w-0">
    <button ref="trigger" type="button" class="grid size-10 shrink-0 place-items-center rounded-full hover:bg-mist hover:shadow-sm focus-visible:outline-2 disabled:opacity-45" :disabled="controlDisabled" :aria-expanded="open" aria-haspopup="dialog" aria-label="选择模型" :title="loading ? '模型加载中' : selectedModel?.name ?? '选择模型'" @click="toggle">
      <img v-if="selectedFamily" :src="selectedFamily.logo" class="size-6" alt="" draggable="false">
      <svg v-else class="size-6 text-slate" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </button>
    <div v-if="open" class="absolute right-0 z-60" :class="placement === 'top' ? 'bottom-full mb-3' : 'top-full mt-3'" role="dialog" aria-label="选择模型家族和型号">
      <div v-if="listOpen && family" ref="modelList" tabindex="-1" class="w-[min(16rem,calc(100vw-6rem))] rounded-2xl border border-graphite/10 bg-paper p-1.5 outline-none" :aria-label="`${family.name}型号列表`">
        <button type="button" class="rounded-lg px-3 py-2 text-xs text-slate hover:bg-mist" @click="back">返回</button>
        <div class="max-h-[min(18rem,45dvh)] overflow-y-auto overscroll-contain [scrollbar-width:thin]">
          <button v-for="model in familyModels" :key="model.id" type="button" class="block w-full rounded-xl px-3 py-2.5 text-left text-sm hover:bg-mist focus-visible:outline-2 disabled:cursor-not-allowed disabled:opacity-40" :class="{ 'bg-mist': model.id === modelValue }" :disabled="!model.is_available" :aria-pressed="model.id === modelValue" @click="selectModel(model)">{{ model.name }}</button>
          <p v-if="!familyModels.length" class="px-3 py-4 text-xs text-slate">暂无已配置的型号</p>
        </div>
      </div>
      <svg v-else ref="dial" class="family-sectors block w-[min(12rem,calc(100vw-6rem))] rounded-full bg-paper outline-none" viewBox="0 0 200 200" tabindex="0" role="group" aria-label="选择模型家族，方向键切换，Enter 展开型号" @keydown="onKeydown">
        <path v-for="(item, position) in sectors" :key="item.id" :d="item.path" class="cursor-pointer transition-colors duration-150 motion-reduce:transition-none focus:outline-none" :fill="index === position ? '#e8e8ef' : '#f7f7f7'" stroke="white" stroke-width="2" role="button" tabindex="0" :aria-label="item.name" :aria-pressed="index === position" @pointerenter="index = position" @focus="index = position" @click="showModels(position)" @keydown.enter.prevent.stop="showModels(position)" @keydown.space.prevent.stop="showModels(position)" />
        <image v-for="item in sectors" :key="item.id" :href="item.logo" :x="item.x" :y="item.y" width="26" height="26" class="pointer-events-none" aria-hidden="true" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.model-selector {
  font-family: "Noto Sans SC Variable", "Noto Sans SC", var(--font-sans);
}
</style>
