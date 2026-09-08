import { ref, watch } from "vue"
import { defineStore } from "pinia"

import { getModelProvider, listModelProviders } from "@/api/model"
import { useAuthStore } from "@/stores/useAuthStore"
import type { ModelProvider, ModelProviderId, ModelProviderSummary } from "@/types/model"

export const useModelProviderStore = defineStore("modelProviders", () => {
  const auth = useAuthStore()
  const providers = ref<ModelProviderSummary[]>([])
  const details = ref<Partial<Record<ModelProviderId, ModelProvider>>>({})
  const loaded = ref(false)
  let revision = 0
  let pendingList: Promise<void> | null = null

  watch(() => auth.accessToken, () => {
    revision++
    providers.value = []
    details.value = {}
    loaded.value = false
    pendingList = null
  }, { flush: "sync" })

  function assertSession(expected: number) {
    if (revision !== expected || !auth.accessToken) throw new Error("登录状态已改变")
  }

  async function loadProviders() {
    const version = revision
    assertSession(version)
    if (loaded.value) return
    if (pendingList) return pendingList
    pendingList = (async () => {
      try {
        const result = await listModelProviders()
        assertSession(version)
        providers.value = result
        loaded.value = true
      } finally {
        if (revision === version) pendingList = null
      }
    })()
    return pendingList
  }

  async function loadProvider(id: ModelProviderId) {
    const version = revision
    assertSession(version)
    await loadProviders()
    assertSession(version)
    if (details.value[id]) return details.value[id]
    if (!providers.value.some(item => item.provider_id === id)) return undefined
    const detail = await getModelProvider(id)
    assertSession(version)
    details.value[id] = detail
    return detail
  }

  function saved(id: ModelProviderId, provider: ModelProvider) {
    details.value[id] = provider
    const summary: ModelProviderSummary = {
      provider_id: id, name: provider.name, is_enabled: provider.is_enabled, has_api_key: provider.has_api_key
    }
    providers.value = [...providers.value.filter(item => item.provider_id !== id), summary]
  }

  return { providers, details, loadProviders, loadProvider, saved }
})
