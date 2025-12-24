<template>
	<router-link
		v-if="rank"
		:to="{ name: 'Leaderboard' }"
		class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-blue-50 hover:bg-blue-100 transition-colors cursor-pointer"
	>
		<Trophy class="h-3.5 w-3.5 stroke-1.5 text-blue-600" />
		<span class="text-xs font-medium text-blue-700">
			{{ __('Rank #{0}').replace('{0}', rank) }}
		</span>
		<span
			v-if="change !== 0"
			class="text-xs"
			:class="change > 0 ? 'text-emerald-600' : 'text-red-500'"
		>
			{{ change > 0 ? '↑' : '↓' }}{{ Math.abs(change) }}
		</span>
	</router-link>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { createResource } from 'frappe-ui'
import { Trophy } from 'lucide-vue-next'

const props = defineProps({
	user: {
		type: String,
		default: ''
	}
})

const $user = inject('$user')
const rank = ref(null)
const change = ref(0)

const userStats = createResource({
	url: 'lms.lms.api.get_user_stats',
	makeParams() {
		return {
			user: props.user || $user?.data?.name
		}
	}
})

onMounted(() => {
	if (props.user || $user?.data?.name) {
		userStats.fetch().then(() => {
			if (userStats.data) {
				rank.value = userStats.data.user_info?.rank
			}
		})
	}
})
</script>
