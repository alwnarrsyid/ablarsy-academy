<template>
	<div class="flex flex-col h-full bg-surface-white overflow-y-auto">
		<!-- Header -->
		<div class="sticky top-0 z-10 bg-surface-white border-b border-outline-gray-2 px-4 py-3">
			<div class="flex items-center justify-between">
				<h3 class="text-base font-medium text-ink-gray-9">
					{{ isOwnStats ? __('Your Stats') : __('User Stats') }}
				</h3>
				<Button
					v-if="!isOwnStats"
					variant="outline"
					size="sm"
					@click="$emit('show-my-stats')"
				>
					<template #prefix>
						<User class="h-4 w-4 stroke-1.5" />
					</template>
					{{ __('My Stats') }}
				</Button>
			</div>
		</div>

		<!-- Loading State -->
		<div v-if="loading && !stats" class="flex-1 flex items-center justify-center">
			<div class="text-ink-gray-5 text-sm">{{ __('Loading...') }}</div>
		</div>

		<!-- Login Prompt (Guest) -->
		<div
			v-else-if="isGuest"
			class="flex-1 flex flex-col items-center justify-center p-6 text-center"
		>
			<div class="text-ink-gray-5 mb-4">
				{{ __('Login to see your stats') }}
			</div>
			<Button variant="outline" size="sm" @click="goToLogin">
				{{ __('Login') }}
			</Button>
		</div>

		<!-- Stats Content -->
		<div v-else-if="stats" class="flex-1 p-4 space-y-4" :class="{ 'opacity-50': loading }">
			<!-- User Info -->
			<div class="flex items-center gap-3 pb-4 border-b border-outline-gray-1">
				<img
					v-if="stats.user_info?.user_image"
					:src="stats.user_info.user_image"
					:alt="stats.user_info.full_name"
					class="h-10 w-10 rounded-full object-cover"
				/>
				<div
					v-else
					class="h-10 w-10 rounded-full bg-surface-gray-3 flex items-center justify-center"
				>
					<span class="text-sm font-medium text-ink-gray-5">{{ getInitials(stats.user_info?.full_name) }}</span>
				</div>
				<div class="flex-1 min-w-0">
					<div class="text-sm font-medium text-ink-gray-9 truncate">
						{{ stats.user_info?.full_name }}
					</div>
					<div class="flex items-center gap-1.5 text-xs text-ink-gray-5">
						<Trophy class="h-3 w-3 stroke-1.5 text-amber-500" />
						<span>{{ __('Rank') }} #{{ stats?.user_info?.rank || '-' }}</span>
					</div>
				</div>
			</div>

			<!-- Total Score -->
			<div class="text-center py-3">
				<div class="text-2xl font-semibold text-ink-gray-9">
					{{ formatNumber(stats.total_score) }}
				</div>
				<div class="text-xs text-ink-gray-5">{{ __('Total Points') }}</div>
			</div>

			<!-- Score Breakdown -->
			<div class="bg-surface-gray-1 rounded-lg p-4">
				<div class="text-xs font-medium text-ink-gray-7 uppercase tracking-wide mb-3">
					{{ __('Score Breakdown') }}
				</div>
				<div class="space-y-2.5">
					<div
						v-for="(value, key) in stats.score_breakdown"
						:key="key"
						class="flex items-center gap-3"
					>
						<div class="flex items-center gap-2 w-28 flex-shrink-0">
							<component :is="getBreakdownIcon(key)" class="h-3.5 w-3.5 stroke-1.5 text-ink-gray-5" />
							<span class="text-sm text-ink-gray-7">{{ getBreakdownLabel(key) }}</span>
						</div>
						<div class="flex-1 h-1.5 bg-surface-gray-3 rounded-full overflow-hidden">
							<div
								class="h-full rounded-full transition-all duration-500"
								:class="getBreakdownColor(key)"
								:style="{ width: getBreakdownWidth(value) + '%' }"
							></div>
						</div>
						<span class="text-sm text-ink-gray-9 font-medium w-8 text-right flex-shrink-0">{{ formatNumber(value) }}</span>
					</div>
				</div>
			</div>

			<!-- Stats Grid -->
			<div class="grid grid-cols-2 gap-3">
				<div class="bg-surface-gray-1 rounded-lg p-3">
					<div class="flex items-center gap-1.5 mb-1">
						<BookOpen class="h-3.5 w-3.5 stroke-1.5 text-blue-500" />
						<span class="text-xs text-ink-gray-5">{{ __('Learning') }}</span>
					</div>
					<div class="text-lg font-semibold text-ink-gray-9">
						{{ stats.stats?.courses_completed || 0 }}
					</div>
					<div class="text-xs text-ink-gray-5">{{ __('courses') }}</div>
				</div>

				<div class="bg-surface-gray-1 rounded-lg p-3">
					<div class="flex items-center gap-1.5 mb-1">
						<CheckCircle class="h-3.5 w-3.5 stroke-1.5 text-emerald-500" />
						<span class="text-xs text-ink-gray-5">{{ __('Quizzes') }}</span>
					</div>
					<div class="text-lg font-semibold text-ink-gray-9">
						{{ stats.stats?.quizzes_completed || 0 }}
					</div>
					<div class="text-xs text-ink-gray-5">{{ __('completed') }}</div>
				</div>

				<div class="bg-surface-gray-1 rounded-lg p-3">
					<div class="flex items-center gap-1.5 mb-1">
						<Award class="h-3.5 w-3.5 stroke-1.5 text-amber-500" />
						<span class="text-xs text-ink-gray-5">{{ __('Certificates') }}</span>
					</div>
					<div class="text-lg font-semibold text-ink-gray-9">
						{{ stats.stats?.certificates || 0 }}
					</div>
					<div class="text-xs text-ink-gray-5">{{ __('earned') }}</div>
				</div>

				<div class="bg-surface-gray-1 rounded-lg p-3">
					<div class="flex items-center gap-1.5 mb-1">
						<Users class="h-3.5 w-3.5 stroke-1.5 text-violet-500" />
						<span class="text-xs text-ink-gray-5">{{ __('Referrals') }}</span>
					</div>
					<div class="text-lg font-semibold text-ink-gray-9">
						{{ stats.stats?.referrals || 0 }}
					</div>
					<div class="text-xs text-ink-gray-5">{{ __('total') }}</div>
				</div>
			</div>
		</div>

		<!-- Empty State -->
		<div v-else class="flex-1 flex items-center justify-center p-6 text-center text-sm text-ink-gray-5">
			{{ __('Select a user to view their statistics') }}
		</div>
	</div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { Button } from 'frappe-ui'
import { User, Trophy, BookOpen, CheckCircle, Award, Users, Heart, Video } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const props = defineProps({
	stats: {
		type: Object,
		default: null
	},
	loading: {
		type: Boolean,
		default: false
	},
	isOwnStats: {
		type: Boolean,
		default: true
	}
})

const emit = defineEmits(['show-my-stats'])

const router = useRouter()
const $user = inject('$user')

const isGuest = computed(() => !$user?.data)

const goToLogin = () => {
	router.push({ name: 'Login' })
}

const formatNumber = (num) => {
	if (!num) return '0'
	return num.toLocaleString()
}

const getInitials = (name) => {
	if (!name) return '?'
	return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
}

// Target for full progress bar: 100,000 points
const FULL_BAR_TARGET = 100000

const getBreakdownWidth = (value) => {
	// Calculate width based on 100,000 point target for full bar
	const percentage = (value / FULL_BAR_TARGET) * 100
	// Cap at 100% max
	return Math.min(percentage, 100)
}

const getBreakdownColor = (key) => {
	const colors = {
		learning: 'bg-blue-400',
		quizzes: 'bg-emerald-400',
		live_class: 'bg-purple-400',
		certificates: 'bg-amber-400',
		referrals: 'bg-violet-400',
		engagement: 'bg-rose-400'
	}
	return colors[key] || 'bg-gray-400'
}

const getBreakdownIcon = (key) => {
	const icons = {
		learning: BookOpen,
		quizzes: CheckCircle,
		live_class: Video,
		certificates: Award,
		referrals: Users,
		engagement: Heart
	}
	return icons[key] || BookOpen
}

const getBreakdownLabel = (key) => {
	const labels = {
		learning: 'Learning',
		quizzes: 'Quizzes',
		live_class: 'Live Class',
		certificates: 'Certificates',
		referrals: 'Referrals',
		engagement: 'Engagement'
	}
	return labels[key] || key
}
</script>
