<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-text-primary mb-1">Workers</h1>
        <p class="text-text-secondary">Inspect all known workers and their available system details.</p>
      </div>

      <div class="flex items-center gap-2 text-sm text-text-secondary">
        <span>Auto-refresh every 15s</span>
        <Button
          variant="outline"
          size="sm"
          class="gap-2"
          :disabled="isLoading"
          @click="refresh"
        >
          <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
          Refresh
        </Button>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Filter Workers</label>
          <input
            v-model="workerNameFilter"
            type="text"
            placeholder="Search by hostname"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Status</label>
          <select
            v-model="statusFilter"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
          >
            <option value="all">All</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="active">Active</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Sort</label>
          <div class="grid grid-cols-2 gap-2">
            <select
              v-model="sortBy"
              class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
            >
              <option value="hostname">Hostname</option>
              <option value="status">Status</option>
              <option value="active_tasks">Active Tasks</option>
              <option value="processed_tasks">Processed Tasks</option>
              <option value="timestamp">Last Seen</option>
            </select>
            <select
              v-model="sortDirection"
              class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
            >
              <option value="asc">Asc</option>
              <option value="desc">Desc</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-4">
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Workers</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ filteredWorkers.length }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Online</p>
        <p class="mt-2 text-2xl font-semibold text-status-success">{{ onlineCount }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Active Tasks</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ totalActiveTasks }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Processed Tasks</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ totalProcessedTasks }}</p>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface overflow-hidden">
      <div class="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
        <h2 class="text-sm font-semibold text-text-primary">Worker Inventory</h2>
        <p class="text-xs text-text-muted">Showing all known workers (live + historical)</p>
      </div>

      <div v-if="isLoading && workers.length === 0" class="p-6 text-sm text-text-secondary">
        Loading workers...
      </div>

      <div v-else-if="error" class="p-6 text-sm text-status-error">
        {{ error }}
      </div>

      <div v-else-if="filteredWorkers.length === 0" class="p-6 text-sm text-text-secondary">
        No workers match the current filters.
      </div>

      <div v-else class="divide-y divide-border-subtle">
        <details
          v-for="worker in filteredWorkers"
          :key="worker.hostname"
          class="group"
        >
          <summary class="cursor-pointer list-none px-4 py-3 hover:bg-background-hover/40">
            <div class="grid grid-cols-1 md:grid-cols-6 gap-3 items-center">
              <div class="md:col-span-2">
                <p class="font-medium text-text-primary">{{ worker.hostname }}</p>
                <p class="text-xs text-text-muted">{{ worker.sw_sys || 'OS unknown' }}</p>
              </div>
              <div>
                <Badge :variant="statusBadgeVariant(worker.status)">{{ worker.status || 'unknown' }}</Badge>
              </div>
              <div class="text-sm text-text-primary">{{ worker.active_tasks || 0 }} active</div>
              <div class="text-sm text-text-primary">{{ worker.processed_tasks || 0 }} processed</div>
              <div class="text-xs text-text-muted">{{ formatTimestamp(worker.timestamp) }}</div>
            </div>
          </summary>

          <div class="px-4 pb-4 pt-2 bg-background-base/30">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="rounded-md border border-border-subtle bg-background-surface p-3">
                <h3 class="text-xs uppercase tracking-wide text-text-muted mb-2">System Details</h3>
                <dl class="space-y-1 text-sm">
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-muted">Software</dt>
                    <dd class="text-text-primary">{{ worker.sw_ident || 'unknown' }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-muted">Version</dt>
                    <dd class="text-text-primary">{{ worker.sw_ver || 'unknown' }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-muted">System</dt>
                    <dd class="text-text-primary">{{ worker.sw_sys || 'unknown' }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-muted">Clock Freq</dt>
                    <dd class="text-text-primary">{{ formatFrequency(worker.freq) }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-muted">Load Avg</dt>
                    <dd class="text-text-primary">{{ formatLoadAvg(worker.loadavg) }}</dd>
                  </div>
                  <div class="pt-1">
                    <dt class="text-text-muted mb-1">Subscribed Queues</dt>
                    <dd>
                      <div
                        v-if="getSubscribedQueues(worker).length > 0"
                        class="flex flex-wrap gap-1"
                      >
                        <span
                          v-for="queue in getSubscribedQueues(worker)"
                          :key="`${worker.hostname}-${queue}`"
                          class="inline-flex items-center rounded border border-border-subtle px-1.5 py-0.5 text-xs text-text-primary"
                        >
                          {{ queue }}
                        </span>
                      </div>
                      <span v-else class="text-text-muted">No queue subscriptions reported</span>
                    </dd>
                  </div>
                </dl>
              </div>

              <div class="rounded-md border border-border-subtle bg-background-surface p-3">
                <h3 class="text-xs uppercase tracking-wide text-text-muted mb-2">Recent Worker Events</h3>
                <div v-if="workerEventsByHostname(worker.hostname).length === 0" class="text-xs text-text-muted">
                  No recent events recorded.
                </div>
                <ul v-else class="space-y-2">
                  <li
                    v-for="event in workerEventsByHostname(worker.hostname).slice(0, 5)"
                    :key="`${event.hostname}-${event.timestamp}-${event.event_type}`"
                    class="text-xs text-text-secondary"
                  >
                    <span class="font-medium text-text-primary">{{ event.event_type }}</span>
                    <span class="mx-1">·</span>
                    <span>{{ formatTimestamp(event.timestamp) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import type { UrlQueryState } from '~/composables/useUrlQuerySync'

const workersStore = useWorkersStore()
const environmentStore = useEnvironmentStore()
const urlQuerySync = useUrlQuerySync()

const workerNameFilter = ref('')
const statusFilter = ref<'all' | 'online' | 'offline' | 'active' | 'unknown'>('online')
const sortBy = ref<'hostname' | 'status' | 'active_tasks' | 'processed_tasks' | 'timestamp'>('hostname')
const sortDirection = ref<'asc' | 'desc'>('asc')

const isInitializing = ref(true)
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null)

const workers = computed(() => workersStore.workers)
const recentWorkerEvents = computed(() => workersStore.recentWorkerEvents)
const isLoading = computed(() => workersStore.isLoading)
const error = computed(() => workersStore.error)

const filteredWorkers = computed(() => {
  const query = workerNameFilter.value.trim().toLowerCase()

  const filtered = workers.value.filter((worker) => {
    const nameMatches = !query || worker.hostname.toLowerCase().includes(query)
    const statusMatches = statusFilter.value === 'all' || worker.status === statusFilter.value
    return nameMatches && statusMatches
  })

  return [...filtered].sort((a, b) => {
    let base = 0
    if (sortBy.value === 'hostname') {
      base = a.hostname.localeCompare(b.hostname)
    } else if (sortBy.value === 'status') {
      base = (a.status || '').localeCompare(b.status || '')
    } else if (sortBy.value === 'timestamp') {
      const aTime = a.timestamp ? Date.parse(a.timestamp) : 0
      const bTime = b.timestamp ? Date.parse(b.timestamp) : 0
      base = aTime - bTime
    } else {
      base = (a[sortBy.value] || 0) - (b[sortBy.value] || 0)
    }

    return sortDirection.value === 'asc' ? base : -base
  })
})

const onlineCount = computed(() => workers.value.filter((w) => w.status === 'online').length)
const totalActiveTasks = computed(() => workers.value.reduce((sum, w) => sum + (w.active_tasks || 0), 0))
const totalProcessedTasks = computed(() => workers.value.reduce((sum, w) => sum + (w.processed_tasks || 0), 0))

const workerEventsByHostname = (hostname: string) => {
  return recentWorkerEvents.value.filter((event: any) => event.hostname === hostname)
}

const statusBadgeVariant = (status?: string) => {
  if (status === 'online' || status === 'active') return 'success'
  if (status === 'offline') return 'secondary'
  return 'outline'
}

const formatTimestamp = (value?: string) => {
  if (!value) return 'unknown'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

const formatFrequency = (value?: number) => {
  if (value === null || value === undefined) return 'unknown'
  return `${value}`
}

const formatLoadAvg = (value?: number[]) => {
  if (!value || value.length === 0) return 'unknown'
  return value.map((v) => Number(v).toFixed(2)).join(', ')
}

const getSubscribedQueues = (worker: any): string[] => {
  const queues = worker?.queues_subscribed
  return Array.isArray(queues) ? queues : []
}

const refresh = async () => {
  await Promise.all([
    workersStore.fetchWorkers(),
    workersStore.fetchRecentWorkerEvents(200),
  ])
}

const getCurrentState = computed((): UrlQueryState => ({
  search: workerNameFilter.value || null,
  filters: statusFilter.value !== 'all' ? statusFilter.value : null,
  sortBy: sortBy.value,
  sortOrder: sortDirection.value,
  environment: environmentStore.activeEnvironment?.id || null,
}))

const applyStateFromUrl = (state: UrlQueryState) => {
  if (state.environment && state.environment !== environmentStore.activeEnvironment?.id) {
    environmentStore.activateEnvironment(state.environment)
  }

  if (state.search) workerNameFilter.value = state.search

  if (state.filters && ['all', 'online', 'offline', 'active', 'unknown'].includes(state.filters)) {
    statusFilter.value = state.filters as typeof statusFilter.value
  }

  if (
    state.sortBy &&
    ['hostname', 'status', 'active_tasks', 'processed_tasks', 'timestamp'].includes(state.sortBy)
  ) {
    sortBy.value = state.sortBy as typeof sortBy.value
  }

  if (state.sortOrder && ['asc', 'desc'].includes(state.sortOrder)) {
    sortDirection.value = state.sortOrder
  }
}

urlQuerySync.initializeFromUrl((state) => {
  applyStateFromUrl(state)
})

let syncTimeout: ReturnType<typeof setTimeout> | null = null
watch(getCurrentState, (newState) => {
  if (isInitializing.value) return

  if (syncTimeout) clearTimeout(syncTimeout)
  syncTimeout = setTimeout(() => {
    urlQuerySync.updateQueryParams(newState, true)
  }, 300)
}, { deep: true })

watch(() => environmentStore.activeEnvironment?.id, () => {
  refresh()
})

onMounted(async () => {
  await refresh()
  isInitializing.value = false

  refreshTimer.value = setInterval(() => {
    refresh()
  }, 15000)
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})
</script>
