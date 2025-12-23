<template>
	<div>
		<header
			class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs" />
		</header>
		<div class="p-4 md:p-5 pb-10">
			<div class="mb-5">
				<div class="text-lg text-ink-gray-9 font-semibold mb-4">
					{{ __('Search') }}
				</div>

				<!-- Search Input -->
				<div class="flex flex-col sm:flex-row gap-3 mb-6">
					<FormControl
						v-model="searchQuery"
						:placeholder="__('Search courses, batches...')"
						type="text"
						class="w-full sm:w-96"
						@input="debouncedSearch"
					>
						<template #prefix>
							<SearchIcon class="w-4 h-4 stroke-1.5 text-ink-gray-5" />
						</template>
					</FormControl>
				</div>
			</div>

			<!-- Loading State -->
			<div v-if="isLoading" class="flex justify-center py-10">
				<LoadingIndicator class="w-8 h-8" />
			</div>

			<!-- Results -->
			<div v-else-if="searchQuery.length >= 2">
				<!-- Courses Section -->
				<div v-if="courses.length" class="mb-8">
					<div class="text-md font-semibold text-ink-gray-7 mb-3">
						{{ __('Courses') }} ({{ courses.length }})
					</div>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
						<router-link
							v-for="course in courses"
							:key="course.name"
							:to="{ name: 'CourseDetail', params: { courseName: course.name } }"
						>
							<CourseCard :course="course" />
						</router-link>
					</div>
				</div>

				<!-- Batches Section -->
				<div v-if="batches.length" class="mb-8">
					<div class="text-md font-semibold text-ink-gray-7 mb-3">
						{{ __('Batches') }} ({{ batches.length }})
					</div>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
						<router-link
							v-for="batch in batches"
							:key="batch.name"
							:to="{ name: 'BatchDetail', params: { batchName: batch.name } }"
						>
							<BatchCard :batch="batch" />
						</router-link>
					</div>
				</div>

				<!-- No Results -->
				<div v-if="!courses.length && !batches.length && !isLoading" class="text-center py-10">
					<SearchIcon class="w-12 h-12 text-ink-gray-4 mx-auto mb-3" />
					<p class="text-ink-gray-5">{{ __('No results found for') }} "{{ searchQuery }}"</p>
				</div>
			</div>

			<!-- Initial State -->
			<div v-else class="text-center py-10">
				<SearchIcon class="w-12 h-12 text-ink-gray-4 mx-auto mb-3" />
				<p class="text-ink-gray-5">{{ __('Type at least 2 characters to search') }}</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Breadcrumbs, FormControl, LoadingIndicator, call, usePageMeta } from 'frappe-ui'
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search as SearchIcon } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import CourseCard from '@/components/CourseCard.vue'
import BatchCard from '@/components/BatchCard.vue'
import { useDebounceFn } from '@vueuse/core'

const route = useRoute()
const router = useRouter()
const { brand } = sessionStore()

const searchQuery = ref('')
const courses = ref([])
const batches = ref([])
const isLoading = ref(false)

onMounted(() => {
	// Get search query from URL if present
	const queryParam = route.query.q
	if (queryParam) {
		searchQuery.value = queryParam
		performSearch()
	}
})

const performSearch = async () => {
	if (searchQuery.value.length < 2) {
		courses.value = []
		batches.value = []
		return
	}

	isLoading.value = true

	try {
		const result = await call('lms.lms.api.global_search', {
			query: searchQuery.value
		})
		courses.value = result.courses || []
		batches.value = result.batches || []

		// Update URL
		router.replace({ query: { q: searchQuery.value } })
	} catch (error) {
		console.error('Search error:', error)
		courses.value = []
		batches.value = []
	} finally {
		isLoading.value = false
	}
}

const debouncedSearch = useDebounceFn(performSearch, 300)

const breadcrumbs = computed(() => [
	{
		label: __('Search'),
		route: { name: 'Search' },
	},
])

usePageMeta(() => {
	return {
		title: __('Search'),
		icon: brand.favicon,
	}
})
</script>
