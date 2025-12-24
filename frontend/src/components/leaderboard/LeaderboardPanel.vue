<template>
	<div class="flex flex-col h-full">
		<!-- Sticky #1 Row -->
		<div
			v-if="topUser"
			class="sticky top-0 z-20 bg-surface-white border-b border-outline-gray-2"
		>
			<LeaderboardRow
				:user="topUser"
				:isCurrentUser="topUser.user === currentUser"
				:isTopRank="true"
				@view="$emit('view', topUser)"
			/>
		</div>

		<!-- Scrollable Table -->
		<div
			ref="scrollContainer"
			class="flex-1 overflow-y-auto min-h-0"
			@scroll="handleScroll"
		>
			<div v-for="user in middleUsers" :key="user.user">
				<LeaderboardRow
					:user="user"
					:isCurrentUser="user.user === currentUser"
					@view="$emit('view', user)"
				/>
			</div>

			<!-- Spacer to push content if list is short -->
			<div class="flex-1"></div>
		</div>

		<!-- Sticky Current User Row (if not in view and not already displayed) -->
		<div
			v-if="showStickyCurrentUser"
			class="sticky bottom-0 z-10 bg-surface-gray-2 border-t border-outline-gray-2"
		>
			<LeaderboardRow
				:user="currentUserData"
				:isCurrentUser="true"
				:isSticky="true"
				@view="$emit('view', currentUserData)"
			/>
		</div>

		<!-- Pagination -->
		<div
			v-if="totalPages > 1"
			class="flex items-center justify-center gap-2 py-3 border-t border-outline-gray-2 bg-surface-white"
		>
			<Button
				variant="ghost"
				:disabled="page <= 1"
				@click="$emit('page-change', page - 1)"
			>
				<template #icon>
					<ChevronLeft class="h-4 w-4 stroke-1.5" />
				</template>
			</Button>
			<span class="text-sm text-ink-gray-7">
				{{ __('Page') }} {{ page }} {{ __('of') }} {{ totalPages }}
			</span>
			<Button
				variant="ghost"
				:disabled="page >= totalPages"
				@click="$emit('page-change', page + 1)"
			>
				<template #icon>
					<ChevronRight class="h-4 w-4 stroke-1.5" />
				</template>
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Button } from 'frappe-ui'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import LeaderboardRow from './LeaderboardRow.vue'

const props = defineProps({
	data: {
		type: Array,
		default: () => []
	},
	currentUser: {
		type: String,
		default: ''
	},
	currentUserData: {
		type: Object,
		default: null
	},
	page: {
		type: Number,
		default: 1
	},
	totalPages: {
		type: Number,
		default: 1
	}
})

const emit = defineEmits(['view', 'page-change'])

const scrollContainer = ref(null)
const isCurrentUserInView = ref(true) // default true to hide sticky initially

// Top user is always rank #1 (first in data on first page)
const topUser = computed(() => {
	if (props.page === 1 && props.data.length > 0) {
		return props.data[0]
	}
	return null
})

// Middle users are all except #1 (for first page) or all (for other pages)
const middleUsers = computed(() => {
	if (props.page === 1 && props.data.length > 1) {
		return props.data.slice(1)
	}
	return props.data
})

// Check if current user is already in the visible list
const isCurrentUserInList = computed(() => {
	if (!props.currentUserData) return false
	return props.data.some(u => u.user === props.currentUserData.user)
})

// Show sticky current user only if:
// 1. We have current user data
// 2. Current user is NOT in the current page's list
const showStickyCurrentUser = computed(() => {
	return props.currentUserData && !isCurrentUserInList.value
})

const handleScroll = () => {
	// Simplified - just track if user scrolled
	if (!scrollContainer.value) return
}

watch(() => props.data, () => {
	isCurrentUserInView.value = true
})
</script>
