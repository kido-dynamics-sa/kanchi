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
          <label for="queue-filter" class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Filter Queues</label>
          <input
            id="queue-filter"
            v-model="queueNameFilter"
            type="text"
            placeholder="Search by queue name"
            class="h-10 w-full rounded-md border border-border-subtle bg-background-base px-3 text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
        <div>
          <label for="queue-sort-by" class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Sort By</label>
          <select
            id="queue-sort-by"
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
          <label for="queue-sort-direction" class="mb-1 block text-xs uppercase tracking-wide text-text-muted">Order</label>
          <select
            id="queue-sort-direction"
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
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ formatNumber(filteredTotalRunning) }}</p>
      </div>
      <div class="rounded-lg border border-border-subtle bg-background-surface p-4">
        <p class="text-xs uppercase tracking-wide text-text-muted">Scheduled Tasks</p>
        <p class="mt-2 text-2xl font-semibold text-text-primary">{{ formatNumber(filteredTotalScheduled) }}</p>
      </div>
    </div>

    <div v-if="hasTieredQueues" class="rounded-lg border border-border-subtle bg-background-surface overflow-hidden">
      <div class="px-4 py-3 border-b border-border-subtle">
        <h2 class="text-sm font-semibold text-text-primary">Priority Tiers</h2>
        <p class="text-xs text-text-muted">Aggregate load per company-bucket priority tier.</p>
      </div>
      <div class="grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
        <div
          v-for="tier in tierSummary"
          :key="tier.tier"
          class="rounded-lg border border-border-subtle bg-background-base p-4"
        >
          <div class="flex items-center gap-2">
            <Badge :variant="tierBadgeVariant(tier.tier)" class="text-[10px] px-1.5 py-0">{{ tier.label }}</Badge>
          </div>
          <p class="mt-2 text-2xl font-semibold text-text-primary">{{ formatNumber(tier.running + tier.scheduled) }}</p>
          <p class="mt-1 text-[11px] text-text-muted">
            {{ formatNumber(tier.running) }} running · {{ formatNumber(tier.scheduled) }} scheduled · {{ tier.queueCount }} {{ tier.queueCount === 1 ? 'queue' : 'queues' }}
          </p>
        </div>
      </div>
    </div>

    <div class="rounded-lg border border-border-subtle bg-background-surface overflow-hidden">
      <div class="px-4 py-3 border-b border-border-subtle flex flex-wrap items-center justify-between gap-2">
        <h2 class="text-sm font-semibold text-text-primary">Queues</h2>
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex flex-wrap items-center gap-3 text-[11px] text-text-muted">
            <span class="inline-flex items-center gap-1">
              <span class="h-2 w-2 rounded-full bg-status-success"></span>
              Running
            </span>
            <span>Scheduled color shows backlog severity</span>
          </div>
          <p class="text-xs text-text-muted" v-if="lastSampledAt">Sampled {{ formatSampledAt(lastSampledAt) }}</p>
        </div>
      </div>

      <div v-if="isLoading && queueLoad.length === 0" class="p-6 text-sm text-text-secondary">
        Loading queue metrics...
      </div>

      <div v-else-if="error" class="py-16 text-center">
        <AlertCircle class="h-10 w-10 text-status-error mx-auto mb-3 opacity-40" />
        <h3 class="text-sm font-medium text-text-primary mb-1">Couldn't load queue metrics</h3>
        <p class="text-xs text-text-muted mb-6 max-w-sm mx-auto">{{ error }}</p>
        <Button size="sm" :disabled="isLoading" @click="fetchQueueLoad">
          <RefreshCw :class="['h-4 w-4 mr-1.5', isLoading ? 'animate-spin' : '']" />
          Retry
        </Button>
      </div>

      <div v-else-if="filteredSortedQueueLoad.length === 0" class="py-16 text-center">
        <Inbox class="h-10 w-10 text-text-muted mx-auto mb-3 opacity-40" />
        <h3 class="text-sm font-medium text-text-primary mb-1">No queue activity found</h3>
        <p class="text-xs text-text-muted mb-6 max-w-sm mx-auto">
          Either this environment isn't connected to a broker yet, or no tasks have run recently for the current filter.
        </p>
        <NuxtLink to="/settings/workspace">
          <Button size="sm" variant="outline">
            Review environment settings
          </Button>
        </NuxtLink>
      </div>

      <template v-else>
        <!-- Desktop / tablet table -->
        <div class="hidden md:block overflow-x-auto">
          <table class="w-full text-sm">
            <caption class="sr-only">Per-queue running, scheduled and tracked task counts, sorted by {{ sortBy }}</caption>
            <thead>
              <tr class="border-b border-border-subtle text-left text-text-muted">
                <th scope="col" class="px-4 py-3 font-medium">Queue</th>
                <th scope="col" class="px-4 py-3 font-medium">Tier</th>
                <th scope="col" class="px-4 py-3 font-medium">Workload</th>
                <th scope="col" class="px-4 py-3 font-medium">Running</th>
                <th scope="col" class="px-4 py-3 font-medium">Scheduled</th>
                <th scope="col" class="px-4 py-3 font-medium">
                  <TooltipProvider :delay-duration="200">
                    <TooltipRoot>
                      <TooltipTrigger as-child>
                        <span class="inline-flex items-center gap-1 cursor-default">
                          Tracked
                          <Info class="h-3 w-3" aria-hidden="true" />
                        </span>
                      </TooltipTrigger>
                      <TooltipContent class="max-w-xs text-[11px]">
                        Total tasks tracked for this queue right now, across every state (running, scheduled, success, failed) — not just active load.
                      </TooltipContent>
                    </TooltipRoot>
                  </TooltipProvider>
                </th>
                <th scope="col" class="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredSortedQueueLoad"
                :key="item.queue"
                class="border-b border-border-subtle/60 last:border-b-0"
              >
                <td class="px-4 py-3 text-text-primary font-medium">
                  <span class="block max-w-[220px] truncate" :title="item.queue">{{ item.queue }}</span>
                </td>
                <td class="px-4 py-3">
                  <Badge v-if="item.tier" :variant="tierBadgeVariant(item.tier)" class="text-[10px] px-1.5 py-0">{{ formatTier(item.tier) }}</Badge>
                  <span v-else class="text-text-secondary">—</span>
                </td>
                <td class="px-4 py-3">
                  <div class="w-44">
                    <div class="h-2 w-full overflow-hidden rounded-full bg-background-base">
                      <div class="flex h-full">
                        <div
                          class="h-full bg-status-success"
                          :style="{ width: `${getRunningWidth(item)}%` }"
                        />
                        <div
                          class="h-full"
                          :class="severityMeta(item).barClass"
                          :style="{ width: `${getScheduledWidth(item)}%` }"
                        />
                      </div>
                    </div>
                    <div class="mt-1.5 flex items-center gap-1.5">
                      <Badge :variant="severityMeta(item).badgeVariant" class="text-[10px] px-1.5 py-0">{{ severityMeta(item).label }}</Badge>
                      <span class="text-[11px] text-text-muted">{{ formatNumber(item.running_tasks + item.scheduled_tasks) }} active load</span>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3 text-text-primary">{{ formatNumber(item.running_tasks) }}</td>
                <td class="px-4 py-3 text-text-primary">{{ formatNumber(item.scheduled_tasks) }}</td>
                <td class="px-4 py-3 text-text-secondary">{{ formatNumber(item.tracked_tasks) }}</td>
                <td class="px-4 py-3">
                  <NuxtLink
                    :to="getQueueActionLink(item)"
                    class="inline-flex items-center gap-1 text-xs font-medium text-status-info hover:underline"
                  >
                    {{ getSeverity(item) === 'healthy' ? 'Open In Dashboard' : 'Investigate In Dashboard' }}
                    <ArrowRight class="h-3 w-3" />
                  </NuxtLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile card list -->
        <div class="md:hidden divide-y divide-border-subtle">
          <div
            v-for="item in filteredSortedQueueLoad"
            :key="item.queue"
            class="p-4 space-y-3"
          >
            <div class="flex items-start justify-between gap-3">
              <p class="min-w-0 flex-1 truncate font-medium text-text-primary" :title="item.queue">{{ item.queue }}</p>
            </div>
            <div class="flex items-center gap-1.5">
              <Badge v-if="item.tier" :variant="tierBadgeVariant(item.tier)" class="text-[10px] px-1.5 py-0">{{ formatTier(item.tier) }}</Badge>
              <Badge :variant="severityMeta(item).badgeVariant" class="text-[10px] px-1.5 py-0">{{ severityMeta(item).label }}</Badge>
            </div>
            <div class="h-2 w-full overflow-hidden rounded-full bg-background-base">
              <div class="flex h-full">
                <div class="h-full bg-status-success" :style="{ width: `${getRunningWidth(item)}%` }" />
                <div class="h-full" :class="severityMeta(item).barClass" :style="{ width: `${getScheduledWidth(item)}%` }" />
              </div>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center">
              <div>
                <p class="text-[10px] uppercase tracking-wide text-text-muted">Running</p>
                <p class="text-sm font-medium text-text-primary">{{ formatNumber(item.running_tasks) }}</p>
              </div>
              <div>
                <p class="text-[10px] uppercase tracking-wide text-text-muted">Scheduled</p>
                <p class="text-sm font-medium text-text-primary">{{ formatNumber(item.scheduled_tasks) }}</p>
              </div>
              <div>
                <p class="text-[10px] uppercase tracking-wide text-text-muted">Tracked</p>
                <p class="text-sm font-medium text-text-primary">{{ formatNumber(item.tracked_tasks) }}</p>
              </div>
            </div>
            <NuxtLink
              :to="getQueueActionLink(item)"
              class="flex items-center justify-center gap-1.5 rounded-md border border-border-subtle bg-background-base py-3 text-xs font-medium text-status-info active:bg-background-hover"
            >
              {{ getSeverity(item) === 'healthy' ? 'Open In Dashboard' : 'Investigate In Dashboard' }}
              <ArrowRight class="h-3.5 w-3.5" />
            </NuxtLink>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RefreshCw, AlertCircle, Inbox, ArrowRight, Info } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Badge, type BadgeVariants } from '~/components/ui/badge'
import { TooltipProvider, TooltipRoot, TooltipTrigger, TooltipContent } from '~/components/ui/tooltip'
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

const TIERS = ['fast', 'medium', 'slow'] as const

// Distinct hues from severity (success/warning/error) so a tier chip is never mistaken for a health signal.
const TIER_BADGE_VARIANT: Record<string, BadgeVariants['variant']> = {
  fast: 'running',
  medium: 'received',
  slow: 'revoked',
}

type Severity = 'healthy' | 'elevated' | 'critical'

// Workload bands are fixed and absolute, not relative to the busiest queue currently on screen —
// otherwise a system-wide backlog just redefines "100%" and every bar looks proportionally fine.
const SEVERITY_THRESHOLDS: Record<'elevated' | 'critical', number> = {
  elevated: 20,
  critical: 100,
}

const SEVERITY_META: Record<Severity, { label: string; badgeVariant: BadgeVariants['variant']; barClass: string }> = {
  healthy: { label: 'Healthy', badgeVariant: 'success', barClass: 'bg-status-info' },
  elevated: { label: 'Elevated', badgeVariant: 'pending', barClass: 'bg-status-warning' },
  critical: { label: 'Critical', badgeVariant: 'failed', barClass: 'bg-status-error' },
}

const formatTier = (tier: string) => tier.charAt(0).toUpperCase() + tier.slice(1)
const tierBadgeVariant = (tier: string): BadgeVariants['variant'] => TIER_BADGE_VARIANT[tier] ?? 'outline'
const formatNumber = (value: number) => value.toLocaleString()

const getSeverity = (item: QueueLoadSummaryDTO): Severity => {
  const workload = item.running_tasks + item.scheduled_tasks
  if (workload >= SEVERITY_THRESHOLDS.critical) return 'critical'
  if (workload >= SEVERITY_THRESHOLDS.elevated) return 'elevated'
  return 'healthy'
}

const severityMeta = (item: QueueLoadSummaryDTO) => SEVERITY_META[getSeverity(item)]

const tierSummary = computed(() => {
  return TIERS.map((tier) => {
    const items = queueLoad.value.filter((item) => item.tier === tier)
    return {
      tier,
      label: formatTier(tier),
      queueCount: items.length,
      running: items.reduce((sum, item) => sum + item.running_tasks, 0),
      scheduled: items.reduce((sum, item) => sum + item.scheduled_tasks, 0),
    }
  })
})

const hasTieredQueues = computed(() => tierSummary.value.some((tier) => tier.queueCount > 0))

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

// Healthy queues just link to the dashboard filtered to this queue. Queues past the healthy
// band jump straight to the tasks that actually need attention (failed/retry/orphaned) for that
// queue, since retry/revoke already live on the task detail and task list screens.
const getQueueActionLink = (item: QueueLoadSummaryDTO) => {
  if (getSeverity(item) === 'healthy') {
    return {
      path: '/',
      query: { filters: `queue:is:${item.queue}` },
    }
  }
  return {
    path: '/',
    query: { filters: `queue:is:${item.queue};state:in:FAILED,RETRY,ORPHANED` },
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
