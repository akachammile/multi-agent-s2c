import { computed, onScopeDispose, reactive, ref, watch } from "vue"
import { message } from "ant-design-vue"

import { discoverProviderModels, saveModelProvider, testProviderConnection } from "@/api/model"
import { useModelProviderStore } from "@/stores/useModelProviderStore"
import { useAuthStore } from "@/stores/useAuthStore"
import type { ModelProviderId, ModelSettingsRequest, SettingsModel } from "@/types/model"

interface ModelDraft extends ModelSettingsRequest {
  initialized?: boolean
  key: string
  keyEdited: boolean
  hasKey: boolean
}

export function useModelSettings() {
  const auth = useAuthStore()
  const providerStore = useModelProviderStore()
  const selected = ref<ModelProviderId>("deepseek")
  const drafts = reactive<Partial<Record<ModelProviderId, ModelDraft>>>({})
  const loading = ref(true)
  const loadError = ref(false)
  const busy = ref<"save" | "discover" | "test" | null>(null)
  const candidates = ref<SettingsModel[] | null>(null)
  const chosen = ref<string[]>([])
  let disposed = false
  let sessionVersion = 0
  let loadVersion = 0
  onScopeDispose(() => { disposed = true })

  watch(() => auth.accessToken, () => {
    sessionVersion++
    loadVersion++
    selected.value = "deepseek"
    for (const id of Object.keys(drafts) as ModelProviderId[]) delete drafts[id]
    candidates.value = null
    chosen.value = []
    busy.value = null
    loading.value = true
    loadError.value = false
  }, { flush: "sync" })

  function draftFor(id: ModelProviderId): ModelDraft {
    return drafts[id] ?? (drafts[id] = {
      base_url: "", is_enabled: false, models: [], key: "", keyEdited: false, hasKey: false
    })
  }
  const draft = computed(() => draftFor(selected.value))
  const blocked = computed(() => loading.value || loadError.value || busy.value !== null)

  async function load() {
    const version = ++loadVersion
    const id = selected.value
    loading.value = true
    loadError.value = false
    if (!auth.accessToken) { loading.value = false; loadError.value = true; return }
    try {
      const provider = await providerStore.loadProvider(id)
      if (disposed || version !== loadVersion) return
      if (provider && !drafts[id]?.initialized) {
        drafts[id] = {
          base_url: provider.base_url, is_enabled: provider.is_enabled,
          models: provider.enabled_models.map(({ model_id, capabilities }) => ({ model_id, capabilities: capabilities ?? [] })),
          key: "", keyEdited: false, hasKey: provider.has_api_key, initialized: true
        }
      }
    } catch (error) {
      if (disposed || version !== loadVersion) return
      loadError.value = true
      void message.error(error instanceof Error ? error.message : "加载失败")
    } finally {
      if (version === loadVersion) loading.value = false
    }
  }

  function request(): ModelSettingsRequest {
    const value = draft.value
    return {
      base_url: value.base_url, is_enabled: value.is_enabled,
      models: value.models.map(({ model_id, capabilities }) => ({ model_id, capabilities: [...capabilities] })),
      ...(value.keyEdited ? { api_key: value.key } : {})
    }
  }

  async function act(action: "save" | "discover" | "test") {
    if (blocked.value) return
    if (!draft.value.base_url.trim()) { void message.error("请输入 Base URL"); return }
    if (action === "test" && !draft.value.models.length) {
      void message.error("请先获取并选择聊天模型")
      return
    }
    const id = selected.value
    const version = sessionVersion
    const current = () => !disposed && version === sessionVersion
    const body = request()
    busy.value = action
    try {
      if (action === "save") {
        const result = await saveModelProvider(id, body)
        if (!current()) return
        const value = draftFor(id)
        if (value.keyEdited) value.hasKey = Boolean(value.key)
        value.key = ""
        value.keyEdited = false
        value.initialized = true
        providerStore.saved(id, {
          provider_id: id, name: providerStore.details[id]?.name ?? id,
          base_url: body.base_url, is_enabled: body.is_enabled, has_api_key: value.hasKey,
          enabled_models: body.models
        })
        void (result.cache_refreshed ? message.success("已保存") : message.warning("已保存，模型缓存刷新失败"))
      } else if (action === "discover") {
        const result = await discoverProviderModels(id, body)
        if (!current()) return
        const merged = new Map(body.models.map(model => [model.model_id, model]))
        for (const model of result) merged.set(model.model_id, model)
        candidates.value = [...merged.values()]
        chosen.value = body.models.map(model => model.model_id)
      } else {
        const result = await testProviderConnection(id, body)
        if (!current()) return
        if (result.success) void message.success(`连接成功 · ${Math.round(result.elapsed_ms)} ms`)
        else void message.error(`连接失败：${result.error ?? "unknown"}${result.status_code ? ` (${result.status_code})` : ""}`)
      }
    } catch (error) {
      if (current()) void message.error(error instanceof Error ? error.message : "操作失败")
    } finally {
      if (current()) busy.value = null
    }
  }

  function confirmModels() {
    draft.value.models = (candidates.value ?? []).filter(model => chosen.value.includes(model.model_id))
    candidates.value = null
  }

  watch([selected, () => auth.accessToken], load, { immediate: true })
  return { selected, draft, blocked, loading, loadError, busy, candidates, chosen, load, act, confirmModels }
}
