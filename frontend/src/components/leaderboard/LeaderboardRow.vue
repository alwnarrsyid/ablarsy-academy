<template>
	<div
		class="flex items-center justify-between px-4 py-2.5 border-b border-outline-gray-1 hover:bg-surface-gray-1 transition-colors cursor-pointer"
		:class="{
			'bg-surface-gray-1': isCurrentUser && !isTopRank,
			'bg-amber-50/50': isTopRank
		}"
		:data-user-rank="user.rank"
		@click="$emit('view', user)"
	>
		<!-- Rank & Avatar -->
		<div class="flex items-center gap-3 flex-1 min-w-0">
			<!-- Rank Number/Icon -->
			<div class="flex-shrink-0 w-6 text-center">
				<Crown v-if="user.rank === 1" class="h-4 w-4 stroke-1.5 text-amber-500 mx-auto" />
				<span v-else class="text-sm font-medium text-ink-gray-5">{{ user.rank }}</span>
			</div>

			<!-- Avatar -->
			<img
				v-if="user.user_image"
				:src="user.user_image"
				:alt="user.full_name"
				class="h-7 w-7 rounded-full object-cover flex-shrink-0"
			/>
			<div
				v-else
				class="h-7 w-7 rounded-full bg-surface-gray-3 flex items-center justify-center flex-shrink-0"
			>
				<span class="text-xs font-medium text-ink-gray-5">{{ getInitials(user.full_name) }}</span>
			</div>

			<!-- Name -->
			<div class="min-w-0 flex-1">
				<div class="flex items-center gap-2">
					<span class="text-sm text-ink-gray-9 truncate">
						{{ user.full_name }}
					</span>
					<span
						v-if="isCurrentUser"
						class="text-xs text-blue-600"
					>
						{{ __('You') }}
					</span>
				</div>
			</div>
		</div>

		<!-- Score -->
		<div class="flex items-center gap-3">
			<div class="text-right">
				<span class="text-sm font-medium text-ink-gray-9">
					{{ formatNumber(user.score) }}
				</span>
				<span class="text-xs text-ink-gray-5 ml-1">{{ __('pts') }}</span>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { Crown } from 'lucide-vue-next'

const props = defineProps({
	user: {
		type: Object,
		required: true
	},
	isCurrentUser: {
		type: Boolean,
		default: false
	},
	isTopRank: {
		type: Boolean,
		default: false
	},
	isSticky: {
		type: Boolean,
		default: false
	}
})

const emit = defineEmits(['view'])

const formatNumber = (num) => {
	if (!num) return '0'
	return num.toLocaleString()
}

const getInitials = (name) => {
	if (!name) return '?'
	return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
}
</script>
