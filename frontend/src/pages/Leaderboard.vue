<template>
	<div class="h-full">
		<!-- Header -->
		<header
			class="sticky top-0 z-10 flex flex-col gap-3 border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<!-- Top row: Breadcrumbs and Seasonal Rewards -->
			<div class="flex items-center justify-between">
				<Breadcrumbs :items="breadcrumbs" />
				<button
					class="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-gray-900 rounded-md hover:bg-gray-800 transition-colors"
					@click="showRewardsModal = true"
				>
					<Gift class="h-4 w-4 stroke-1.5" />
					{{ __('Seasonal Rewards') }}
				</button>
			</div>

			<!-- Filters Row -->
			<div class="flex flex-wrap items-center justify-between gap-3">
				<div class="flex items-center gap-3">
					<!-- Category Filter -->
					<Select
						v-model="category"
						:options="categoryOptions"
						class="w-32"
					/>
					<!-- Period Tabs -->
					<TabButtons
						:buttons="periodButtons"
						v-model="period"
						class="w-fit"
					/>
				</div>
				<!-- Season Info -->
				<div v-if="seasonInfo" class="flex items-center gap-2 px-3 py-1.5 bg-surface-gray-1 rounded-lg">
					<Trophy class="h-4 w-4 stroke-1.5 text-amber-500" />
					<span class="text-sm font-medium text-ink-gray-9">{{ __('Season') }} {{ seasonInfo.season }}</span>
					<span class="text-ink-gray-3">•</span>
					<Clock class="h-3.5 w-3.5 stroke-1.5 text-ink-gray-5" />
					<span class="text-sm text-ink-gray-7">{{ seasonInfo.days_remaining }} {{ __('days left') }}</span>
				</div>
			</div>
		</header>

		<!-- Content -->
		<div class="h-[calc(100vh-130px)] flex flex-col lg:flex-row">
			<!-- Left Panel: Leaderboard Table -->
			<div class="flex-1 lg:w-3/5 border-r border-outline-gray-1 flex flex-col">
				<!-- Hall of Fame -->
				<div
					v-if="period === 'Season' && hallOfFame.length"
					class="px-4 py-3 border-b border-outline-gray-1 bg-surface-gray-1"
				>
					<div class="flex items-center gap-2 mb-2">
						<Crown class="h-4 w-4 stroke-1.5 text-amber-500" />
						<span class="text-xs font-medium text-ink-gray-7 uppercase tracking-wide">{{ __('Hall of Fame') }}</span>
					</div>
					<div class="flex flex-wrap gap-2">
						<div
							v-for="champion in hallOfFame"
							:key="champion.season"
							class="flex items-center gap-2 px-2.5 py-1 bg-surface-white rounded border border-outline-gray-2 text-sm"
						>
							<img
								v-if="champion.user_image"
								:src="champion.user_image"
								class="h-5 w-5 rounded-full object-cover"
							/>
							<span class="text-ink-gray-7">{{ champion.full_name }}</span>
							<span class="text-xs text-ink-gray-4">S{{ champion.season }}</span>
						</div>
					</div>
				</div>

				<!-- Loading -->
				<div
					v-if="leaderboard.loading"
					class="flex-1 flex items-center justify-center"
				>
					<div class="text-ink-gray-5 text-sm">{{ __('Loading...') }}</div>
				</div>

				<!-- Empty State -->
				<div
					v-else-if="!leaderboardData.length"
					class="flex-1 flex flex-col items-center justify-center p-6"
				>
					<div class="text-ink-gray-5 text-sm">
						{{ __('No rankings yet') }}
					</div>
				</div>

				<!-- Leaderboard Panel -->
				<LeaderboardPanel
					v-else
					:data="leaderboardData"
					:currentUser="currentUser"
					:currentUserData="currentUserData"
					:page="page"
					:totalPages="totalPages"
					@view="handleViewUser"
					@page-change="handlePageChange"
				/>
			</div>

			<!-- Right Panel: User Stats (Desktop) -->
			<div class="hidden lg:block lg:w-2/5 h-full">
				<UserStatsPanel
					:stats="selectedUserStats"
					:loading="userStats.loading"
					:isOwnStats="isViewingOwnStats"
					@show-my-stats="showMyStats"
				/>
			</div>
		</div>

		<!-- Mobile: Stats Modal -->
		<Dialog
			v-model="showStatsModal"
			:options="{ title: __('User Stats'), size: 'lg' }"
		>
			<template #body-content>
				<UserStatsPanel
					:stats="selectedUserStats"
					:loading="userStats.loading"
					:isOwnStats="isViewingOwnStats"
					@show-my-stats="showMyStats"
					class="max-h-[70vh] overflow-y-auto"
				/>
			</template>
		</Dialog>

		<!-- Seasonal Rewards Modal -->
		<Dialog
			v-model="showRewardsModal"
			:options="{ title: __('Seasonal Rewards'), size: 'lg' }"
		>
			<template #body-content>
				<div class="flex flex-col items-center justify-center py-8 text-center">
					<div class="text-ink-gray-5 mb-2">
						{{ __('Coming Soon') }}
					</div>
					<p class="text-sm text-ink-gray-4 max-w-xs">
						{{ __('Seasonal rewards will be announced soon. Stay tuned for exciting prizes!') }}
					</p>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, computed, watch, inject, onMounted } from 'vue'
import {
	Breadcrumbs,
	Button,
	Select,
	TabButtons,
	Dialog,
	createResource,
	usePageMeta
} from 'frappe-ui'
import { Trophy, Crown, Gift, Clock } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import LeaderboardPanel from '@/components/leaderboard/LeaderboardPanel.vue'
import UserStatsPanel from '@/components/leaderboard/UserStatsPanel.vue'

const { brand } = sessionStore()
const $user = inject('$user')

// State
const category = ref('student')
const period = ref('Season')
const page = ref(1)
const selectedUser = ref(null)
const showStatsModal = ref(false)
const showRewardsModal = ref(false)

// Options
const categoryOptions = [
	{ label: __('Students'), value: 'student' },
	{ label: __('Instructors'), value: 'instructor' }
]

const periodButtons = [
	{ label: 'Season' },
	{ label: 'Monthly' },
	{ label: 'Weekly' }
]

// Map period label to API period value
const periodMap = {
	'Season': 'season',
	'Monthly': 'monthly',
	'Weekly': 'weekly'
}

const periodApiValue = computed(() => periodMap[period.value] || 'season')

// Computed
const currentUser = computed(() => $user?.data?.name || '')

const isViewingOwnStats = computed(() => {
	return !selectedUser.value || selectedUser.value === currentUser.value
})

// Resources
const leaderboard = createResource({
	url: 'lms.lms.api.get_leaderboard',
	cache: ['leaderboard', category.value, period.value, page.value],
	makeParams() {
		return {
			category: category.value,
			period: periodApiValue.value,
			page: page.value,
			limit: 25
		}
	},
	auto: true
})

const userStats = createResource({
	url: 'lms.lms.api.get_user_stats',
	makeParams() {
		return {
			user: selectedUser.value || currentUser.value || undefined
		}
	},
	auto: false
})

// Computed from resources
const leaderboardData = computed(() => leaderboard.data?.data || [])
const totalPages = computed(() => leaderboard.data?.total_pages || 1)
const currentUserData = computed(() => leaderboard.data?.current_user_data || null)
const selectedUserStats = computed(() => userStats.data || null)
const seasonInfo = computed(() => leaderboard.data?.season_info || null)
const hallOfFame = computed(() => leaderboard.data?.hall_of_fame || [])

// Handlers
const handleViewUser = (user) => {
	selectedUser.value = user.user

	// On mobile, show modal
	if (window.innerWidth < 1024) {
		showStatsModal.value = true
	}
}

const showMyStats = () => {
	selectedUser.value = null
}

const handlePageChange = (newPage) => {
	page.value = newPage
}

// Watchers
watch([category, period], () => {
	page.value = 1
	leaderboard.reload()
})

watch(page, () => {
	leaderboard.reload()
})

// Watch selectedUser to reload stats
watch(selectedUser, () => {
	const targetUser = selectedUser.value || currentUser.value
	if (targetUser) {
		userStats.fetch()
	}
})

// Watch for user data becoming available (async injection)
watch(() => $user?.data?.name, (newVal) => {
	if (newVal && !selectedUser.value && !userStats.data) {
		userStats.fetch()
	}
}, { immediate: true })

// Load own stats on mount
onMounted(() => {
	if (currentUser.value) {
		userStats.fetch()
	}
})

// Breadcrumbs
const breadcrumbs = computed(() => [
	{
		label: __('Leaderboard'),
		route: { name: 'Leaderboard' }
	}
])

// Page meta
usePageMeta(() => ({
	title: __('Leaderboard'),
	icon: brand.favicon
}))
</script>
