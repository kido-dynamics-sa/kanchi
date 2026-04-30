<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-text-primary mb-1">Queue Load</h1>
        <p class="text-text-secondary">Monitor queue-level running and scheduled tasks.</p>
      </div>

      <div class="flex items-center gap-2 text-sm text-text-secondary">
        <span>Auto-refresh every 10s</span>
        <Button
          variant="outline"
          size="sm"
          class="gap-2"
          :disabled="isLoading"
          @click="fetchQueueLoad"
        >
          <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
          Refresh
        </Button>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Filter Queues</label>
          <input
            v-model="queueNameFilter"
            type="text"
            placeholder="Search by queue name"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Sort By</label>
          <select
            v-model="sortBy"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary"
          >
            <option value="queue">Queue</option>
            <option value="running_tasks">Running</option>
            <option value="scheduled_tasks">Scheduled</option>
            <option value="tracked_tasks">Tracked</option>
            <option value="workload">Workload (Running + Scheduled)</option>
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
        <p class="text-xs uppercase tracking-wide text-text-muted">Queues (Shown)</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ filteredSortedQueueLoad.length }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Running Tasks</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ filteredTotalRunning }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Scheduled Tasks</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ filteredTotalScheduled }}</p>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface overflow-hidden">
      <div class="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
        <h2 class="text-sm font-semibold text-text-primary">Queues</h2>
        <div class="flex items-center gap-4">
          <div class="hidden sm:flex items-center gap-3 text-[11px] text-text-muted">
            <span class="inline-flex items-center gap-1">
              <span class="h-2 w-2 rounded-full bg-status-warning"></span>
              Running
            </span>
            <span class="inline-flex items-center gap-1">
              <span class="h-2 w-2 rounded-full bg-status-info"></span>
              Scheduled
            </span>
          </div>
          <p class="text-xs text-text-muted" v-if="lastSampledAt">Sampled {{ formatSampledAt(lastSampledAt) }}</p>
        </div>
      </div>

      <div v-if="isLoading && queueLoad.length === 0" class="p-6 text-sm text-text-secondary">
        Loading queue metrics...
      </div>

      <div v-else-if="error" class="p-6 text-sm text-status-error">
        {{ error }}
      </div>

      <div v-else-if="filteredSortedQueueLoad.length === 0" class="p-6 text-sm text-text-secondary">
        No queue activity found for the current environment.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border-subtle text-left text-text-muted">
              <th class="px-4 py-3 font-medium">Queue</th>
              <th class="px-4 py-3 font-medium">Workload</th>
              <th class="px-4 py-3 font-medium">Running</th>
              <th class="px-4 py-3 font-medium">Scheduled</th>
              <th class="px-4 py-3 font-medium">Tracked</th>
              <th class="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filteredSortedQueueLoad"
              :key="item.queue"
              class="border-b border-border-subtle/60 last:border-b-0"
            >
              <td class="px-4 py-3 text-text-primary font-medium">{{ item.queue }}</td>
              <td class="px-4 py-3">
                <div class="w-44">
                  <div class="h-2 w-full overflow-hidden rounded-full bg-background-base">
                    <div class="flex h-full">
                      <div
                        class="h-full bg-status-warning"
                        :style="{ width: `${getRunningWidth(item)}%` }"
                      />
                      <div
                        class="h-full bg-status-info"
                        :style="{ width: `${getScheduledWidth(item)}%` }"
                      />
                    </div>
                  </div>
                  <p class="mt-1 text-[11px] text-text-muted">
                    {{ item.running_tasks + item.scheduled_tasks }} active load
                  </p>
                </div>
              </td>
              <td class="px-4 py-3 text-text-primary">{{ item.running_tasks }}</td>
              <td class="px-4 py-3 text-text-primary">{{ item.scheduled_tasks }}</td>
              <td class="px-4 py-3 text-text-secondary">{{ item.tracked_tasks }}</td>
              <td class="px-4 py-3">
                <NuxtLink
                  :to="getQueueDashboardLink(item.queue)"
                  class="text-xs font-medium text-status-info hover:underline"
                >
                  Open In Dashboard
                </NuxtLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { useApiService, type QueueLoadSummaryDTO } from '~/services/apiClient'
import type { UrlQueryState } from '~/composables/useUrlQuerySync'

const apiService = useApiService()
const environmentStore = useEnvironmentStore()

const queueLoad = ref<QueueLoadSummaryDTO[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null)
const queueNameFilter = ref('')
const sortBy = ref<'queue' | 'running_tasks' | 'scheduled_tasks' | 'tracked_tasks' | 'workload'>('workload')
const sortDirection = ref<'asc' | 'desc'>('desc')
const urlQuerySync = useUrlQuerySync()
const isInitializing = ref(true)

const lastSampledAt = computed(() => queueLoad.value[0]?.sampled_at || null)
const maxVisibleWorkload = computed(() => {
  const maxWorkload = filteredSortedQueueLoad.value.reduce((max, item) => {
    const workload = item.running_tasks + item.scheduled_tasks
    return Math.max(max, workload)
  }, 0)
  return Math.max(maxWorkload, 1)
})

const totalRunning = computed(() => {
  return queueLoad.value.reduce((sum, item) => sum + (item.running_tasks || 0), 0)
})

const totalScheduled = computed(() => {
  return queueLoad.value.reduce((sum, item) => sum + (item.scheduled_tasks || 0), 0)
})

const filteredSortedQueueLoad = computed(() => {
  const query = queueNameFilter.value.trim().toLowerCase()

  const filtered = queueLoad.value.filter((item) => {
    if (!query) return true
    return item.queue.toLowerCase().includes(query)
  })

  return [...filtered].sort((a, b) => {
    const aWorkload = a.running_tasks + a.scheduled_tasks
    const bWorkload = b.running_tasks + b.scheduled_tasks

    let base = 0
    if (sortBy.value === 'queue') {
      base = a.queue.localeCompare(b.queue)
    } else if (sortBy.value === 'workload') {
      base = aWorkload - bWorkload
    } else {
      base = (a[sortBy.value] as number) - (b[sortBy.value] as number)
    }

    return sortDirection.value === 'asc' ? base : -base
  })
})

const filteredTotalRunning = computed(() => {
  return filteredSortedQueueLoad.value.reduce((sum, item) => sum + item.running_tasks, 0)
})

const filteredTotalScheduled = computed(() => {
  return filteredSortedQueueLoad.value.reduce((sum, item) => sum + item.scheduled_tasks, 0)
})

const getCurrentState = computed((): UrlQueryState => ({
  search: queueNameFilter.value || null,
  sortBy: sortBy.value || null,
  sortOrder: sortDirection.value,
  environment: environmentStore.activeEnvironment?.id || null,
}))

const applyStateFromUrl = (state: UrlQueryState) => {
  if (state.environment && state.environment !== environmentStore.activeEnvironment?.id) {
    environmentStore.activateEnvironment(state.environment)
  }

  if (state.search) {
    queueNameFilter.value = state.search
  }

  if (
    state.sortBy &&
    ['queue', 'running_tasks', 'scheduled_tasks', 'tracked_tasks', 'workload'].includes(state.sortBy)
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

const formatSampledAt = (value: string) => {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString()
}

const getQueueDashboardLink = (queue: string) => {
  return {
    path: '/',
    query: {
      filters: `queue:is:${queue}`
    }
  }
}

const getRunningWidth = (item: QueueLoadSummaryDTO) => {
  const workload = item.running_tasks + item.scheduled_tasks
  if (workload === 0) return 0
  return Math.round((item.running_tasks / maxVisibleWorkload.value) * 100)
}

const getScheduledWidth = (item: QueueLoadSummaryDTO) => {
  const workload = item.running_tasks + item.scheduled_tasks
  if (workload === 0) return 0
  return Math.round((item.scheduled_tasks / maxVisibleWorkload.value) * 100)
}

const fetchQueueLoad = async () => {
  isLoading.value = true
  error.value = null

  try {
    queueLoad.value = await apiService.getQueueLoad()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Failed to load queue metrics.'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await fetchQueueLoad()

  isInitializing.value = false

  refreshTimer.value = setInterval(() => {
    fetchQueueLoad()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})

watch(() => environmentStore.activeEnvironment?.id, () => {
  fetchQueueLoad()
})
</script>
