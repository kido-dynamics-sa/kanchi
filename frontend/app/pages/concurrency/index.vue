<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-text-primary mb-1">Company Concurrency</h1>
        <p class="text-text-secondary">Current values from Redis keys prefixed with company_concurrency:</p>
      </div>

      <div class="flex items-center gap-2 text-sm text-text-secondary">
        <span>Auto-refresh every 10s</span>
        <Button
          variant="outline"
          size="sm"
          class="gap-2"
          :disabled="isLoading"
          @click="fetchCounters"
        >
          <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
          Refresh
        </Button>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Search</label>
          <input
            v-model="search"
            type="text"
            placeholder="Filter by key or company UUID"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Sort By</label>
          <select
            v-model="sortBy"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
          >
            <option value="value">Value</option>
            <option value="company_id">Company UUID</option>
            <option value="key">Key</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Order</label>
          <select
            v-model="sortDirection"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Entries</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ filteredEntries.length }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Total Running</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ totalValue }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Max Single Company</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ maxValue }}</p>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface overflow-hidden">
      <div class="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
        <h2 class="text-sm font-semibold text-text-primary">Redis Counters</h2>
        <p class="text-xs text-text-muted" v-if="lastUpdated">Updated {{ lastUpdated }}</p>
      </div>

      <div v-if="isLoading && entries.length === 0" class="p-6 text-sm text-text-secondary">
        Loading counters...
      </div>

      <div v-else-if="error" class="p-6 text-sm text-status-error">
        {{ error }}
      </div>

      <div v-else-if="filteredEntries.length === 0" class="p-6 text-sm text-text-secondary">
        No matching entries found.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border-subtle text-left text-text-muted">
              <th class="px-4 py-3 font-medium">Company UUID</th>
              <th class="px-4 py-3 font-medium">Current Value</th>
              <th class="px-4 py-3 font-medium">Redis Key</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in filteredEntries"
              :key="entry.key"
              class="border-b border-border-subtle/60 last:border-b-0"
            >
              <td class="px-4 py-3 text-text-primary font-medium">{{ entry.company_id }}</td>
              <td class="px-4 py-3 text-text-primary">{{ entry.value }}</td>
              <td class="px-4 py-3 text-text-secondary">{{ entry.key }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { useApiService, type CompanyConcurrencyCounterDTO } from '~/services/apiClient'

const apiService = useApiService()

const entries = ref<CompanyConcurrencyCounterDTO[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const sortBy = ref<'value' | 'company_id' | 'key'>('value')
const sortDirection = ref<'asc' | 'desc'>('desc')
const lastUpdated = ref<string | null>(null)
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null)

const filteredEntries = computed(() => {
  const query = search.value.trim().toLowerCase()

  const filtered = entries.value.filter((item) => {
    if (!query) return true
    return item.key.toLowerCase().includes(query) || item.company_id.toLowerCase().includes(query)
  })

  return [...filtered].sort((a, b) => {
    let base = 0
    if (sortBy.value === 'value') {
      base = a.value - b.value
    } else if (sortBy.value === 'company_id') {
      base = a.company_id.localeCompare(b.company_id)
    } else {
      base = a.key.localeCompare(b.key)
    }

    return sortDirection.value === 'asc' ? base : -base
  })
})

const totalValue = computed(() => filteredEntries.value.reduce((sum, item) => sum + item.value, 0))
const maxValue = computed(() => filteredEntries.value.reduce((max, item) => Math.max(max, item.value), 0))

const fetchCounters = async () => {
  isLoading.value = true
  error.value = null

  try {
    entries.value = await apiService.getCompanyConcurrency(5000)
    lastUpdated.value = new Date().toLocaleTimeString()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Failed to load company concurrency counters.'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await fetchCounters()

  refreshTimer.value = setInterval(() => {
    fetchCounters()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})
</script>
